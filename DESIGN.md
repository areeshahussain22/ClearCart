---
name: ClearCart
description: A kawaii sticker sheet for safe voice and keyboard shopping, with Basket the mascot keeping you company.
colors:
  plum-ink: "#2b1a2e"
  plum-soft: "#5a4560"
  strawberry: "#ffc4dd"
  bubblegum: "#ff6fae"
  bubblegum-hover: "#ff8cbf"
  mint: "#bdf0da"
  butter: "#ffe89a"
  sky: "#c7e3ff"
  lilac: "#e3d4ff"
  peach: "#ffd3bd"
  blush-ground: "#fff3f8"
  sticker-white: "#ffffff"
  ok-green: "#0a5e36"
  stop-crimson: "#9e1239"
  night-ground: "#1d1320"
  night-surface: "#2a1d2e"
  night-ink: "#fff2f8"
  night-ink-soft: "#e6d3ea"
  night-ok: "#8ff0bd"
  night-stop: "#ffa3c0"
typography:
  display:
    fontFamily: "Fredoka, Atkinson Hyperlegible, system-ui, sans-serif"
    fontSize: "clamp(2.4rem, 1.7rem + 2.6vw, 3.75rem)"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.015em"
  headline:
    fontFamily: "Fredoka, Atkinson Hyperlegible, system-ui, sans-serif"
    fontSize: "2rem"
    fontWeight: 700
    lineHeight: 1.15
  title:
    fontFamily: "Fredoka, Atkinson Hyperlegible, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.15
  body-large:
    fontFamily: "Atkinson Hyperlegible, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 400
    lineHeight: 1.45
  body:
    fontFamily: "Atkinson Hyperlegible, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Atkinson Hyperlegible, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 700
    lineHeight: 1.3
  button:
    fontFamily: "Fredoka, Atkinson Hyperlegible, system-ui, sans-serif"
    fontSize: "1.3rem"
    fontWeight: 600
    lineHeight: 1.1
rounded:
  sm: "14px"
  md: "22px"
  lg: "32px"
  pill: "999px"
spacing:
  xs: "0.6rem"
  sm: "1rem"
  md: "1.5rem"
  lg: "1.75rem"
  xl: "2.75rem"
components:
  button-primary:
    backgroundColor: "{colors.bubblegum}"
    textColor: "{colors.plum-ink}"
    typography: "{typography.button}"
    rounded: "{rounded.pill}"
    padding: "0.55rem 1.7rem"
    height: "56px"
  button-primary-hover:
    backgroundColor: "{colors.bubblegum-hover}"
  button-secondary:
    backgroundColor: "{colors.sticker-white}"
    textColor: "{colors.plum-ink}"
    rounded: "{rounded.pill}"
    padding: "0.55rem 1.7rem"
    height: "56px"
  button-secondary-hover:
    backgroundColor: "{colors.sky}"
  button-pressed:
    backgroundColor: "{colors.mint}"
  button-danger:
    backgroundColor: "{colors.sticker-white}"
    textColor: "{colors.stop-crimson}"
    rounded: "{rounded.pill}"
    height: "56px"
  input-text:
    backgroundColor: "{colors.sticker-white}"
    textColor: "{colors.plum-ink}"
    rounded: "{rounded.pill}"
    padding: "0.5rem 1.25rem"
    height: "58px"
  pin-cell:
    backgroundColor: "{colors.sticker-white}"
    rounded: "{rounded.pill}"
    size: "4rem"
  pay-sticker:
    backgroundColor: "{colors.butter}"
    textColor: "{colors.plum-ink}"
    rounded: "{rounded.lg}"
    padding: "1.75rem 2rem 2rem"
  message-assistant:
    backgroundColor: "{colors.mint}"
    textColor: "{colors.plum-ink}"
    typography: "{typography.body-large}"
    rounded: "{rounded.md}"
    padding: "0.75rem 1.2rem 0.95rem"
  message-you:
    backgroundColor: "{colors.butter}"
    textColor: "{colors.plum-ink}"
    rounded: "{rounded.md}"
  tag:
    backgroundColor: "{colors.butter}"
    textColor: "{colors.plum-ink}"
    typography: "{typography.title}"
    rounded: "{rounded.pill}"
    padding: "0.25rem 1.1rem"
  chip:
    backgroundColor: "{colors.sticker-white}"
    textColor: "{colors.plum-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0.3rem 1rem"
  nav-link:
    textColor: "{colors.plum-ink}"
    rounded: "{rounded.pill}"
    padding: "0 1.4rem"
    height: "52px"
  nav-link-current:
    backgroundColor: "{colors.sticker-white}"
    textColor: "{colors.plum-ink}"
---

# Design System: ClearCart

## Overview

**Creative North Star: "The Kawaii Sticker Sheet"**

ClearCart is a sheet of candy stickers peeled onto a pale pink dotted page. Every container is a sticker: a pastel or white shape with a thick plum outline, a white die-cut ring, a second plum edge and a soft lift. Headings are chunky, rounded Fredoka; reading text is Atkinson Hyperlegible, set large. Basket, a small pink shopping basket with a face, keeps the shopper company and changes expression with the app's state.

The cuteness is never paid for in legibility. The candy pastels (strawberry, butter, mint, sky, lilac, peach) carry plum ink at 11:1 or better, the body size is 1.25rem, targets are 52–58px tall, and the focus ring is a 4px plum outline with a 9px bubblegum band that shows up on every candy colour. Basket is decorative (`aria-hidden`); every mood it shows is also said in text. Under forced colours the sticker rings drop away and the system falls back to borders.

Density is low and friendly: generous gaps, one job per sticker, and the single payment waiting for a PIN shown as the brightest sticker on the screen. The previous "Embossed Label" world was rejected by the user and is not to be revived.

**Key Characteristics:**
- Plum (#2b1a2e) outlines and plum text on every pastel, in light and dark mode alike.
- Sticker edge: 3px plum border, 5px white ring, 8px plum ring, soft plum lift.
- Pills everywhere small (buttons, inputs, chips, tags, nav); 22–32px corners on cards.
- Fredoka display, Atkinson Hyperlegible body, tabular numerals throughout.
- Basket the mascot reacts to state; motion is springy and only runs when reduced motion is not requested.

## Colors

A candy pastel set on a blush dotted ground, held together by one plum ink.

### Primary
- **Bubblegum** (`bubblegum`): primary button fill, filled PIN bubbles, the limit bar's fill, the current step's number badge, link hover underline, selection, and the focus band. Primary buttons fill with the lighter **Bubblegum Hover** (`bubblegum-hover`, #ff8cbf, 7.6:1 with plum) and lighten to #ffa8cf on hover (9.1:1); full bubblegum (6.3:1) never carries text.
- **Strawberry** (`strawberry`): the site header band, Basket's body, the "stop" tag, and the PIN bubble waiting for input on the pay sticker.

### Secondary
- **Butter** (`butter`): the pay sticker, "You" chat messages, the default tag, prices, the notice, the current setup step, and the empty PIN bubble waiting for input (off-sticker).
- **Mint** (`mint`): ClearCart's chat messages, completed steps, OK tags, pressed toggle buttons (Talk).

### Tertiary
- **Lilac** (`lilac`): information panels (safety facts, hints) and the unlock sticker.
- **Sky** (`sky`) and **Peach** (`peach`): store aisle tags (with the rest of the candy set, cycling in a fixed order of strawberry, mint, butter, sky, lilac, peach) and secondary-button hover.

### Neutral
- **Plum Ink** (`plum-ink`): all text on pastels and white stickers, every outline, Basket's features. Never changes with the colour scheme.
- **Plum Soft** (`plum-soft`): secondary text (lead paragraphs, product descriptions, muted notes); 8.5:1 on white.
- **Blush Ground** (`blush-ground`): page ground, overlaid with a 28px dot grid of bubblegum at 22% opacity.
- **Sticker White** (`sticker-white`): the chat log, product list, receipts, read-back card, the die-cut ring.
- **OK Green** (`ok-green`) and **Stop Crimson** (`stop-crimson`): status text and the danger button's text and border.
- **Night** set (`night-ground`, `night-surface`, `night-ink`, `night-ink-soft`, `night-ok`, `night-stop`): dark mode replaces only ground, surface, text-on-ground, status and focus colours; the dot grid stays.

### Named Rules
**The Plum On Candy Rule.** Any pastel or white sticker carries plum ink (#2b1a2e) text, in light and dark mode. Never put light text on a pastel, and never let a sticker's text colour follow the colour scheme.

**The Pink Header Rule.** The header stays strawberry with plum ink in both schemes; it is the one fixed band of the sheet.

## Typography

**Display Font:** Fredoka (variable 300–700, self-hosted; falls back to Atkinson Hyperlegible, then system-ui)
**Body Font:** Atkinson Hyperlegible (400 and 700, self-hosted; falls back to system-ui)

**Character:** Fredoka's round terminals give the headings their soft, toy-like voice; Atkinson Hyperlegible keeps every letter distinct for low-vision readers. Numerals are tabular everywhere so amounts line up and do not jitter.

### Hierarchy
- **Display** (Fredoka 700, clamp 2.4–3.75rem, 1.15, -0.015em): page h1 only; balanced wrapping.
- **Headline** (Fredoka 700, 2rem, 1.15): section h2 and the pay sticker's "Pay £x" title.
- **Title** (Fredoka 600, 1.5rem): h3, product names, tags, the price pill.
- **Body Large** (Atkinson 400, 1.5rem, 1.45–1.5): lead paragraphs, chat messages (max 46ch), the payment read-back.
- **Body** (Atkinson 400, 1.25rem, 1.6): everything else; paragraphs capped at 66ch.
- **Label** (Atkinson 700, 1.0625rem): chips, the sandbox pill; form labels use body size at 700.
- **Button** (Fredoka 600, 1.3rem, 1.1): buttons and nav links (nav at 1.25rem).

### Named Rules
**The Two Voices Rule.** Fredoka speaks in headings, buttons, prices and speaker names; Atkinson Hyperlegible carries every sentence a shopper must read. Never set running text in Fredoka.

**The Big Small Text Rule.** The smallest text on the sheet is 1.0625rem. Nothing goes smaller.

## Layout

A centred 82rem frame with 1.5rem side padding; non-wide pages hold content to 54rem. Two-column pages (welcome, setup, check) use a fluid main column beside a 28rem side sticker with a 3–4rem gap. The assistant desk pairs the conversation with a 30rem sticky side column (top 3rem) holding the pay sticker or hints.

Spacing runs on rem steps: 0.6–1rem inside clusters, 1.25–1.75rem between stickers and inside them, 2.5–2.75rem between sections.

At 60rem and below, columns stack; when a payment is waiting the side column moves above the conversation so the pay sticker comes first. At 36rem the nav fills the width with equal pills, the main padding drops to 1rem, the read-back drops to body size, PIN bubbles shrink to 3.4rem, and Basket shrinks.

## Elevation & Depth

Depth comes from the sticker edge, not from layered surfaces. Large stickers wear a stacked ring: the plum border, then a crisp white die-cut ring, then a plum outer ring, then a soft blurred lift. Buttons are puffy rather than lifted: a short soft drop and an inner bottom shade. Everything else is flat and outlined.

### Shadow Vocabulary
- **Sticker edge** (`box-shadow: 0 0 0 5px #fff, 0 0 0 8px #2b1a2e, 0 6px 16px rgba(43,26,46,0.16)`): chat log, pay sticker, info panels, product list, receipt sheet, notice. Dark mode lift is `0 6px 18px rgba(0,0,0,0.45)`.
- **Puffy button** (`box-shadow: 0 6px 10px -4px rgba(43,26,46,0.55), inset 0 -4px 0 rgba(43,26,46,0.18)`): every button.
- **Focus band** (`outline: 4px solid plum; outline-offset: 3px; box-shadow: 0 0 0 9px #ff6fae`): every focusable element; outline turns night ink in dark mode except on stickers and the header.

### Named Rules
**The Die-Cut Rule.** A sticker is a whole container (log, panel, list, sheet, notice, pay sticker). Messages, chips and list items inside a sticker get a 2px plum border only, never the full ring.

## Shapes

Round all the way down. Small controls are full pills (999px): buttons, inputs, chips, tags, nav links, the step stickers, the limit bar. Messages and inner cards use 22px; large stickers use 32px; code blocks and the skip link use 14px. PIN cells and number badges are true circles. Borders are plum: 3px on stickers, buttons and inputs, 2px on things nested inside a sticker. The one dashed line is the divider between products and the waiting PIN bubble.

## Components

### Buttons
Puffy candy pills that bounce a little.
- **Shape:** full pill, 3px plum border, 56px tall (small variant 50px).
- **Primary:** bubblegum fill, plum text, Fredoka 600.
- **Hover / Active:** fill lightens; lifts 2px and scales 1.02 on a springy curve (140ms, `cubic-bezier(0.34,1.56,0.64,1)`); presses down 2px and to 0.98.
- **Secondary:** white fill, sky on hover. **Pressed toggle** (Talk while listening): mint. **Danger** (Unlink): white with crimson text and border.
- **Disabled:** 55% opacity, no motion.

### Chips
- **Style:** white pill, 2px border in text colour, label size; carries account facts ("PayPal linked", "Limit").

### Tags
- **Style:** Fredoka 600 pill in a candy colour with a 3px plum border. Used as the visible heading of store aisles and the welcome "Get started" heading, and as order status (mint = OK, strawberry = stop).

### Cards / Containers
- **Corner Style:** 32px.
- **Background:** white (log, products, receipt), lilac (facts, hints, unlock), butter (pay sticker, notice).
- **Shadow Strategy:** sticker edge (see Elevation).
- **Internal Padding:** 1.5–2rem.

### Inputs / Fields
- **Style:** pill, 58px tall, 3px border in the text colour, surface fill; plum caret. Checkboxes are 1.7rem with bubblegum accent.
- **Focus:** the shared plum outline and bubblegum band.

### Navigation
- **Style:** Fredoka 600 pills in the strawberry header, 52px tall, transparent border at rest; hover adds a plum border and half-white fill; the current page is a white pill with plum border. Full-width equal pills on small screens.

### PIN Bubbles
Four candy circles (4rem) drawn over a real password input, which stays focusable and readable. The bubble waiting for the next digit turns butter (strawberry on the pay sticker) with a dashed border; each digit typed pops a bubblegum candy with a white shine into its bubble (260ms springy scale). The whole row takes the focus ring.

### Pay Sticker
The one thing waiting for a PIN: a butter sticker with a Fredoka headline ("Pay £4.50"), the read-back in a white inner card, the candy limit bar, the PIN bubbles and Pay / Cancel. Basket peeks over its top-right corner. It pops in (420ms, scale 0.94 and -1° to rest).

### Chat Messages
Stickers inside the white log: mint for ClearCart, butter for You, 22px corners, 2px plum border, Body Large text, speaker name in Fredoka 700.

### Basket the Mascot
An inline SVG basket: strawberry body, plum outlines and eyes with white shines, bubblegum blush. The page's `data-mood` swaps its face: idle (open eyes, smile), thinking (open mouth, blinking thought dots), listening (open mouth, gentle sway), excited and happy (closed happy eyes, two hops), worried (wobbly mouth), sleepy (closed eyes). Sizes: 3.25rem in the brand, 5.5rem beside the chat, 8.5rem on welcome, 5rem peeking over the pay sticker.

### Setup Steps
Round white step pills with a circular number badge: mint when done, butter with a bubblegum badge when current, regular weight when still to do.

## Do's and Don'ts

### Do:
- **Do** outline every sticker in plum and give whole containers the full die-cut ring (5px white, 8px plum, soft lift).
- **Do** put plum ink (#2b1a2e) on every pastel and white sticker, in both colour schemes.
- **Do** pick fills from the candy set (strawberry, bubblegum, butter, mint, sky, lilac, peach); no other hues.
- **Do** say in text whatever Basket's face shows, and keep Basket `aria-hidden`.
- **Do** keep targets at 52px or taller, text at 1.0625rem or larger, and the plum-and-bubblegum focus ring on everything focusable.
- **Do** wrap springy motion (`cubic-bezier(0.34,1.56,0.64,1)`) in `prefers-reduced-motion: no-preference`, and drop the sticker rings under forced colours.

### Don't:
- **Don't** put light text on a pastel, or let sticker text flip with dark mode.
- **Don't** use square corners; small controls are pills, containers are 22–32px.
- **Don't** set running text in Fredoka.
- **Don't** make Basket the only signal of a state.
- **Don't** add product images; none exist.
- **Don't** bring back the rejected "Embossed Label" look.
