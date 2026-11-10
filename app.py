"""ClearCart: accessible voice and keyboard shopping assistant for PayPal stores."""

import logging
import os
import time
from contextlib import asynccontextmanager
from decimal import Decimal, InvalidOperation

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, Form, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

import account
import actions
import agent
import catalog
import pages
import paypal_api
import search
from paypal_mcp import mcp_client

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("clearcart")


@asynccontextmanager
async def lifespan(app):
    # Start PayPal's MCP server in the background now, so the first PayPal check isn't slow.
    if os.environ.get("PAYPAL_CLIENT_ID") and os.environ.get("PAYPAL_CLIENT_SECRET"):
        mcp_client.start()
    # Load saved product embeddings; embed any missing/changed products in the background.
    search.start_background_refresh()
    yield
    await mcp_client.stop()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=account.SESSION_SECRET,
    same_site="lax",
    https_only=os.environ.get("HTTPS_ONLY", "").lower() in ("1", "true", "yes"),
    max_age=60 * 60 * 8,
)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")


def base_url(request):
    configured = os.environ.get("PUBLIC_BASE_URL")
    if configured:
        return configured.rstrip("/")
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", request.url.netloc))
    return "%s://%s" % (proto, host)


def pop_notice(request):
    return request.session.pop("notice", None)


# ---- Pages ----------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    acct = account.load(request)
    if not acct.get("paypal"):
        return pages.welcome(pop_notice(request))
    if not account.is_set_up(acct):
        return RedirectResponse("/setup", status_code=303)
    return pages.assistant(acct, pop_notice(request), account.is_idle_locked(acct))


@app.get("/store", response_class=HTMLResponse)
def store(request: Request):
    acct = account.load(request)
    return pages.store(acct if acct.get("paypal") else None, pop_notice(request))


@app.get("/health")
def health():
    return {"ok": True, "mcp_ready": mcp_client.ready, "mcp_error": mcp_client.last_error,
            "search": {k: search.status[k] for k in ("model", "products_embedded", "products_total", "last_method", "last_error")},
            "ai": [k for k in ("GEMINI_API_KEY", "GROQ_API_KEY") if os.environ.get(k)]}


# ---- Link PayPal once -----------------------------------------------------------

@app.get("/link")
async def link(request: Request):
    base = base_url(request)
    try:
        setup_id, approve = await run_in_threadpool(
            paypal_api.create_setup_token, base + "/paypal/return", base + "/paypal/cancel")
    except Exception as e:
        log.exception("link failed")
        return HTMLResponse(pages.error("Could not start PayPal linking",
                                        "PayPal did not accept the request. Please try again.", str(e)), 502)
    request.session["setup_token_id"] = setup_id
    return RedirectResponse(approve, status_code=303)


@app.get("/paypal/return")
async def paypal_return(request: Request):
    setup_id = request.session.pop("setup_token_id", None)
    if not setup_id:
        request.session["notice"] = "Linking expired. Please try linking PayPal again."
        return RedirectResponse("/", status_code=303)
    try:
        linked = await run_in_threadpool(paypal_api.create_payment_token, setup_id)
    except Exception as e:
        log.exception("save account failed")
        return HTMLResponse(pages.error("Could not link PayPal",
                                        "PayPal did not save the account. Please try again.", str(e)), 502)
    acct = account.load(request)
    acct["paypal"] = linked
    account.save(request, acct)
    request.session["notice"] = "PayPal linked: %s." % (linked.get("email") or "")
    return RedirectResponse("/setup" if not account.is_set_up(acct) else "/", status_code=303)


@app.get("/paypal/cancel")
def paypal_cancel(request: Request):
    request.session.pop("setup_token_id", None)
    request.session["notice"] = "PayPal linking was cancelled. Nothing was saved."
    return RedirectResponse("/", status_code=303)


@app.post("/unlink")
def unlink(request: Request):
    request.session.pop("acct", None)
    request.session["notice"] = "PayPal unlinked and your ClearCart settings were removed from this browser."
    return RedirectResponse("/", status_code=303)


# ---- One-time setup: PIN and spending limit ---------------------------------------

@app.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request):
    acct = account.load(request)
    if not acct.get("paypal"):
        return RedirectResponse("/", status_code=303)
    return pages.setup(acct, pop_notice(request))


@app.post("/setup")
def setup_save(request: Request, pin: str = Form(""), pin2: str = Form(""), limit: str = Form("30")):
    acct = account.load(request)
    if not acct.get("paypal"):
        return RedirectResponse("/", status_code=303)
    if acct.get("pin_hash") and account.is_idle_locked(acct):
        request.session["notice"] = "Unlock ClearCart first."
        return RedirectResponse("/", status_code=303)
    if not account.valid_pin_format(pin):
        return HTMLResponse(pages.setup(acct, "Your PIN must be exactly 4 digits."), 400)
    if pin != pin2:
        return HTMLResponse(pages.setup(acct, "The two PINs don't match. Please type them again."), 400)
    try:
        lim = Decimal(limit).quantize(Decimal("0.01"))
    except InvalidOperation:
        lim = Decimal("0")
    if lim < 1 or lim > 500:
        return HTMLResponse(pages.setup(acct, "Choose a spending limit between 1 and 500 pounds."), 400)
    acct["pin_salt"], acct["pin_hash"] = account.hash_pin(pin)
    acct["limit"] = str(lim)
    acct["attempts"] = 0
    account.touch(acct)
    account.save(request, acct)
    request.session["notice"] = "All set. Your spending limit is %s per purchase." % catalog.money_words(lim)
    return RedirectResponse("/", status_code=303)


# ---- Assistant API (used by static/app.js) ----------------------------------------

def _state(acct):
    return {"pending": pages.pending_view(acct),
            "locked": account.is_idle_locked(acct),
            "lockout_seconds": account.locked_out_for(acct)}


def _not_ready(acct):
    if not account.is_set_up(acct):
        return JSONResponse({"error": "Please link PayPal and set your PIN first.", "redirect": "/"}, 400)
    return None


@app.post("/api/chat")
async def api_chat(request: Request):
    acct = account.load(request)
    bad = _not_ready(acct)
    if bad:
        return bad
    if account.is_idle_locked(acct):
        return JSONResponse({"reply": "ClearCart locked itself after a few minutes without use. "
                                      "Type your PIN in the unlock box to continue.", **_state(acct)})
    payload = await request.json()
    message = str(payload.get("message", "")).strip()[:1000]
    history = [{"role": h.get("role"), "text": str(h.get("text", ""))[:1000]}
               for h in (payload.get("history") or [])[-10:] if h.get("role") in ("user", "assistant")]
    if not message:
        return JSONResponse({"reply": "Please type or say what you'd like.", **_state(acct)})
    acct.pop("pending", None)  # a new request replaces anything waiting for a PIN
    t0 = time.time()
    try:
        reply, provider, tools_used, info = await agent.chat(message, history, acct)
    except Exception as e:
        log.exception("agent failed")
        account.touch(acct)
        account.save(request, acct)
        return JSONResponse({"reply": "Sorry, the assistant isn't available right now. You can still use the store page.",
                             "detail": str(e)[:300], **_state(acct)})
    account.touch(acct)
    account.save(request, acct)
    return JSONResponse({"reply": reply, "provider": provider, "tools": tools_used,
                         "seconds": round(time.time() - t0, 1), **info, **_state(acct)})


@app.post("/api/confirm")
async def api_confirm(request: Request):
    acct = account.load(request)
    bad = _not_ready(acct)
    if bad:
        return bad
    payload = await request.json()
    if not acct.get("pending"):
        return JSONResponse({"ok": False, "reply": "There's nothing waiting to be confirmed.", **_state(acct)})
    ok, msg = account.check_pin(acct, str(payload.get("pin", "")))
    if not ok:
        account.save(request, acct)
        return JSONResponse({"ok": False, "reply": msg, **_state(acct)})
    done, reply, extra = await actions.execute_pending(acct)
    account.touch(acct)
    account.save(request, acct)
    return JSONResponse({"ok": done, "reply": reply, **extra, **_state(acct)})


@app.post("/api/cancel")
def api_cancel(request: Request):
    acct = account.load(request)
    had = acct.pop("pending", None)
    account.touch(acct)
    account.save(request, acct)
    msg = "Cancelled. Nothing was charged." if had and had["type"] == "pay" else (
        "Cancelled. Nothing was refunded." if had else "There was nothing to cancel.")
    return JSONResponse({"ok": True, "reply": msg, **_state(acct)})


@app.post("/api/unlock")
async def api_unlock(request: Request):
    acct = account.load(request)
    bad = _not_ready(acct)
    if bad:
        return bad
    payload = await request.json()
    ok, msg = account.check_pin(acct, str(payload.get("pin", "")))
    account.save(request, acct)
    if ok:
        return JSONResponse({"ok": True, "reply": "Unlocked. What would you like to do?", **_state(acct)})
    return JSONResponse({"ok": False, "reply": msg, **_state(acct)})


# ---- Store page (keyboard-only path, also needs the PIN) --------------------------

@app.get("/confirm/{product_id}", response_class=HTMLResponse)
def confirm(request: Request, product_id: str):
    product = catalog.get(product_id)
    if not product:
        return HTMLResponse(pages.error("Product not found", "That product does not exist."), 404)
    acct = account.load(request)
    return pages.confirm(product, acct, pop_notice(request))


@app.post("/pay")
async def pay(request: Request, product_id: str = Form(...), expected_total: str = Form(...), pin: str = Form("")):
    acct = account.load(request)
    if not account.is_set_up(acct):
        request.session["notice"] = "Please link PayPal and set your PIN before paying."
        return RedirectResponse("/", status_code=303)
    product = catalog.get(product_id)
    if not product:
        return HTMLResponse(pages.error("Product not found", "That product does not exist."), 404)
    price = catalog.price_of(product_id)
    try:
        shown = Decimal(expected_total)
    except InvalidOperation:
        shown = None
    if shown != price:
        request.session["notice"] = ("The price of %s changed to %s. Nothing was charged. Please check again."
                                     % (product["name"], catalog.money(price)))
        return RedirectResponse("/confirm/" + product_id, status_code=303)
    prep = actions.prepare_purchase(acct, product_id, 1)
    if prep.get("error"):
        account.save(request, acct)
        request.session["notice"] = prep["error"]
        return RedirectResponse("/confirm/" + product_id, status_code=303)
    ok, msg = account.check_pin(acct, pin)
    if not ok:
        acct.pop("pending", None)
        account.save(request, acct)
        request.session["notice"] = msg
        return RedirectResponse("/confirm/" + product_id, status_code=303)
    done, reply, extra = await actions.execute_pending(acct)
    account.save(request, acct)
    if not extra.get("order_id"):
        return HTMLResponse(pages.error("Payment did not go through", reply, extra.get("detail")), 502)
    return RedirectResponse("/receipt/" + extra["order_id"], status_code=303)


# ---- Receipt, read back from PayPal --------------------------------------------

def summarize(order):
    pu = (order.get("purchase_units") or [{}])[0]
    amount = pu.get("amount") or {}
    caps = ((pu.get("payments") or {}).get("captures") or [{}])
    cap = caps[0] if caps else {}
    items = ", ".join("%s x%s" % (i.get("name"), i.get("quantity")) for i in pu.get("items", [])) or pu.get("description", "")
    value = amount.get("value") or (cap.get("amount") or {}).get("value") or "0"
    return {
        "order_id": order.get("id"),
        "status": order.get("status", "UNKNOWN"),
        "items": items,
        "total": catalog.money(value),
        "total_words": catalog.money_words(value),
        "capture_status": cap.get("status", "unknown"),
        "capture_id": cap.get("id", "not available"),
    }


async def fetch_order(order_id):
    """Ask PayPal for the order: first with PayPal's MCP agent tool, then the REST API as a backup."""
    try:
        order = await mcp_client.call("get_order", {"id": order_id})
        if isinstance(order, dict) and order.get("id"):
            return order, "PayPal's agent tools (get_order)"
        log.warning("Unexpected get_order result: %r", str(order)[:200])
    except Exception as e:
        log.warning("MCP get_order failed, using REST: %r", e)
    order = await run_in_threadpool(paypal_api.get_order, order_id)
    return order, "PayPal's API (backup)"


@app.get("/receipt/{order_id}", response_class=HTMLResponse)
async def receipt(request: Request, order_id: str):
    acct = account.load(request)
    if not account.find_order(acct, order_id) or account.find_order(acct, order_id)["id"] != order_id:
        return HTMLResponse(pages.error("Order not found", "This order isn't in your recent orders."), 404)
    try:
        order, source = await fetch_order(order_id)
    except Exception as e:
        log.exception("receipt failed")
        return HTMLResponse(pages.error("Could not check the payment",
                                        "PayPal could not be reached. Please try again in a moment.", str(e)), 502)
    return pages.receipt(summarize(order), source)
