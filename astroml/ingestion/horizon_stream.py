"""Async streaming client for Stellar Horizon transaction events."""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import ssl
from collections.abc import Callable
from typing import Any
from urllib.parse import urlencode, urlparse

Transaction = dict[str, Any]
TransactionHandler = Callable[[Transaction], Any]


class HorizonStreamError(RuntimeError):
    """Raised when the Horizon stream returns an invalid HTTP response."""


class HorizonStreamingClient:
    """Consume Horizon transaction events over Server-Sent Events (SSE).

    Reads the SSE wire format directly over an ``asyncio`` transport instead of
    going through the synchronous ``stellar-sdk`` client, so the caller's event
    loop is never blocked on a socket that Horizon may hold open indefinitely.

    Args:
        base_url: Horizon root, e.g. ``https://horizon.stellar.org``.
        endpoint: Resource to stream, appended to ``base_url``.
        cursor: Where to start. ``"now"`` skips history and delivers only
            transactions that arrive after connecting.
        reconnect_delay: First backoff wait after a failed connection, seconds.
        max_reconnect_delay: Ceiling for the exponentially growing backoff.
        logger: Logger for connection and reconnect notices. Defaults to this
            module's.

    Raises:
        ValueError: At construction, if ``base_url`` is not an http(s) URL with
            a hostname, or a reconnect delay is not positive.

    Example:
        .. code-block:: python

            import asyncio
            from astroml.ingestion import HorizonStreamingClient

            async def main() -> None:
                client = HorizonStreamingClient(cursor="now")

                async def on_transaction(tx: dict) -> None:
                    print(tx["hash"])

                await client.start(on_transaction)   # returns immediately
                await asyncio.sleep(30)
                await client.stop()                  # drains the task
                print("resumed from", client.cursor)

            asyncio.run(main())
    """

    def __init__(
        self,
        *,
        base_url: str = "https://horizon.stellar.org",
        endpoint: str = "/transactions",
        cursor: str = "now",
        reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 30.0,
        logger: logging.Logger | None = None,
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("base_url must use http or https")
        if not parsed.hostname:
            raise ValueError("base_url must include a hostname")
        if reconnect_delay <= 0 or max_reconnect_delay <= 0:
            raise ValueError("Reconnect delays must be positive")

        self._base_url = parsed
        self._endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        self._cursor = str(cursor)
        self._reconnect_delay = reconnect_delay
        self._max_reconnect_delay = max_reconnect_delay
        self._logger = logger or logging.getLogger(__name__)
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._writer: asyncio.StreamWriter | None = None

    @property
    def cursor(self) -> str:
        """Where the stream will resume, or has resumed to.

        Advances as transactions arrive (see :meth:`_handle_payload`), so
        reading it after :meth:`stop` gives the reconnect point.
        """
        return self._cursor

    async def start(self, on_transaction: TransactionHandler) -> None:
        """Begin consuming in a background task and return immediately.

        Args:
            on_transaction: Called per transaction with the parsed Horizon
                payload. May be a coroutine function; the awaitable is awaited.

        Raises:
            RuntimeError: If a stream is already running. Call
                :meth:`stop` first rather than starting a second consumer,
                which would advance ``cursor`` from two places at once.
        """
        if self._task and not self._task.done():
            raise RuntimeError("stream already running")
        self._stop_event.clear()
        self._task = asyncio.create_task(self.stream(on_transaction))

    async def stop(self) -> None:
        """Ask the stream to end and wait for its task to finish.

        Returns once consumption has actually stopped, so a caller can be
        sure no handler is still running — which is what makes it safe to
        read :attr:`cursor` immediately afterwards.

        Side effects: closes the open transport, which makes
        :meth:`_consume_stream` return, and clears the tracked task. Never
        raises: a transport that is already dead is the outcome we wanted.
        """
        self._stop_event.set()
        writer = self._writer
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:  # pragma: no cover - transport specific
                pass

        if self._task is not None:
            task = self._task
            self._task = None
            # Called from inside the stream task itself (a handler that
            # shuts down), awaiting our own task would deadlock forever.
            if task is not asyncio.current_task():
                await task

    async def stream(self, on_transaction: TransactionHandler) -> None:
        """Reconnect loop: keep consuming until :meth:`stop` is called.

        Exponential backoff restarts at ``reconnect_delay`` after a
        connection that ended cleanly and doubles per failed attempt up to
        ``max_reconnect_delay``, so a Horizon outage costs one retry per
        capped interval instead of a hot loop, while a routine server-side
        disconnect reconnects promptly.

        Args:
            on_transaction: Handler passed through to each consumption; may be
                a coroutine function.

        Note:
            Exceptions from ``on_transaction`` propagate out of this method
            and end the loop — a failing handler is a bug to surface, not a
            disconnected socket to retry.
        """
        delay = self._reconnect_delay

        while not self._stop_event.is_set():
            try:
                await self._consume_stream(on_transaction)
                if self._stop_event.is_set():
                    break
                delay = self._reconnect_delay
                self._logger.warning("Horizon stream disconnected. Reconnecting in %.2fs", delay)
            except asyncio.CancelledError:
                raise
            except Exception:
                if self._stop_event.is_set():
                    break
                self._logger.exception("Horizon stream error. Reconnecting in %.2fs", delay)

            if self._stop_event.is_set():
                break

            await asyncio.sleep(delay)
            delay = min(delay * 2, self._max_reconnect_delay)

        self._logger.info("Horizon streaming client stopped")

    async def _consume_stream(self, on_transaction: TransactionHandler) -> None:
        ssl_context = ssl.create_default_context() if self._base_url.scheme == "https" else None
        port = self._base_url.port or (443 if self._base_url.scheme == "https" else 80)
        host_header = self._base_url.hostname
        if self._base_url.port is not None:
            host_header = f"{host_header}:{self._base_url.port}"

        reader, writer = await asyncio.open_connection(
            host=self._base_url.hostname,
            port=port,
            ssl=ssl_context,
        )
        self._writer = writer

        try:
            request = (
                f"GET {self._request_path()} HTTP/1.1\r\n"
                f"Host: {host_header}\r\n"
                "Accept: text/event-stream\r\n"
                "Connection: close\r\n\r\n"
            )
            writer.write(request.encode("ascii"))
            await writer.drain()

            status = await reader.readline()
            if not status:
                raise HorizonStreamError("No HTTP response from Horizon")

            parts = status.decode("iso-8859-1").strip().split(" ", 2)
            if len(parts) < 2:
                raise HorizonStreamError(f"Invalid HTTP status line: {status!r}")
            status_code = int(parts[1])
            if status_code != 200:
                raise HorizonStreamError(f"Unexpected HTTP status: {status_code}")

            while True:
                header_line = await reader.readline()
                if header_line in {b"\r\n", b"\n", b""}:
                    break

            self._logger.info("Connected to Horizon stream: %s", self._request_path())

            data_lines = []
            while not self._stop_event.is_set():
                line = await reader.readline()
                if not line:
                    return

                text = line.decode("utf-8").rstrip("\r\n")
                if text == "":
                    if data_lines:
                        payload = "\n".join(data_lines)
                        data_lines = []
                        await self._handle_payload(payload, on_transaction)
                    continue

                if text.startswith("data:"):
                    data_lines.append(text[5:].lstrip())
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:  # pragma: no cover - transport specific
                pass
            if self._writer is writer:
                self._writer = None

    async def _handle_payload(
        self,
        payload: str,
        on_transaction: TransactionHandler,
    ) -> None:
        try:
            tx = json.loads(payload)
        except json.JSONDecodeError:
            self._logger.warning("Skipping non-JSON stream payload: %r", payload)
            return

        if not isinstance(tx, dict):
            self._logger.warning("Skipping non-object transaction payload: %r", tx)
            return

        paging_token = tx.get("paging_token")
        if paging_token is not None:
            self._cursor = str(paging_token)

        result = on_transaction(tx)
        if inspect.isawaitable(result):
            await result

    def _request_path(self) -> str:
        query = urlencode({"cursor": self._cursor, "stream": "true"})
        return f"{self._endpoint}?{query}"
