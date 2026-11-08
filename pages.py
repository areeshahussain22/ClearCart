"""HTML pages. Plain, semantic HTML so screen readers and keyboards work well."""

from html import escape

import catalog


def layout(title, body, notice=None):
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
<header class="site"><p class="brand"><a href="/">ClearCart</a></p>
<p class="tag">Demo store · PayPal sandbox · no real money</p></header>
<main id="main" tabindex="-1">
%s
%s
</main>
</body>
</html>""" % (escape(title), live, body)


def paypal_status(linked):
    if linked:
        return ("""<section class="panel" aria-labelledby="pp-h">
<h2 id="pp-h">Your PayPal account</h2>
<p>Linked: <strong>%s</strong>. You can pay without opening PayPal each time.</p>
<form method="post" action="/unlink"><button type="submit" class="secondary">Unlink PayPal</button></form>
</section>""" % escape(linked.get("email") or "PayPal account"))
    return """<section class="panel" aria-labelledby="pp-h">
<h2 id="pp-h">Your PayPal account</h2>
<p>Not linked yet. Link it once, on PayPal's own page. After that you can pay here without opening PayPal again.</p>
<p><a class="button" href="/link">Link PayPal</a></p>
</section>"""


def home(linked, notice=None):
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
    body = """<h1>ClearCart demo store</h1>
%s
<section aria-labelledby="prod-h">
<h2 id="prod-h">Products</h2>
<ul class="products">%s</ul>
</section>""" % (paypal_status(linked), "\n".join(items))
    return layout("Store", body, notice)


def confirm(product, linked, notice=None):
    price = catalog.money(product["price"])
    words = catalog.money_words(product["price"])
    if not linked:
        body = """<h1>Check your order</h1>
<p>%s, %s.</p>
<p>To pay, first link your PayPal account.</p>
<p><a class="button" href="/link">Link PayPal</a> <a href="/">Back to the store</a></p>""" % (
            escape(product["name"]), price)
        return layout("Check your order", body, notice)
    body = """<h1>Check your order</h1>
<p id="readback">%(name)s, quantity 1, %(words)s. Total %(words)s.
Paid with your linked PayPal account, %(email)s. Nothing has been charged yet.</p>
<dl class="summary">
<dt>Item</dt><dd>%(name)s</dd>
<dt>Quantity</dt><dd>1</dd>
<dt>Price</dt><dd>%(price)s</dd>
<dt>Total</dt><dd>%(price)s</dd>
<dt>Pay with</dt><dd>PayPal (%(email)s)</dd>
</dl>
<form method="post" action="/pay">
<input type="hidden" name="product_id" value="%(id)s">
<input type="hidden" name="expected_total" value="%(raw)s">
<button type="submit" aria-describedby="readback">Pay %(price)s with PayPal</button>
</form>
<p><a href="/">Cancel and go back</a></p>""" % {
        "name": escape(product["name"]), "words": words, "price": price, "raw": product["price"],
        "email": escape(linked.get("email") or "PayPal account"), "id": product["id"]}
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
<p><a class="button" href="/">Back to the store</a></p>""" % (
        escape(heading), escape(lead), rows, escape(source))
    return layout(heading, body)


def error(title, message, detail=None):
    extra = '<details><summary>Technical details</summary><pre>%s</pre></details>' % escape(detail) if detail else ""
    body = """<h1>%s</h1>
<p role="alert">%s</p>
%s
<p><a class="button" href="/">Back to the store</a></p>""" % (escape(title), escape(message), extra)
    return layout(title, body)
