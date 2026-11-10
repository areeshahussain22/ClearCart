"""HTML pages. Plain, semantic HTML so screen readers and keyboards work well."""

import json
from decimal import Decimal
from html import escape

import account
import catalog

_MASCOT = """<svg class="%s" viewBox="0 0 120 110" aria-hidden="true" focusable="false">
<path class="m-handle" d="M30 48 C30 14, 90 14, 90 48" fill="none" stroke-width="7" stroke-linecap="round"/>
<path class="m-body" d="M12 46 H108 a6 6 0 0 1 6 7 L104 96 a10 10 0 0 1 -10 8 H26 a10 10 0 0 1 -10 -8 L6 53 a6 6 0 0 1 6 -7 Z" stroke-width="5" stroke-linejoin="round"/>
<path class="m-weave" d="M14 62 H106" fill="none" stroke-width="3" stroke-linecap="round" opacity=".35"/>
<g class="m-eyes-open"><ellipse cx="43" cy="72" rx="6" ry="7.5"/><ellipse cx="77" cy="72" rx="6" ry="7.5"/>
<circle class="m-shine" cx="45" cy="69" r="2"/><circle class="m-shine" cx="79" cy="69" r="2"/></g>
<g class="m-eyes-happy" fill="none" stroke-width="4.5" stroke-linecap="round"><path d="M36 74 q7 -9 14 0"/><path d="M70 74 q7 -9 14 0"/></g>
<g class="m-eyes-sleepy" fill="none" stroke-width="4.5" stroke-linecap="round"><path d="M36 72 q7 6 14 0"/><path d="M70 72 q7 6 14 0"/></g>
<ellipse class="m-blush" cx="31" cy="83" rx="7" ry="4.5"/><ellipse class="m-blush" cx="89" cy="83" rx="7" ry="4.5"/>
<path class="m-smile" d="M51 84 q9 9 18 0" fill="none" stroke-width="4.5" stroke-linecap="round"/>
<ellipse class="m-o" cx="60" cy="88" rx="5" ry="6"/>
<path class="m-wobble" d="M50 89 q5 -5 10 0 q5 5 10 0" fill="none" stroke-width="4" stroke-linecap="round"/>
<g class="m-dots"><circle cx="98" cy="22" r="4"/><circle cx="108" cy="12" r="5"/><circle cx="114" cy="0" r="0"/></g>
</svg>"""


def mascot(cls="mascot"):
    """Basket, ClearCart's helper. Decorative: everything it shows is also said in text."""
    return _MASCOT % cls


def pin_field(input_id, label, name=None, autocomplete="off", on_plate=False):
    """A real password input, drawn as four round bubbles that fill as you type."""
    name_attr = ' name="%s"' % name if name else ""
    cells = '<span class="pin-cell"></span>' * 4
    return """<div class="pin%s">
<label for="%s">%s</label>
<div class="pin-field" data-count="0">
<input id="%s"%s type="password" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" autocomplete="%s" required>
<span class="pin-cells" aria-hidden="true">%s</span>
</div>
</div>""" % (" on-plate" if on_plate else "", input_id, label, input_id, name_attr, autocomplete, cells)


def steps(current):
    """The three setup steps as round stickers."""
    names = ["Link PayPal", "Choose a PIN and limit", "Ask for what you need"]
    items = []
    for i, text in enumerate(names, start=1):
        state = "done" if i < current else ("current" if i == current else "todo")
        sr = {"done": "Done: ", "current": "Now: ", "todo": ""}[state]
        aria = ' aria-current="step"' if i == current else ""
        items.append('<li class="%s"%s><span class="badge" aria-hidden="true">%d</span>'
                     '<span><span class="sr-only">%s</span>%s</span></li>' % (state, aria, i, sr, text))
    return '<ol class="steps" aria-label="Setup steps">%s</ol>' % "".join(items)


def pending_view(acct):
    """What the screen shows for a payment or refund waiting for a PIN: type, read-back, amount."""
    pending = acct.get("pending")
    if not pending:
        return None
    view = {"type": pending["type"], "readback": pending["readback"]}
    try:
        if pending["type"] == "pay":
            amount = Decimal(pending["price"]) * int(pending["quantity"])
            limit = Decimal(acct.get("limit", "30"))
            view["limit"] = catalog.money(limit)
            view["share"] = max(0, min(100, int(amount / limit * 100)))
        else:
            order = account.find_order(acct, pending.get("order_id"))
            amount = Decimal(order["total"]) if order else None
        if amount is not None:
            view["amount"] = catalog.money(amount)
    except Exception:
        pass
    return view


def layout(title, body, notice=None, scripts="", current=None, wide=False):
    live = ('<div id="notice" class="notice" role="status" aria-live="polite">%s</div>'
            % escape(notice)) if notice else '<div id="notice" role="status" aria-live="polite"></div>'
    nav = []
    for href, text, key in (("/", "Assistant", "assistant"), ("/store", "Store", "store")):
        cur = ' aria-current="page"' if key == current else ""
        nav.append('<a href="%s"%s>%s</a>' % (href, cur, text))
    return """<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>%s · ClearCart</title>
<link rel="preload" href="/static/fonts/atkinson-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/static/fonts/atkinson-700.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/static/fonts/fredoka-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/static/style.css">
<script>document.documentElement.classList.add("js");</script>
</head>
<body>
<a class="skip" href="#main">Skip to main content</a>
<header class="site">
<div class="bar">
<a class="brand" href="/">%s<span>ClearCart</span></a>
<p class="sandbox">Demo store · PayPal sandbox · no real money</p>
<nav aria-label="Main">%s</nav>
</div>
</header>
<main id="main" tabindex="-1" class="%s">
%s
%s
</main>
<script src="/static/pin.js" defer></script>
%s
</body>
</html>""" % (escape(title), mascot("mascot brand-mark"), "".join(nav),
              "wide" if wide else "", live, body, scripts)


def welcome(notice=None):
    body = """<div class="intro">
<section class="lead-col" aria-labelledby="welcome-h">
%s
<h1 id="welcome-h">Shop by voice or keyboard, pay with PayPal</h1>
<p class="lead">ClearCart helps you find products, pay, check and track orders, and ask for refunds, by talking or typing.</p>
<h2 class="tag">Get started</h2>
%s
<p class="example">Then just ask, for example: "I need a notebook under 5 pounds."</p>
<p class="actions"><a class="button" href="/link">Link PayPal</a> <a class="quiet-link" href="/store">Or browse the store first</a></p>
</section>
<section class="facts" aria-labelledby="safe-h">
<h2 id="safe-h">How your money stays safe</h2>
<ul>
<li><strong>Your PIN is typed, never spoken.</strong> Nobody can copy it from your voice, and voice can never confirm a payment.</li>
<li><strong>The assistant only prepares.</strong> Code checks your PIN, your spending limit and the price before any money moves.</li>
<li><strong>You hear it before you pay.</strong> Every payment is read back from the store's own prices. Nothing is charged until you type your PIN.</li>
</ul>
</section>
</div>""" % (mascot("mascot hero-mascot"), steps(1))
    return layout("Welcome", body, notice, current="assistant", wide=True)


def store(linked_acct, notice=None):
    groups = {}
    for p in catalog.PRODUCTS:
        groups.setdefault(p["category"], []).append(p)
    sections = []
    for cat, products in groups.items():
        slug = cat.lower().replace(" ", "-")
        items = []
        for p in products:
            items.append("""<li class="product">
<div class="product-text">
<h3 id="h-%(id)s">%(name)s</h3>
<p>%(desc)s <span class="rating">Rated %(rating)s out of 5.</span></p>
</div>
<p class="price">%(price)s <span class="sr-only">(%(words)s)</span></p>
<p class="buy"><a class="button small" href="/confirm/%(id)s" aria-describedby="h-%(id)s">Buy</a></p>
</li>""" % {"id": p["id"], "name": escape(p["name"]), "price": catalog.money(p["price"]),
                "words": catalog.money_words(p["price"]), "rating": p["rating"],
                "desc": escape(p["description"])})
        sections.append('<section class="aisle" aria-labelledby="cat-%s"><h2 id="cat-%s" class="tag">%s</h2>'
                        '<ul class="products">%s</ul></section>' % (slug, slug, escape(cat), "\n".join(items)))
    if linked_acct:
        status = '<p class="chips"><span class="chip">PayPal linked: <strong>%s</strong></span></p>' % escape(
            linked_acct["paypal"].get("email") or "")
    else:
        status = '<p class="chips"><span class="chip">PayPal is not linked yet.</span> <a href="/link">Link PayPal</a> to buy.</p>'
    body = """<h1>Store</h1>
%s
%s""" % (status, "\n".join(sections))
    return layout("Store", body, notice, current="store")


def setup(acct, notice=None):
    body = """<div class="intro">
<section class="lead-col" aria-labelledby="setup-h">
<h1 id="setup-h">Set your PIN and spending limit</h1>
%s
<p class="chips"><span class="chip">PayPal linked: <strong>%s</strong></span></p>
<p>Your PIN is typed, never spoken, so nobody can copy it from your voice. You'll type it for every payment and refund.</p>
<form method="post" action="/setup" class="stack">
%s
%s
<div class="field">
<label for="limit">Spending limit per purchase, in pounds</label>
<input id="limit" name="limit" type="number" min="1" max="500" step="1" value="%s" required>
</div>
<p><button type="submit">Save</button></p>
</form>
</section>
<section class="facts" aria-labelledby="unlink-h">
<h2 id="unlink-h">Linked account</h2>
<p>To stop using this PayPal account with ClearCart, unlink it. You can link it again later.</p>
<form method="post" action="/unlink"><button type="submit" class="danger">Unlink PayPal</button></form>
</section>
</div>""" % (
        steps(2),
        escape(acct["paypal"].get("email") or "PayPal"),
        pin_field("pin", "Choose a 4-digit PIN", name="pin", autocomplete="new-password"),
        pin_field("pin2", "Type the PIN again", name="pin2", autocomplete="new-password"),
        escape(str(int(float(acct.get("limit", 30))))))
    return layout("Set up", body, notice, wide=True)


def assistant(acct, notice=None, locked=False):
    email = escape(acct["paypal"].get("email") or "PayPal")
    body = """<h1 class="sr-only">ClearCart assistant</h1>
<div class="desk">
<section class="convo" aria-labelledby="chat-h">
<div class="buddy">%s<p class="chips"><span class="chip">PayPal: <strong>%s</strong></span>
<span class="chip">Limit: <strong>%s</strong> per purchase</span>
<a href="/setup">Change PIN or limit</a></p></div>
<h2 id="chat-h" class="sr-only">Conversation</h2>
<div id="log" class="log" role="log" aria-live="polite" aria-relevant="additions" tabindex="0" aria-label="Conversation">
<p class="msg bot"><span class="who">ClearCart<span class="sr-only">:</span></span> Hi. What would you like? For example, "I need a notebook under 5 pounds", "Where's my order?" or "I want a refund."</p>
</div>

<form id="chat-form" class="chat-form">
<label for="msg">Type a message</label>
<div class="row send-row">
<input id="msg" type="text" autocomplete="off" required>
<button type="submit">Send</button>
<button type="button" id="mic" class="secondary" hidden aria-pressed="false">Talk</button>
</div>
<div class="check">
<input type="checkbox" id="speak"><label for="speak" class="inline">Read replies aloud (turn off if you use a screen reader)</label>
</div>
</form>
<p id="voice-status" class="muted"></p>
<p id="voice-note" class="muted" hidden>Voice input works in Chrome and Edge. In other browsers, type instead.</p>
</section>

<div class="side">
<section id="confirm" class="plate" hidden aria-labelledby="confirm-h">
%s
<h2 id="confirm-h" tabindex="-1">Check before you confirm</h2>
<p class="plate-sub" id="confirm-sub">Nothing has been charged yet.</p>
<p id="readback" class="readback"></p>
<div class="meter" id="confirm-meter" hidden>
<p id="confirm-meter-text"></p>
<span class="tape-meter" aria-hidden="true"><span id="confirm-meter-bar"></span></span>
</div>
<form id="pin-form">
%s
<div class="row"><button type="submit" id="pin-submit">Confirm</button>
<button type="button" id="cancel" class="secondary">Cancel</button></div>
</form>
</section>

<section id="unlock" class="plate" hidden aria-labelledby="unlock-h">
<h2 id="unlock-h" tabindex="-1">ClearCart is locked</h2>
<p class="plate-sub">It locked itself after a few minutes without use.</p>
<form id="unlock-form">
%s
<p><button type="submit">Unlock</button></p>
</form>
</section>

<section class="hints" aria-labelledby="hints-h">
<h2 id="hints-h">Things you can ask</h2>
<ul>
<li>"I need a notebook under 5 pounds."</li>
<li>"Did my last order go through?"</li>
<li>"Where's my order?"</li>
<li>"Show my orders."</li>
<li>"I want a refund."</li>
</ul>
<p>When something needs paying or refunding, it appears here. Type your PIN to confirm. Saying yes is never enough.</p>
</section>
</div>
</div>
""" % (mascot("mascot buddy-mascot"), email, escape(catalog.money(acct["limit"])),
       mascot("mascot plate-mascot"),
       pin_field("pin", "Type your 4-digit PIN, then press Enter", on_plate=True),
       pin_field("unlock-pin", "Type your 4-digit PIN to unlock", on_plate=True))
    init = {"locked": bool(locked), "pending": pending_view(acct)}
    scripts = ('<script>window.CLEARCART=%s;</script><script src="/static/app.js"></script>'
               % json.dumps(init))
    return layout("Assistant", body, notice, scripts, current="assistant", wide=True)


def _limit_meter(price, limit):
    """The total drawn as a length of the shopper's spending limit."""
    try:
        share = max(0, min(100, int(Decimal(price) / Decimal(limit) * 100)))
    except Exception:
        return ""
    return """<div class="meter">
<p>%s of your %s limit</p>
<span class="tape-meter" aria-hidden="true"><span style="width:%d%%"></span></span>
</div>""" % (catalog.money(price), catalog.money(limit), share)


def confirm(product, acct, notice=None):
    price = catalog.money(product["price"])
    words = catalog.money_words(product["price"])
    if not acct or not acct.get("pin_hash"):
        body = """<h1>Check your order</h1>
<p class="lead">%s, %s.</p>
<p>To pay, first link your PayPal account and set your PIN.</p>
<p class="actions"><a class="button" href="/">Get started</a> <a class="quiet-link" href="/store">Back to the store</a></p>""" % (
            escape(product["name"]), price)
        return layout("Check your order", body, notice, current="store")
    body = """<div class="intro">
<section class="lead-col" aria-labelledby="check-h">
<h1 id="check-h">Check your order</h1>
<p id="readback" class="lead">%(name)s, quantity 1, %(words)s. Total %(words)s.
Paid with your linked PayPal account, %(email)s. Nothing has been charged yet.</p>
<dl class="summary">
<dt>Item</dt><dd>%(name)s</dd>
<dt>Quantity</dt><dd>1</dd>
<dt>Total</dt><dd>%(price)s</dd>
<dt>Pay with</dt><dd>PayPal (%(email)s)</dd>
</dl>
</section>
<section class="plate" aria-labelledby="pay-h">
%(mascot)s
<h2 id="pay-h">Pay %(price)s</h2>
<p class="plate-sub">Nothing has been charged yet.</p>
%(meter)s
<form method="post" action="/pay">
<input type="hidden" name="product_id" value="%(id)s">
<input type="hidden" name="expected_total" value="%(raw)s">
%(pin)s
<p><button type="submit" aria-describedby="readback">Pay %(price)s with PayPal</button></p>
</form>
<p><a href="/store">Cancel and go back</a></p>
</section>
</div>""" % {
        "name": escape(product["name"]), "words": words, "price": price, "raw": product["price"],
        "email": escape(acct["paypal"].get("email") or "PayPal account"), "id": product["id"],
        "mascot": mascot("mascot plate-mascot"),
        "meter": _limit_meter(product["price"], acct.get("limit", "30")),
        "pin": pin_field("pin", "Type your 4-digit PIN to pay", name="pin", on_plate=True)}
    return layout("Check your order", body, notice, current="store", wide=True)


def receipt(summary, source):
    def plain(status):
        return escape(str(status).replace("_", " ").capitalize())
    if summary["status"] == "COMPLETED":
        heading = "Payment complete"
        lead = "PayPal says the payment is complete: %s." % summary["total_words"]
    else:
        heading = "Payment status: %s" % str(summary["status"]).replace("_", " ").capitalize()
        lead = "PayPal says the order status is %s." % str(summary["status"]).replace("_", " ").lower()

    def status_tape(status):
        cls = "ok" if status == "COMPLETED" else ""
        return '<span class="tag %s">%s</span>' % (cls, plain(status))
    rows = "".join("<dt>%s</dt><dd>%s</dd>" % (escape(k), v) for k, v in [
        ("Item", escape(str(summary["items"]))),
        ("Total", escape(str(summary["total"]))),
        ("Order status", status_tape(summary["status"])),
        ("Payment status", status_tape(summary["capture_status"])),
        ("PayPal order ID", escape(str(summary["order_id"]))),
        ("PayPal transaction ID", escape(str(summary["capture_id"]))),
    ])
    body = """<h1>%s</h1>
<p id="lead" class="lead">%s</p>
<dl class="summary sheet">%s</dl>
<p class="source">Checked with PayPal just now, using %s.</p>
<p class="actions"><a class="button" href="/">Back to the assistant</a></p>""" % (
        escape(heading), escape(lead), rows, escape(source))
    return layout(heading, body)


def error(title, message, detail=None):
    extra = '<details><summary>Technical details</summary><pre>%s</pre></details>' % escape(detail) if detail else ""
    body = """<h1>%s</h1>
<p role="alert" class="lead">%s</p>
%s
<p class="actions"><a class="button" href="/">Back to the assistant</a> <a class="quiet-link" href="/store">Go to the store</a></p>""" % (escape(title), escape(message), extra)
    return layout(title, body)
