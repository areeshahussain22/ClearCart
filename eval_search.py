"""Measure search quality: old keyword search vs meaning (embedding) search.

    python eval_search.py

For each test request we know which product(s) are right. We count how often a right
product is the first result (top 1) and appears in the first 3 results (top 3), and
time each search. Results are also saved to eval_results.json.
"""

import json
import statistics
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import catalog
import search

# (request, acceptable product ids). Mix of exact words and everyday, vague wording.
TESTS = [
    ("notebook", {"p01"}),
    ("pens", {"p02"}),
    ("chocolate", {"p11"}),
    ("earphones", {"p14"}),
    ("headphones for music", {"p14"}),
    ("something to write with", {"p02"}),
    ("I'm thirsty", {"p08"}),
    ("something to carry water on a walk", {"p08"}),
    ("something warm for winter nights", {"p18"}),
    ("label my spice jars so I can feel them", {"p04", "p06"}),
    ("mark the buttons on my microwave", {"p06"}),
    ("know when my pasta is done", {"p05"}),
    ("charge my phone", {"p13"}),
    ("hold my phone while I watch videos", {"p15"}),
    ("a healthy snack", {"p12", "p11"}),
    ("something relaxing to drink before bed", {"p10"}),
    ("my hands are dry", {"p19"}),
    ("make the room smell nice", {"p17"}),
    ("bag for groceries", {"p16"}),
    ("cup for my morning coffee", {"p07"}),
    ("chop vegetables safely", {"p09"}),
    ("plan my week, I need big text", {"p03"}),
    ("protect my face on the bus", {"p20"}),
    ("listen to podcasts wirelessly", {"p14"}),
]


def run(name, fn):
    top1 = top3 = 0
    times, misses = [], []
    for query, right in TESTS:
        t0 = time.time()
        found, method = fn(query)
        times.append((time.time() - t0) * 1000)
        ids = [p["id"] for p in found]
        if ids[:1] and ids[0] in right:
            top1 += 1
        if right & set(ids[:3]):
            top3 += 1
        else:
            misses.append((query, [catalog.get(i)["name"] for i in ids[:3]] or ["nothing"]))
    n = len(TESTS)
    print("\n== %s ==" % name)
    print("Right product first:     %d of %d (%d%%)" % (top1, n, round(100 * top1 / n)))
    print("Right product in top 3:  %d of %d (%d%%)" % (top3, n, round(100 * top3 / n)))
    print("Search time: median %.0f ms, slowest %.0f ms" % (statistics.median(times), max(times)))
    if misses:
        print("Missed:")
        for q, got in misses:
            print("  %-40s -> %s" % (repr(q), ", ".join(got)))
    return {"top1": top1, "top3": top3, "n": n, "median_ms": round(statistics.median(times)),
            "max_ms": round(max(times)), "misses": [q for q, _ in misses]}


stale = search.load()
if stale:
    print("Embedding %d products first..." % len(stale))
    search.refresh(stale, save=True)

keyword = run("Keyword search (old)", lambda q: search.keyword_only(q, None, 3))
meaning = run("Meaning search (embeddings, %s)" % search.EMBED_MODEL, lambda q: search.search(q, None, 3))
cached = run("Meaning search, repeated (cached)", lambda q: search.search(q, None, 3))

with open("eval_results.json", "w") as f:
    json.dump({"model": search.EMBED_MODEL, "dims": search.EMBED_DIMS, "tests": len(TESTS),
               "keyword": keyword, "meaning": meaning, "meaning_cached": cached}, f, indent=2)
print("\nSaved eval_results.json")
