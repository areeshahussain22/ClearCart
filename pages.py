"""HTML pages. Plain, semantic HTML so screen readers and keyboards work well."""

import json
from html import escape

import catalog


def layout(title, body, notice=None, scripts=""):
    live = ('<div id="notice" class="notice" role="status" aria-live="polite">%s</div>'
            % escape(notice)) if notice else '<div id="notice" role="status" aria-live="polite"></div>'
    return """<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s · ClearCart</title>
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to main content</a>
<header class="site">
<p class="brand"><a href="/">ClearCart</a></p>
<p class="tag">Demo store · PayPal sandbox · no real money</p>
<nav aria-label="Main"><a href="/">Assistant</a> <a href="/store">Store</a></nav>
</header>
<main id="main" tabindex="-1">
%s
%s
</main>
%s
</body>
</html>""" % (escape(title), live, body, scripts)


def welcome(notice=None):
    body = """<h1>Shop by voice or keyboard, pay with PayPal</h1>
<p>ClearCart helps you find products, pay, check and track orders, and ask for refunds, by talking or typing.</p>
<section class="panel" aria-labelledby="start-h">
<h2 id="start-h">Get started</h2>
<ol>
<li>Link your PayPal account once, on PayPal's own page.</li>
<li>Choose a 4-digit PIN and a spending limit.</li>
<li>Then just ask, for example: "I need a notebook under 5 pounds."</li>
</ol>
<p><a class="button" href="/link">Link PayPal</a></p>
</section>
<p>Or <a href="/store">browse the store</a> first.</p>"""
    return layout("Welcome", body, notice)


def store(linked_acct, notice=None):
    items = []
    for p in catalog.PRODUCTS:
        items.append("""<li class="product">
<h3 id="h-%(id)s">%(name)s</h3>
<p class="price">%(price)s <span class="sr-only">(%(words)s)</span></p>
<p>Rating %(rating)s out of 5. %(desc)s</p>
<p><a class="button" href="/confirm/%(id)s" aria-describedby="h-%(id)s">Buy</a></p>
</li>""" % {"id": p["id"], "name": escape(p["name"]), "price": catalog.money(p["price"]),
            "words": catalog.money_words(p["price"]), "rating": p["rating"],
            "desc": escape(p["description"])})
    if linked_acct:
        status = '<p>PayPal linked: <strong>%s</strong>.</p>' % escape(linked_acct["paypal"].get("email") or "")
    else:
        status = '<p>PayPal is not linked yet. <a href="/link">Link PayPal</a> to buy.</p>'
    body = """<h1>Store</h1>
%s
<ul class="products">%s</ul>""" % (status, "\n".join(items))
    return layout("Store", body, notice)


def setup(acct, notice=None):
    body = """<h1>Set your PIN and spending limit</h1>
<p>PayPal is linked: <strong>%s</strong>.</p>
<p>Your PIN is typed, never spoken, so nobody can copy it from your voice. You'll type it for every payment and refund.</p>
<form method="post" action="/setup" class="stack">
<label for="pin">Choose a 4-digit PIN</label>
<input id="pin" name="pin" type="password" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" autocomplete="new-password" required>
<label for="pin2">Type the PIN again</label>
<input id="pin2" name="pin2" type="password" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" autocomplete="new-password" required>
<label for="limit">Spending limit per purchase, in pounds</label>
<input id="limit" name="limit" type="number" min="1" max="500" step="1" value="%s" required>
<button type="submit">Save</button>
</form>
<form method="post" action="/unlink"><button type="submit" class="secondary">Unlink PayPal</button></form>""" % (
        escape(acct["paypal"].get("email") or "PayPal"), escape(str(int(float(acct.get("limit", 30))))))
    return layout("Set up", body, notice)


def assistant(acct, notice=None, locked=False):
    email = escape(acct["paypal"].get("email") or "PayPal")
    body = """<h1>ClearCart assistant</h1>
<p class="muted">PayPal: <strong>%s</strong> · Spending limit: %s per purchase · <a href="/setup">Change PIN or limit</a></p>

<section aria-labelledby="chat-h">
<h2 id="chat-h" class="sr-only">Conversation</h2>
<div id="log" class="log" role="log" aria-live="polite" aria-relevant="additions">
<p class="msg bot"><span class="who">ClearCart:</span> Hi. What would you like? For example, "I need a notebook under 5 pounds", "Where's my order?" or "I want a refund."</p>
</div>
</section>

<section id="confirm" class="panel" hidden aria-labelledby="confirm-h">
<h2 id="confirm-h" tabindex="-1">Check before you confirm</h2>
<p id="readback"></p>
<form id="pin-form" class="stack">
<label for="pin">Type your 4-digit PIN, then press Enter</label>
<input id="pin" type="password" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" autocomplete="off" required>
<div class="row"><button type="submit" id="pin-submit">Confirm</button>
<button type="button" id="cancel" class="secondary">Cancel</button></div>
</form>
</section>

<section id="unlock" class="panel" hidden aria-labelledby="unlock-h">
<h2 id="unlock-h" tabindex="-1">ClearCart is locked</h2>
<p>It locked itself after a few minutes without use.</p>
<form id="unlock-form" class="stack">
<label for="unlock-pin">Type your 4-digit PIN to unlock</label>
<input id="unlock-pin" type="password" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" autocomplete="off" required>
<button type="submit">Unlock</button>
</form>
</section>

<form id="chat-form" class="chat-form">
<label for="msg">Type a message</label>
<div class="row">
<input id="msg" type="text" autocomplete="off" required>
<button type="submit">Send</button>
<button type="button" id="mic" class="secondary" hidden aria-pressed="false">Talk</button>
</div>
<div class="row">
<input type="checkbox" id="speak"><label for="speak" class="inline">Read replies aloud (turn off if you use a screen reader)</label>
</div>
</form>
<p id="voice-status" class="muted"></p>
<p id="voice-note" class="muted" hidden>Voice input works in Chrome and Edge. In other browsers, type instead.</p>
""" % (email, catalog.money_words(acct["limit"]))
    pending = acct.get("pending")
    init = {"locked": bool(locked),
            "pending": {"type": pending["type"], "readback": pending["readback"]} if pending else None}
    scripts = ('<script>window.CLEARCART=%s;</script><script src="/static/app.js"></script>'
               % json.dumps(init))
    return layout("Assistant", body, notice, scripts)


def confirm(product, acct, notice=None):
    price = catalog.money(product["price"])
    words = catalog.money_words(product["price"])
    if not acct or not acct.get("pin_hash"):
        body = """<h1>Check your order</h1>
<p>%s, %s.</p>
<p>To pay, first link your PayPal account and set your PIN.</p>
<p><a class="button" href="/">Get started</a> <a href="/store">Back to the store</a></p>""" % (
            escape(product["name"]), price)
        return layout("Check your order", body, notice)
    body = """<h1>Check your order</h1>
<p id="readback">%(name)s, quantity 1, %(words)s. Total %(words)s.
Paid with your linked PayPal account, %(email)s. Nothing has been charged yet.</p>
<dl class="summary">
<dt>Item</dt><dd>%(name)s</dd>
<dt>Quantity</dt><dd>1</dd>
<dt>Total</dt><dd>%(price)s</dd>
<dt>Pay with</dt><dd>PayPal (%(email)s)</dd>
</dl>
<form method="post" action="/pay" class="stack">
<input type="hidden" name="product_id" value="%(id)s">
<input type="hidden" name="expected_total" value="%(raw)s">
<label for="pin">Type your 4-digit PIN to pay</label>
<input id="pin" name="pin" type="password" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" autocomplete="off" required>
<button type="submit" aria-describedby="readback">Pay %(price)s with PayPal</button>
</form>
<p><a href="/store">Cancel and go back</a></p>""" % {
        "name": escape(product["name"]), "words": words, "price": price, "raw": product["price"],
        "email": escape(acct["paypal"].get("email") or "PayPal account"), "id": product["id"]}
    return layout("Check your order", body, notice)


def receipt(summary, source):
    if summary["status"] == "COMPLETED":
        heading = "Payment complete"
        lead = "PayPal says the payment is complete: %s." % summary["total_words"]
    else:
        heading = "Payment status: %s" % summary["status"]
        lead = "PayPal says the order status is %s." % summary["status"]
    rows = "".join("<dt>%s</dt><dd>%s</dd>" % (escape(k), escape(str(v))) for k, v in [
        ("Item", summary["items"]),
        ("Total", summary["total"]),
        ("Order status", summary["status"]),
        ("Payment status", summary["capture_status"]),
        ("PayPal order ID", summary["order_id"]),
        ("PayPal transaction ID", summary["capture_id"]),
    ])
    body = """<h1>%s</h1>
<p id="lead">%s</p>
<dl class="summary">%s</dl>
<p class="source">Checked with PayPal just now, using %s.</p>
<p><a class="button" href="/">Back to the assistant</a></p>""" % (
        escape(heading), escape(lead), rows, escape(source))
    return layout(heading, body)


def error(title, message, detail=None):
    extra = '<details><summary>Technical details</summary><pre>%s</pre></details>' % escape(detail) if detail else ""
    body = """<h1>%s</h1>
<p role="alert">%s</p>
%s
<p><a class="button" href="/">Back</a></p>""" % (escape(title), escape(message), extra)
    return layout(title, body)
