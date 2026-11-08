from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ClearCart</title></head>
<body><main><h1>ClearCart</h1><p>Deploy test: it works.</p></main></body></html>"""


@app.get("/health")
def health():
    return {"ok": True}
