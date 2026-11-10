# ClearCart

An accessible voice and keyboard shopping assistant for PayPal stores.
Find, pay, track and return, all through PayPal. **Work in progress.**

Runs on the **PayPal sandbox only**. No real money moves.

## What it does

- **AI assistant** (Gemini, with Groq as a backup): type or talk (voice works in Chrome and Edge).
  Ask for products ("a notebook under 5 pounds"), buy, check an order, track it, see your orders, ask for a refund.
- **Link PayPal once** on PayPal's own page (PayPal Vault / saved payment method).
- **4-digit PIN** for every payment and refund. Typed, never spoken. Voice can never confirm a payment.
- **Spending limit** per purchase, set by the shopper.
- **3 wrong PINs** lock payments and refunds for 5 minutes. The app **auto-locks** after 5 minutes idle.
- The AI can only *prepare* a payment or refund. Code checks the PIN, the limit and the price, then moves money.
- Read-backs before paying are written by code from the store's prices; receipts come from PayPal.
- A plain store page (keyboard path) that uses the same PIN and limit.

## PayPal features used

| Step | PayPal feature |
|---|---|
| Link account once | Payment Method Tokens API (setup token, then payment token) |
| Pay | Orders API v2 with `payment_source.paypal.vault_id` |
| Receipt, "did it go through?" | PayPal MCP tool `get_order` |
| Store ships the item | PayPal MCP tool `create_shipment_tracking` |
| "Where's my order?" | PayPal MCP tool `get_shipment_tracking` |
| Refund | PayPal MCP tool `create_refund` |

## Run it on your computer

You need **Python 3.10+** and **Node.js 18+** (Node runs PayPal's MCP server).

1. Get PayPal **sandbox** keys: developer.paypal.com > Apps & Credentials (Sandbox) > your app.
   In the app settings, turn on **Vault** under Advanced options.
2. Get a free Gemini API key at aistudio.google.com (optional backup: a Groq key).
3. Copy `.env.example` to `.env` and fill in `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`,
   `GEMINI_API_KEY` and any long random text for `SESSION_SECRET`.
4. Install and run:

```
pip install -r requirements.txt
uvicorn app:app --reload
```

5. Open http://127.0.0.1:8000, click **Link PayPal**, log in with your **sandbox personal (buyer)**
   account, approve, choose a PIN and limit, then ask the assistant for something.

## For judges

- Hosted demo: https://clearcart-tko8.onrender.com
  (free hosting: the first load can take up to a minute while it wakes up)
- A sandbox buyer login for "Link PayPal" is in our Devpost submission.
- Voice input works in Chrome and Edge. Typing works in any browser.

## Deploy (Render, Docker)

Use the included `Dockerfile` (it has both Python and Node).
On Render: New > Web Service > this repo > Language **Docker**.
Add environment variables: `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `SESSION_SECRET`, `GEMINI_API_KEY` (and optionally `GROQ_API_KEY`).
On Render's free plan the app sleeps when idle, so the first load can take about a minute.

## Limits

- Sandbox only. Live use of saved PayPal accounts needs approval from PayPal and
  PayPal's risk data collection, which this demo does not include.
- Shopper settings (linked account, PIN hash, limit, recent orders) are kept in an encrypted browser cookie, not a database.
  Because of that, the wrong-PIN counter could be reset by replaying an old cookie; a real deployment would keep it on the server.
- Order history covers orders made in the current browser session.
- Tracking numbers are added by the demo store itself.
- Gemini's free tier may use prompts to improve Google products; don't type real personal details.
