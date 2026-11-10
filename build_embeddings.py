"""Create or update product_embeddings.json.

Run it whenever products change:
    python build_embeddings.py

Only products that are new or whose text changed are sent to Gemini.
Commit product_embeddings.json so the app never has to embed products at startup.
"""

import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import search

stale = search.load()
print("Model: %s, %d dimensions" % (search.EMBED_MODEL, search.EMBED_DIMS))
print("Products already embedded and up to date: %d" % search.status["products_embedded"])
print("Products to embed now: %d" % len(stale))
if stale:
    t0 = time.time()
    n = search.refresh(stale, save=True)
    print("Embedded %d products in %.1f s" % (n, time.time() - t0))
print("Saved: %s" % search.EMB_FILE)
