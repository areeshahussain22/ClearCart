# ClearCart

An accessible voice and keyboard shopping assistant for PayPal stores.
Find, pay, track and return, all through PayPal. **Work in progress.**

Runs on the **PayPal sandbox only**. No real money moves.

## What works so far (Day 2)

- Demo store with 20 made-up products (prices in GBP).
- **Link PayPal once** on PayPal's own page (PayPal Vault / saved payment method).
- **Pay with the saved account**, with no PayPal pop-up each time.
- A check-your-order page that says "Nothing has been charged yet" before paying.
- A price recheck: if the price changed, payment stops.
- A **receipt read back from PayPal** using PayPal's MCP agent tool `get_order`
  (falls back to PayPal's REST API if the MCP server is unavailable).

## PayPal features used

| Step | PayPal feature |
|---|---|
| Link account once | Payment Method Tokens API (setup token, then payment token) |
| Pay | Orders API v2 with `payment_source.paypal.vault_id` |
| Receipt | PayPal MCP server (`@paypal/mcp`), tool `get_order` |

## Run it on your computer

You need **Python 3.10+** and **Node.js 18+** (Node runs PayPal's MCP server).

1. Get PayPal **sandbox** keys: developer.paypal.com > Apps & Credentials (Sandbox) > your app.
   In the app settings, turn on **Vault** under Advanced options.
2. Copy `.env.example` to `.env` and fill in `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`
   and any long random text for `SESSION_SECRET`.
3. Install and run:

```
pip install -r requirements.txt
uvicorn app:app --reload
```

4. Open http://127.0.0.1:8000, click **Link PayPal**, log in with your **sandbox personal (buyer)**
   account, approve, then buy something.

## Deploy (Render, Docker)

Use the included `Dockerfile` (it has both Python and Node).
On Render: New > Web Service > this repo > Language **Docker**.
Add environment variables: `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `SESSION_SECRET`.
On Render's free plan the app sleeps when idle, so the first load can take about a minute.

## Limits

- Sandbox only. Live use of saved PayPal accounts needs approval from PayPal and
  PayPal's risk data collection, which this demo does not include.
- The saved account is kept in a signed browser cookie for the demo, not in a database.
