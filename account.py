"""The shopper's account state: linked PayPal account, PIN, limit, orders, pending action.

Stored inside the session cookie, **encrypted** (so the PIN hash and PayPal token
can't be read from the browser). No database, so it survives host restarts as long
as SESSION_SECRET stays the same.

Demo limitation: because state lives in the cookie, an attacker who saved an old
cookie could replay it to reset the wrong-PIN counter. A real deployment would keep
attempt counters on the server.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from cryptography.fernet import Fernet, InvalidToken

AUTO_LOCK_SECONDS = int(os.environ.get("AUTO_LOCK_SECONDS", "300"))   # 5 minutes idle
MAX_PIN_ATTEMPTS = 3
LOCKOUT_SECONDS = int(os.environ.get("LOCKOUT_SECONDS", "300"))       # 5 minutes
MAX_ORDERS_KEPT = 8

_secret = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)
SESSION_SECRET = _secret
_fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(("acct:" + _secret).encode()).digest()))


def load(request):
    blob = request.session.get("acct")
    if not blob:
        return {}
    try:
        return json.loads(_fernet.decrypt(blob.encode()).decode())
    except (InvalidToken, ValueError):
        return {}


def save(request, acct):
    request.session["acct"] = _fernet.encrypt(json.dumps(acct, separators=(",", ":")).encode()).decode()


# ---- PIN --------------------------------------------------------------------

def hash_pin(pin, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt), 200_000).hex()
    return salt, digest


def valid_pin_format(pin):
    return isinstance(pin, str) and len(pin) == 4 and pin.isdigit()


def is_set_up(acct):
    return bool(acct.get("paypal") and acct.get("pin_hash") and acct.get("limit"))


def locked_out_for(acct):
    """Seconds left in a wrong-PIN lockout (0 if not locked out)."""
    return max(0, int(acct.get("locked_until", 0) - time.time()))


def check_pin(acct, pin):
    """Returns (ok, message). Updates attempt counters in `acct` (caller must save)."""
    wait = locked_out_for(acct)
    if wait:
        return False, "Too many wrong PINs. Payments are locked for %d more minutes." % max(1, round(wait / 60))
    if not valid_pin_format(pin or ""):
        return False, "Please type your 4-digit PIN."
    _, digest = hash_pin(pin, acct["pin_salt"])
    if hmac.compare_digest(digest, acct["pin_hash"]):
        acct["attempts"] = 0
        acct["last_active"] = time.time()
        return True, ""
    acct["attempts"] = acct.get("attempts", 0) + 1
    left = MAX_PIN_ATTEMPTS - acct["attempts"]
    if left <= 0:
        acct["attempts"] = 0
        acct["locked_until"] = time.time() + LOCKOUT_SECONDS
        acct.pop("pending", None)
        return False, ("Wrong PIN. That was the third try, so payments and refunds are locked for %d minutes. "
                       "Nothing was charged." % (LOCKOUT_SECONDS // 60))
    return False, "Wrong PIN. Nothing was charged. %d %s left." % (left, "try" if left == 1 else "tries")


# ---- Auto-lock --------------------------------------------------------------

def is_idle_locked(acct):
    last = acct.get("last_active")
    return bool(last) and time.time() - last > AUTO_LOCK_SECONDS


def touch(acct):
    acct["last_active"] = time.time()


# ---- Orders -------------------------------------------------------------------

def add_order(acct, order):
    orders = acct.get("orders", [])
    orders.append(order)
    acct["orders"] = orders[-MAX_ORDERS_KEPT:]


def find_order(acct, order_id=None):
    orders = acct.get("orders", [])
    if not orders:
        return None
    if not order_id:
        return orders[-1]
    oid = order_id.strip().upper()
    for o in orders:
        if o["id"].upper() == oid:
            return o
    return None
