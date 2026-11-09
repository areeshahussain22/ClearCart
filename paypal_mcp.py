"""PayPal's MCP agent tools, kept running in the background.

Starting the PayPal MCP server takes a few seconds, so we start it once and
reuse it. One background task owns the connection; requests are sent to it
through a queue. The server is restarted before the access token expires.
"""

import asyncio
import json
import logging
import os
import shutil
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import paypal_api

log = logging.getLogger("clearcart.mcp")

CALL_TIMEOUT = float(os.environ.get("MCP_CALL_TIMEOUT", "25"))


def _server_params():
    override = os.environ.get("MCP_TEST_COMMAND")  # only for local testing with a fake server
    env = dict(os.environ)
    env["PAYPAL_ENVIRONMENT"] = env.get("PAYPAL_ENVIRONMENT", "SANDBOX")
    if override:
        parts = override.split()
        return StdioServerParameters(command=parts[0], args=parts[1:], env=env)
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if not npx:
        raise RuntimeError("npx not found. Install Node.js 18 or newer.")
    token = paypal_api.access_token()
    return StdioServerParameters(
        command=npx,
        args=["-y", "@paypal/mcp", "--tools=all", "--access-token=" + token],
        env=env,
    )


class PayPalMCP:
    def __init__(self):
        self._queue = None
        self._worker = None
        self.ready = False
        self.last_error = None

    def start(self):
        if self._worker is None:
            self._queue = asyncio.Queue()
            self._worker = asyncio.create_task(self._run())

    async def stop(self):
        if self._worker:
            self._worker.cancel()
            try:
                # Don't let a stuck MCP process block the app from shutting down.
                await asyncio.wait_for(asyncio.shield(self._worker), timeout=5)
            except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
                pass
            self._worker = None

    async def call(self, tool, args):
        """Call one PayPal MCP tool. Returns the parsed JSON result (or raw text)."""
        self.start()
        fut = asyncio.get_running_loop().create_future()
        await self._queue.put((tool, args, fut))
        return await asyncio.wait_for(fut, timeout=CALL_TIMEOUT + 30)

    async def _run(self):
        while True:
            try:
                params = _server_params()
                restart_at = paypal_api.token_expires_at() - 600 if not os.environ.get("MCP_TEST_COMMAND") else float("inf")
                async with stdio_client(params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        self.ready = True
                        self.last_error = None
                        log.info("PayPal MCP server ready")
                        while time.time() < restart_at:
                            try:
                                tool, args, fut = await asyncio.wait_for(self._queue.get(), timeout=60)
                            except asyncio.TimeoutError:
                                continue
                            if fut.done():
                                continue
                            try:
                                r = await asyncio.wait_for(session.call_tool(tool, args), timeout=CALL_TIMEOUT)
                                fut.set_result(_parse(r))
                            except Exception as e:  # pass the error to the caller, keep serving
                                if not fut.done():
                                    fut.set_exception(e)
                log.info("Restarting PayPal MCP server (token refresh)")
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.ready = False
                self.last_error = repr(e)
                log.warning("PayPal MCP server failed: %r", e)
                # Fail any waiting calls quickly so the app can fall back.
                while self._queue and not self._queue.empty():
                    _, _, fut = self._queue.get_nowait()
                    if not fut.done():
                        fut.set_exception(RuntimeError("PayPal MCP unavailable: %r" % e))
                await asyncio.sleep(5)


class ToolError(Exception):
    pass


def _parse(result):
    text = "\n".join(getattr(c, "text", None) or "" for c in result.content).strip()
    if getattr(result, "isError", False) or getattr(result, "is_error", False):
        raise ToolError(text[:500])
    try:
        data = json.loads(text)
    except ValueError:
        return text
    if isinstance(data, dict) and data.get("ok") is False:
        raise ToolError(text[:500])
    return data


mcp_client = PayPalMCP()
