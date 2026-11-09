#!/usr/bin/env python3
"""Find out why Gemini is slow or failing. Run it in your clearcart-day3 folder:

    python gemini_check.py

It reads GEMINI_API_KEY from your .env file. It never prints the key.
"""

import os
import sys
import time

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

KEY = os.environ.get("GEMINI_API_KEY")
if not KEY:
    print("GEMINI_API_KEY is not set in .env")
    sys.exit(1)

BASE = "https://generativelanguage.googleapis.com/v1beta"
HEAD = {"x-goog-api-key": KEY, "Content-Type": "application/json"}

try:
    import agent
    TOOLS = agent.TOOLS
    SYSTEM = agent.SYSTEM_PROMPT
except Exception:
    TOOLS, SYSTEM = None, "You are a shopping assistant."


def timed(label, fn):
    t0 = time.time()
    try:
        r = fn()
        secs = time.time() - t0
        if r.status_code == 200:
            print("%-48s OK      %5.1f s" % (label, secs))
        else:
            print("%-48s HTTP %s %5.1f s  %s" % (label, r.status_code, secs, r.text[:200].replace("\n", " ")))
        return r
    except requests.exceptions.Timeout:
        print("%-48s TIMEOUT after %.0f s" % (label, time.time() - t0))
    except Exception as e:
        print("%-48s ERROR   %s" % (label, repr(e)[:200]))


print("1. Does the key work, and which flash models can it see?")
r = timed("   list models", lambda: requests.get(BASE + "/models?pageSize=200", headers=HEAD, timeout=30))
if r is not None and r.status_code == 200:
    names = [m["name"].split("/")[-1] for m in r.json().get("models", [])]
    flash = [n for n in names if "flash" in n]
    print("   flash models visible:", ", ".join(flash) or "none")

for model in ["gemini-3.8-flash", "gemini-3.5-flash-lite"]:
    url = "%s/models/%s:generateContent" % (BASE, model)
    print("\n2. %s: tiny message, no tools" % model)
    timed("   'Say hi'", lambda: requests.post(url, headers=HEAD, timeout=60, json={
        "contents": [{"role": "user", "parts": [{"text": "Say hi in 3 words."}]}]}))
    if TOOLS:
        print("3. %s: our real request (rules + tools)" % model)
        timed("   'I need a notebook under 5 pounds'", lambda: requests.post(url, headers=HEAD, timeout=60, json={
            "systemInstruction": {"parts": [{"text": SYSTEM}]},
            "contents": [{"role": "user", "parts": [{"text": "I need a notebook under 5 pounds"}]}],
            "tools": [{"functionDeclarations": TOOLS}],
            "generationConfig": {"temperature": 0.3}}))
