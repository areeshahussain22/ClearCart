# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Blind and low-vision shoppers first: screen reader and screen magnifier users, plus people who prefer voice or keyboard over a mouse. They want to find a product, pay, check or track an order, and ask for a refund without fighting a visual-first checkout.

The immediate audience for this build is PayPal hackathon judges watching a live walkthrough or video and possibly trying the app themselves.

## Product Purpose
ClearCart is an accessible voice and keyboard shopping assistant for PayPal stores. The shopper links PayPal once, sets a 4-digit PIN and a per-purchase spending limit, then shops by talking or typing to an AI assistant. Success for the hackathon is a demo that shows a blind shopper can buy, track and refund safely, and that the experience feels considered rather than bolted on.

## Positioning
The AI can only prepare a payment or refund; code checks the PIN, the limit and the price before any money moves. The PIN is always typed, never spoken, and voice can never confirm a payment. Read-backs before paying are written by code from the store's prices, and receipts are read back from PayPal itself.

## Operating Context
- Runs on the PayPal sandbox only. No real money moves.
- Demo store of 20 made-up products priced in GBP (catalog.py).
- Two paths: the AI assistant (chat log with optional voice in/out) and a plain store page (keyboard path) that uses the same PIN and limit.
- Voice input works in Chrome and Edge only; other browsers type.
- Hosted on Render's free plan; first load after idle can take about a minute.

## Capabilities and Constraints
- FastAPI app; HTML is server-rendered strings in pages.py, styles in static/style.css, assistant behaviour in static/app.js. No front-end framework or build step.
- Pages must work without JavaScript except the assistant page.
- Flows: welcome, link PayPal (on PayPal's own page), set PIN and limit, assistant, store, check-your-order, receipt, error.
- 3 wrong PINs lock payments and refunds for 5 minutes; the app auto-locks after 5 minutes idle.
- Shopper settings live in an encrypted browser cookie, not a database.

## Brand Commitments
- Name: ClearCart. Voice is plain, short, literal British English ("Nothing has been charged yet.").
- Must say clearly it is a demo on the PayPal sandbox with no real money.
- PayPal is the payment provider named in copy; no PayPal logo assets are in the repo.

## Evidence on Hand
- Product data: catalog.py (names, prices, ratings, descriptions, categories). No product images exist; do not invent them.
- No testimonials, users, metrics or press. Do not fabricate any.

## Product Principles
1. Nothing moves money without a typed PIN, and the screen always says what will happen before it happens.
2. Every step is fully usable by screen reader, keyboard and voice alone; sight is never required.
3. Say it plainly: amounts are written in words for speech, states are announced, nothing is implied by colour or position alone.
4. Calm and trustworthy over flashy; the shopper should always know where they are and what was charged.

## Accessibility & Inclusion
Target WCAG 2.2 AAA where possible: 7:1 text contrast, large targets, large default text, visible focus, reduced-motion respect, live regions for chat and status, sensible heading order and landmarks. Must hold up at 200–400% zoom and under Windows High Contrast / forced colours.
