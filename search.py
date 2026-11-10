"""Product search by meaning (embeddings), with a keyword search as backup.

How it works
- Each product's text is turned into numbers (an "embedding") ONCE and saved in
  product_embeddings.json. The app loads that file at startup: no calls needed.
- If a product's text changes, only that product is re-embedded (we keep a
  fingerprint of each product's text).
- A shopper's request is embedded when they ask (cached, so repeats are free),
  and products are ranked by closeness in meaning.
- Price limits are applied by code, never by the AI or the embeddings.
- If the embedding service fails, we fall back to keyword search.

For a big store, the same idea moves to a vector database (e.g. Postgres + pgvector).
"""

import hashlib
import json
import logging
import math
import os
import re
import threading
import time
from collections import OrderedDict
from decimal import Decimal, InvalidOperation

import requests

import catalog

log = logging.getLogger("clearcart.search")

EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-001")
EMBED_DIMS = int(os.environ.get("EMBED_DIMS", "768"))
EMBED_TIMEOUT = float(os.environ.get("EMBED_TIMEOUT", "8"))
EMB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "product_embeddings.json")
API_BASE = "https://generativelanguage.googleapis.com/v1beta"
BATCH_LIMIT = 100
QUERY_CACHE_SIZE = 256

_session = requests.Session()          # keeps the connection to Google open between calls
_vectors = {}                           # product_id -> normalized vector
_lock = threading.Lock()
_query_cache = OrderedDict()            # normalized query text -> vector
status = {"model": EMBED_MODEL, "dims": EMBED_DIMS, "products_embedded": 0,
          "products_total": len(catalog.PRODUCTS), "last_error": None, "last_method": None}

STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "to", "of", "in", "on", "at", "by", "my", "me",
    "i", "im", "i'm", "need", "want", "would", "like", "some", "something", "thing", "things",
    "please", "can", "you", "get", "buy", "find", "show", "looking", "look", "any", "that", "this",
    "is", "are", "be", "it", "under", "below", "less", "than", "pounds", "pound", "max", "up",
    "around", "about", "help", "use", "so", "do", "have", "one", "more", "good", "nice", "new",
}


# ---- Text and vectors -----------------------------------------------------------

def product_text(p):
    return "%s. Category: %s. %s" % (p["name"], p["category"], p["description"])


def fingerprint(text):
    return hashlib.sha256(("%s|%d|%s" % (EMBED_MODEL, EMBED_DIMS, text)).encode()).hexdigest()[:16]


def _normalize(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def embed_texts(texts, task_type):
    """Embed texts with Gemini. task_type: RETRIEVAL_DOCUMENT (products) or RETRIEVAL_QUERY (requests)."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    out = []
    for i in range(0, len(texts), BATCH_LIMIT):
        chunk = texts[i:i + BATCH_LIMIT]
        body = {"requests": [{"model": "models/" + EMBED_MODEL,
                              "content": {"parts": [{"text": t}]},
                              "taskType": task_type,
                              "outputDimensionality": EMBED_DIMS} for t in chunk]}
        r = _session.post("%s/models/%s:batchEmbedContents" % (API_BASE, EMBED_MODEL),
                          headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                          json=body, timeout=EMBED_TIMEOUT if len(chunk) == 1 else 60)
        if r.status_code != 200:
            raise RuntimeError("Embedding HTTP %s: %s" % (r.status_code, r.text[:300]))
        out.extend(_normalize(e["values"]) for e in r.json()["embeddings"])
    return out


# ---- Stored product embeddings --------------------------------------------------

def _read_file():
    try:
        with open(EMB_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def load():
    """Load saved embeddings. Returns the ids of products that are missing or out of date."""
    data = _read_file()
    stored = data.get("products", {}) if data.get("model") == EMBED_MODEL and data.get("dims") == EMBED_DIMS else {}
    stale = []
    with _lock:
        _vectors.clear()
        for p in catalog.PRODUCTS:
            entry = stored.get(p["id"])
            if entry and entry.get("fingerprint") == fingerprint(product_text(p)):
                _vectors[p["id"]] = entry["vector"]
            else:
                stale.append(p["id"])
        status["products_embedded"] = len(_vectors)
    log.info("Embeddings loaded: %d of %d products (%d need embedding)",
             len(_vectors), len(catalog.PRODUCTS), len(stale))
    return stale


def refresh(stale_ids, save=True):
    """Embed only the products that are missing or changed, then save the file."""
    if not stale_ids:
        return 0
    products = [catalog.get(pid) for pid in stale_ids if catalog.get(pid)]
    vectors = embed_texts([product_text(p) for p in products], "RETRIEVAL_DOCUMENT")
    with _lock:
        for p, v in zip(products, vectors):
            _vectors[p["id"]] = v
        status["products_embedded"] = len(_vectors)
    if save:
        save_file()
    return len(products)


def save_file():
    with _lock:
        data = {"model": EMBED_MODEL, "dims": EMBED_DIMS, "products": {
            p["id"]: {"fingerprint": fingerprint(product_text(p)),
                      "vector": [round(x, 6) for x in _vectors[p["id"]]]}
            for p in catalog.PRODUCTS if p["id"] in _vectors}}
    try:
        with open(EMB_FILE, "w") as f:
            json.dump(data, f, separators=(",", ":"))
    except OSError as e:  # read-only disk on some hosts: fine, they stay in memory
        log.warning("Could not save embeddings file: %r", e)


def start_background_refresh():
    """At app startup: load the file; embed anything missing in the background."""
    stale = load()
    if stale and os.environ.get("GEMINI_API_KEY"):
        def work():
            try:
                n = refresh(stale)
                log.info("Embedded %d products at startup", n)
            except Exception as e:
                status["last_error"] = str(e)[:300]
                log.warning("Could not embed products at startup (keyword search will be used): %r", e)
        threading.Thread(target=work, daemon=True).start()


# ---- Query embeddings (cached) ----------------------------------------------------

def embed_query(text):
    key = " ".join(text.lower().split())
    with _lock:
        if key in _query_cache:
            _query_cache.move_to_end(key)
            return _query_cache[key]
    vec = embed_texts([text], "RETRIEVAL_QUERY")[0]
    with _lock:
        _query_cache[key] = vec
        while len(_query_cache) > QUERY_CACHE_SIZE:
            _query_cache.popitem(last=False)
    return vec


# ---- Search -------------------------------------------------------------------------

def _words(text):
    out = []
    for w in re.findall(r"[a-z0-9]+", (text or "").lower()):
        if w in STOPWORDS or len(w) < 3:
            continue
        out.append(w[:-1] if len(w) > 4 and w.endswith("s") else w)   # "pens" -> "pen"
    return out


def _keyword_score(p, words):
    name = p["name"].lower()
    hay = (p["name"] + " " + p["description"] + " " + p["category"]).lower()
    return sum(2 if w in name else 1 for w in words if w in hay)


def parse_max_price(text):
    """Find a price limit like 'under 5 pounds', 'below £10', 'up to 7.50'. Returns Decimal or None."""
    t = (text or "").lower()
    m = re.search(r"(?:under|below|less than|cheaper than|max(?:imum)?|up to|at most|no more than|within)\s*£?\s*(\d+(?:\.\d{1,2})?)", t)
    if not m:
        m = re.search(r"£?\s*(\d+(?:\.\d{1,2})?)\s*(?:pounds?|quid|£)?\s*(?:or less|or under|max)", t)
    if not m:
        return None
    try:
        return Decimal(m.group(1))
    except InvalidOperation:
        return None


def search(query, max_price=None, k=3):
    """Returns (products, method). method is 'meaning' or 'keyword'."""
    items = catalog.PRODUCTS
    if max_price not in (None, ""):
        try:
            cap = Decimal(str(max_price))
            items = [p for p in items if Decimal(p["price"]) <= cap]
        except (InvalidOperation, ValueError):
            pass
    if not items:
        return [], "none"
    query = (query or "").strip()
    words = _words(query)

    if query and all(p["id"] in _vectors for p in items):
        try:
            qv = embed_query(query)
            scored = sorted(items, key=lambda p: -(_dot(qv, _vectors[p["id"]]) + 0.02 * _keyword_score(p, words)))
            status["last_method"] = "meaning"
            return scored[:k], "meaning"
        except Exception as e:
            status["last_error"] = str(e)[:300]
            log.warning("Meaning search failed, using keywords: %r", e)

    status["last_method"] = "keyword"
    if not words:
        return sorted(items, key=lambda p: -p["rating"])[:k], "keyword"
    scored = [(p, _keyword_score(p, words)) for p in items]
    hits = [p for p, s in sorted(scored, key=lambda x: (-x[1], -x[0]["rating"])) if s > 0]
    return hits[:k], "keyword"


def keyword_only(query, max_price=None, k=3):
    """Old-style keyword search, used by the evaluation script for comparison."""
    saved = dict(_vectors)
    with _lock:
        _vectors.clear()
    try:
        return search(query, max_price, k)
    finally:
        with _lock:
            _vectors.update(saved)
