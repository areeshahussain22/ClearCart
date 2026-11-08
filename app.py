"""ClearCart - Day 2: store, link PayPal once, pay with the saved account, receipt from PayPal."""

import logging
import os
import secrets
from contextlib import asynccontextmanager
from decimal import Decimal, InvalidOperation

from fastapi import FastAPI, Form, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import catalog
import pages
import paypal_api
from paypal_mcp import mcp_client

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("clearcart")


@asynccontextmanager
async def lifespan(app):
    # Start PayPal's MCP server in the background now, so the first receipt isn't slow.
    if os.environ.get("PAYPAL_CLIENT_ID") and os.environ.get("PAYPAL_CLIENT_SECRET"):
        mcp_client.start()
    yield
    await mcp_client.stop()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET") or secrets.token_hex(32),
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


def linked_account(request):
    acc = request.session.get("paypal")
    return acc if acc and acc.get("payment_token_id") else None


def pop_notice(request):
    return request.session.pop("notice", None)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return pages.home(linked_account(request), pop_notice(request))


@app.get("/health")
def health():
    return {"ok": True, "mcp_ready": mcp_client.ready, "mcp_error": mcp_client.last_error}


# ---- Link PayPal once -------------------------------------------------------

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
        acc = await run_in_threadpool(paypal_api.create_payment_token, setup_id)
    except Exception as e:
        log.exception("save account failed")
        return HTMLResponse(pages.error("Could not link PayPal",
                                        "PayPal did not save the account. Please try again.", str(e)), 502)
    request.session["paypal"] = acc
    request.session["notice"] = "PayPal linked: %s. You can now pay without opening PayPal." % (acc.get("email") or "")
    return RedirectResponse("/", status_code=303)


@app.get("/paypal/cancel")
def paypal_cancel(request: Request):
    request.session.pop("setup_token_id", None)
    request.session["notice"] = "PayPal linking was cancelled. Nothing was saved."
    return RedirectResponse("/", status_code=303)


@app.post("/unlink")
def unlink(request: Request):
    request.session.pop("paypal", None)
    request.session["notice"] = "PayPal unlinked from this browser."
    return RedirectResponse("/", status_code=303)


# ---- Buy ----------------------------------------------------------------------

@app.get("/confirm/{product_id}", response_class=HTMLResponse)
def confirm(request: Request, product_id: str):
    product = catalog.get(product_id)
    if not product:
        return HTMLResponse(pages.error("Product not found", "That product does not exist."), 404)
    return pages.confirm(product, linked_account(request), pop_notice(request))


@app.post("/pay")
async def pay(request: Request, product_id: str = Form(...), expected_total: str = Form(...)):
    acc = linked_account(request)
    if not acc:
        request.session["notice"] = "Please link PayPal before paying."
        return RedirectResponse("/", status_code=303)
    product = catalog.get(product_id)
    if not product:
        return HTMLResponse(pages.error("Product not found", "That product does not exist."), 404)

    # Price recheck: the price shown to the shopper must still match the catalog.
    price = catalog.price_of(product_id)
    try:
        shown = Decimal(expected_total)
    except InvalidOperation:
        shown = None
    if shown != price:
        request.session["notice"] = ("The price of %s changed to %s. Nothing was charged. Please check again."
                                     % (product["name"], catalog.money(price)))
        return RedirectResponse("/confirm/" + product_id, status_code=303)

    try:
        order = await run_in_threadpool(
            paypal_api.pay_with_saved_account, acc["payment_token_id"], product, price, 1, catalog.CURRENCY)
    except Exception as e:
        log.exception("payment failed")
        return HTMLResponse(pages.error("Payment did not go through",
                                        "PayPal did not complete the payment. Nothing was charged.", str(e)), 502)
    orders = request.session.get("orders", [])
    orders.append(order["id"])
    request.session["orders"] = orders[-20:]
    return RedirectResponse("/receipt/" + order["id"], status_code=303)


# ---- Receipt, read back from PayPal ------------------------------------------

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
    if order_id not in request.session.get("orders", []):
        return HTMLResponse(pages.error("Order not found", "This order isn't in your recent orders."), 404)
    try:
        order, source = await fetch_order(order_id)
    except Exception as e:
        log.exception("receipt failed")
        return HTMLResponse(pages.error("Could not check the payment",
                                        "PayPal could not be reached. Please try again in a moment.", str(e)), 502)
    return pages.receipt(summarize(order), source)
