# Python app + Node.js (PayPal's MCP server runs on Node).
FROM node:22-bookworm-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PayPal's MCP server ahead of time so it doesn't download on first use.
RUN npm install --omit=dev @paypal/mcp@1.8.1

COPY requirements.txt .
RUN python3 -m venv /venv && /venv/bin/pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PATH="/app/node_modules/.bin:/venv/bin:$PATH" \
    PAYPAL_ENVIRONMENT=SANDBOX \
    HTTPS_ONLY=true

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
