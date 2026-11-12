# ClearCart

An accessible voice and keyboard shopping assistant for PayPal stores, built for blind and low-vision shoppers.
Find, pay, track and return, all through PayPal.

Runs on the **PayPal sandbox only**. No real money moves.

**Live demo:** https://clearcart-tko8.onrender.com
(free hosting: the first load can take up to a minute while it wakes up)

## Why we built it

Studies of voice shopping assistants for blind shoppers found that users liked them, but wanted extra checks and were nervous about trusting an AI with money. Those studies stopped before the payment step. ClearCart covers the whole journey, including paying and refunds, with safety rules built into the code.

## What it does

- **Works with screen readers and keyboards.** Every page is labelled and can be used without a mouse.
- **Talk or type.** Voice works in Chrome and Edge. Typing works in any browser.
- **Chat with an AI agent** (Gemini, with Groq as a backup). Ask for products, buy, check an order, track it, see your orders and ask for a refund.
- **Link PayPal once** on PayPal's own page (PayPal Vault). After that, pay from the chat with no pop-ups.
- **A plain store page** (keyboard path) that uses the same PIN and limit.

## Safety

- A **4-digit PIN** for every payment and refund. Typed, never spoken. Voice can never confirm a payment.
- A **spending limit** per purchase, set by the shopper.
- **3 wrong PINs** lock payments and refunds for 5 minutes. The app **auto-locks** after 5 minutes idle.
- The AI can only *prepare* a payment or refund. Code checks the PIN, the limit and the price, then moves money.
- Read-backs before paying are written by code from the store's prices. Receipts come from PayPal.
- Voice is never used to prove who the shopper is.

## PayPal features used

| Step                  | PayPal feature                                              |
|---                    |---                                                          |
| Link account once     | Payment Method Tokens API (setup token, then payment token) |
| Pay                   | Orders API v2 with `payment_source.paypal.vault_id`         |
| Receipt               | PayPal MCP tool `get_order`                                 |
| Store ships the item  | PayPal MCP tool `create_shipment_tracking`                  |
| "Where's my order?"   | PayPal MCP tool `get_shipment_tracking`                     |
| Refund                | PayPal MCP tool `create_refund`                             |

## Results

**Accessibility:** axe DevTools found zero issues on every page. We also tested with keyboard only and with the NVDA screen reader.

## Tech stack

- Python, FastAPI, Uvicorn
- PayPal Orders API, PayPal Vault, PayPal MCP server (`@paypal/mcp`, runs on Node.js)
- Google Gemini (chat and `gemini-embedding-001`), Groq as a backup
- Browser Web Speech API for voice
- HTML, CSS, JavaScript
- Docker, deployed on Render

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

### Optional settings (`.env`)

| Variable           | What it does                                                      |
|---                 |---                                                                |
| `GROQ_API_KEY`     | Backup AI if Gemini is slow or fails                              |
| `GEMINI_MODEL`     | Gemini chat model (default `gemini-3.5-flash-lite`)               |
| `GROQ_MODEL`       | Groq model (default `openai/gpt-oss-120b`)                        |
| `PUBLIC_BASE_URL`  | Set on a host if PayPal's return link points to the wrong address |
| `HTTPS_ONLY`       | Set to `true` when hosted on https |

## Smart product search (embeddings)

- Each product's text is turned into an embedding **once** with Gemini (`gemini-embedding-001`, 768 numbers)
  and saved in `product_embeddings.json`. The app loads it at startup, so there are no embedding calls then.
- Only new or changed products are re-embedded (each product's text has a fingerprint).
- **Retrieve first:** for a shopping message, code finds the 8 closest products by meaning (price limits applied by
  code) and sends them with the message, so the AI answers in one call.
- **Direct replies:** for buying, refunds, tracking and order status, the reply is written by code from PayPal's
  result, so no second AI call is needed.
- If the embedding service is down, search falls back to keywords.
- Scaling path for big stores: the same design with a vector database (for example Postgres + pgvector).

Scripts:
- `python build_embeddings.py` creates or updates `product_embeddings.json` (run it after changing products).
- `python eval_search.py` compares keyword search with meaning search and saves `eval_results.json`.

## Project files

| File                 | What it does                                                     |
|---                   |---                                                               |
| `app.py`             | Web server and routes                                            |
| `agent.py`           | The AI agent (Gemini, Groq backup)                               |
| `actions.py`         | Buying, refunds, tracking and order checks, with the safety rules|
| `account.py`         | Linked account, PIN, limit and lock                              |
| `paypal_api.py`      | PayPal Vault and Orders API calls                                |
| `paypal_mcp.py`      | Connects to PayPal's MCP server                                  |
| `search.py`          | Meaning-based product search                                     |
| `catalog.py`         | The demo store's products                                        |
| `pages.py`, `static/`| Pages, styles, scripts and fonts                                 |

## For judges

- Hosted demo: https://clearcart-tko8.onrender.com
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
- Tested by us with NVDA and keyboard only, not yet with blind or low-vision users.
- Order history covers orders made in the current browser session.

## Team

- Areesha Hussain
- Sarah

## Credits

- Fonts: Atkinson Hyperlegible and Fredoka, under the SIL Open Font License.

## License

MIT, see `LICENSE`.
