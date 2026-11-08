"""Direct calls to PayPal's REST API (sandbox).

Used for the steps PayPal's MCP tools don't cover:
- linking (saving) the buyer's PayPal account
- paying with the saved account
It also gives the access token that the MCP server needs.
"""

import os
import time
import uuid

import requests

BASE = os.environ.get("PAYPAL_API_BASE", "https://api-m.sandbox.paypal.com")

_token = {"value": None, "expires_at": 0.0}


class PayPalError(Exception):
    def __init__(self, step, status, body):
        super().__init__("%s failed (HTTP %s)" % (step, status))
        self.step = step
        self.status = status
        self.body = body


def access_token():
    """Return a valid access token, reusing it until 5 minutes before it expires."""
    if _token["value"] and time.time() < _token["expires_at"] - 300:
        return _token["value"]
    cid = os.environ.get("PAYPAL_CLIENT_ID")
    secret = os.environ.get("PAYPAL_CLIENT_SECRET")
    if not cid or not secret:
        raise RuntimeError("PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET are not set.")
    r = requests.post(BASE + "/v1/oauth2/token", auth=(cid, secret),
                      data={"grant_type": "client_credentials"}, timeout=30)
    if r.status_code != 200:
        raise PayPalError("get access token", r.status_code, r.text[:500])
    d = r.json()
    _token["value"] = d["access_token"]
    _token["expires_at"] = time.time() + float(d.get("expires_in", 3600))
    return _token["value"]


def token_expires_at():
    return _token["expires_at"]


def _headers(extra=None):
    h = {"Authorization": "Bearer " + access_token(),
         "Content-Type": "application/json",
         "PayPal-Request-Id": str(uuid.uuid4())}
    if extra:
        h.update(extra)
    return h


def create_setup_token(return_url, cancel_url):
    """Step 1 of linking: returns (setup_token_id, approve_url)."""
    body = {"payment_source": {"paypal": {
        "description": "ClearCart saved PayPal account",
        "permit_multiple_payment_tokens": False,
        "usage_pattern": "IMMEDIATE",
        "usage_type": "MERCHANT",
        "customer_type": "CONSUMER",
        "experience_context": {
            "shipping_preference": "NO_SHIPPING",
            "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
            "brand_name": "ClearCart",
            "locale": "en-GB",
            "return_url": return_url,
            "cancel_url": cancel_url,
        },
    }}}
    r = requests.post(BASE + "/v3/vault/setup-tokens", headers=_headers(), json=body, timeout=30)
    if r.status_code not in (200, 201):
        raise PayPalError("create setup token", r.status_code, r.text[:800])
    d = r.json()
    approve = next((l["href"] for l in d.get("links", []) if l.get("rel") == "approve"), None)
    if not approve:
        raise PayPalError("create setup token (no approve link)", r.status_code, r.text[:800])
    return d["id"], approve


def create_payment_token(setup_token_id):
    """Step 2 of linking, after the buyer approves. Returns the saved account details."""
    body = {"payment_source": {"token": {"id": setup_token_id, "type": "SETUP_TOKEN"}}}
    r = requests.post(BASE + "/v3/vault/payment-tokens", headers=_headers(), json=body, timeout=30)
    if r.status_code not in (200, 201):
        raise PayPalError("save PayPal account", r.status_code, r.text[:800])
    d = r.json()
    paypal = (d.get("payment_source") or {}).get("paypal", {})
    return {"payment_token_id": d["id"],
            "customer_id": (d.get("customer") or {}).get("id"),
            "email": paypal.get("email_address")}


def pay_with_saved_account(payment_token_id, item, unit_price, quantity, currency):
    """Create and capture an order with the saved account. No PayPal page opens.

    `unit_price` must come from the server's catalog, never from the browser.
    Returns the PayPal order (dict).
    """
    total = (unit_price * quantity).quantize(unit_price.__class__("0.01"))
    body = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": "clearcart",
            "description": "ClearCart order",
            "amount": {
                "currency_code": currency,
                "value": str(total),
                "breakdown": {"item_total": {"currency_code": currency, "value": str(total)}},
            },
            "items": [{
                "name": item["name"][:127],
                "sku": item["id"],
                "quantity": str(quantity),
                "unit_amount": {"currency_code": currency, "value": str(unit_price)},
                "category": "PHYSICAL_GOODS",
            }],
        }],
        "payment_source": {"paypal": {"vault_id": payment_token_id}},
    }
    extra = {"PayPal-Client-Metadata-Id": uuid.uuid4().hex[:32]}
    r = requests.post(BASE + "/v2/checkout/orders", headers=_headers(extra), json=body, timeout=45)
    if r.status_code not in (200, 201):
        raise PayPalError("pay with saved account", r.status_code, r.text[:800])
    d = r.json()
    if d.get("status") == "APPROVED":  # some accounts need a separate capture
        c = requests.post(BASE + "/v2/checkout/orders/%s/capture" % d["id"], headers=_headers(), timeout=45)
        if c.status_code not in (200, 201):
            raise PayPalError("capture payment", c.status_code, c.text[:800])
        d = c.json()
    return d


def get_order(order_id):
    """REST fallback, used only if the MCP tool is unavailable."""
    r = requests.get(BASE + "/v2/checkout/orders/" + order_id, headers=_headers(), timeout=30)
    if r.status_code != 200:
        raise PayPalError("get order", r.status_code, r.text[:800])
    return r.json()
