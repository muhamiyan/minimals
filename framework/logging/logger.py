"""Structured logging, request metrics, and alerting.

Provides:
- ``JSONFormatter`` — ``logging.Formatter`` subclass that emits JSON lines.
- ``get_logger(name)`` — factory returning a logger pre-configured with the
  JSON formatter and a ``StreamHandler``.
- ``init_logging(app)`` — (re)configures the root logger when a Flask app
  starts, reading ``LOG_LEVEL`` from ``app.config``.
- ``RequestMetrics`` — lightweight in-memory request counter + timing
  accumulator, exposed at ``/health`` and ``/ready``.
- ``request_middleware(app)`` — Flask ``before_request``/``after_request``
  pair that logs every request/response as a structured JSON log line.
- ``alert(logger, message)`` — emit a CRITICAL log line flagged as alert
  so a log aggregator can route it to PagerDuty / Slack / etc.

Usage in a service::

    from framework.logging import get_logger, request_middleware, init_logging
    logger = get_logger(__name__)

    def create_app():
        app = Flask(__name__)
        init_logging(app)
        request_middleware(app)
        ...
"""
from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from typing import Any

import flask
from flask import request

# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

class JSONFormatter(logging.Formatter):
    """Emit a single JSON object per log line.

    Fields always present: ``timestamp``, ``level``, ``name``, ``message``.
    Additional fields (``service``, ``request_id``, ``method``, ``path``,
    ``status_code``, ``duration_ms``, ``exception``, ``traceback``) are
    added only when provided via the ``extra`` kwarg of ``logger.info`` etc.
    """

    def __init__(self) -> None:
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        obj: dict[str, Any] = {
            "timestamp": datetime.now(UTC)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        for key in ("service", "request_id", "method", "path",
                     "status_code", "duration_ms", "alert"):
            if hasattr(record, key):
                obj[key] = getattr(record, key)
        if record.exc_info and record.exc_info[0] is not None:
            obj["exception"] = record.exc_info[0].__name__
            obj["traceback"] = self.formatException(record.exc_info)
        return json.dumps(obj, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Request metrics
# ---------------------------------------------------------------------------

@dataclass
class _RequestStat:
    count: int = 0
    total_ms: float = 0.0
    errors: int = 0


class RequestMetrics:
    """In-memory request metrics, thread-safe via a
    ``threading.Lock``. Each process has its own snapshot.

    The stats dictionary is capped at ``max_entries`` to prevent unbounded
    memory growth in long-running processes with many unique paths (e.g.,
    REST APIs with IDs). When capped, new entries are silently dropped.
    """

    def __init__(self, max_entries: int = 1000) -> None:
        self._stats: dict[str, _RequestStat] = {}
        self._total_errors: int = 0
        self._lock: threading.Lock = threading.Lock()
        self._max_entries = max_entries

    def record(self, method: str, path: str, status_code: int,
               duration_ms: float) -> None:
        key = f"{method} {path}"
        with self._lock:
            stat = self._stats.get(key)
            if stat is None:
                # Cap dictionary size to prevent memory leak
                if len(self._stats) >= self._max_entries:
                    return
                stat = _RequestStat()
                self._stats[key] = stat
            stat.count += 1
            stat.total_ms += duration_ms
            if status_code >= 400:
                stat.errors += 1
                self._total_errors += 1

    def snapshot(self, *, endpoints: bool = False) -> dict[str, Any]:
        with self._lock:
            total = sum(s.count for s in self._stats.values())
            total_ms = sum(s.total_ms for s in self._stats.values())
            errors = self._total_errors
            payload = {
                "totalRequests": total,
                "totalErrors": errors,
                "errorRate": round(errors / total, 4) if total else 0.0,
                "avgResponseMs": round(total_ms / total, 2) if total else 0.0,
            }
            if endpoints:
                payload["endpoints"] = {
                    k: {
                        "count": s.count,
                        "avgMs": round(s.total_ms / s.count, 2)
                        if s.count
                        else 0,
                        "errors": s.errors,
                    }
                    for k, s in sorted(self._stats.items())
                }
            return payload

    def reset(self) -> None:
        with self._lock:
            self._stats.clear()
            self._total_errors = 0


# Module-level metrics shared across the service.
metrics = RequestMetrics()


# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------

_root_configured = False
_root_lock = threading.Lock()


def _configure_root(log_level: str = "INFO",
                    log_file: str | None = None) -> None:
    """Configure the root logger with a JSON formatter once.

    Adds a ``StreamHandler`` (always) and, when ``log_file`` is
    given, a ``RotatingFileHandler`` (10 MB per file, 5 backups).
    Thread-safe: only the first caller actually configures.
    """
    global _root_configured
    with _root_lock:
        if _root_configured:
            return
        _root_configured = True

    formatter = JSONFormatter()

    # Console output — always present.
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root.addHandler(stream_handler)
    root.propagate = False

    # Persistent file output with rotation (10 MB per file, 5 backups).
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    # Silence noisy third-party loggers.
    for logger_name in ("werkzeug", "sqlalchemy.engine", "alembic"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str, log_file: str | None = None,
               log_level: str = "INFO") -> logging.Logger:
    """Return a logger whose ``StreamHandler`` uses the JSON formatter.

    The first call configures the root logger; subsequent calls reuse it.
    Pass ``log_file`` to ensure the rotating file handler is added
    even if ``init_logging`` has not been called yet.
    """
    _configure_root(log_level=log_level, log_file=log_file)
    logger = logging.getLogger(name)
    return logger


# ---------------------------------------------------------------------------
# Flask middleware
# ---------------------------------------------------------------------------

def _generate_request_id() -> str:
    return uuid.uuid4().hex[:16]


def request_middleware(app: flask.Flask, service: str = "app") -> None:
    """Register ``before_request``/``after_request`` handlers that log
    every request/response as a structured JSON line via ``app.logger``.

    Also attaches the request context to ``metrics.record()`` so the
    ``/health`` response includes a real-time snapshot.
    """
    log_file = app.config.get("LOG_FILE")

    @app.before_request
    def _before_request():
        request.request_id = _generate_request_id()
        request._start_time = time.monotonic()

    @app.after_request
    def _after_request(response: flask.Response) -> flask.Response:
        if not hasattr(request, "_start_time"):
            return response
        duration = (time.monotonic() - request._start_time) * 1000
        method = request.method
        path = request.path
        status_code = response.status_code

        metrics.record(method, path, status_code, duration)

        logger = get_logger(name="request", log_file=log_file)
        extra: dict[str, Any] = {
            "request_id": getattr(request, "request_id", ""),
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration, 2),
            "service": service,
        }
        # Flag 5xx errors for log-based alerting.
        if status_code >= 500:
            extra["alert"] = True
        logger.info("request", extra=extra)
        return response

    # Expose metrics at /health via a context processor.
    @app.context_processor
    def _inject_metrics():
        return {"metrics": metrics}


# ---------------------------------------------------------------------------
# Alerting helpers
# ---------------------------------------------------------------------------

def alert(logger: logging.Logger, message: str, *,
          service: str = "app", **kwargs: Any) -> None:
    """Emit a CRITICAL alert-level log entry.

    Intended for critical conditions that warrant external attention
    (e.g. repeated auth failures, database connection loss). The log
    line carries ``"alert": true`` so a log aggregator can route it
    to PagerDuty / Slack / etc.

    Usage::

        from framework.logging import alert, get_logger
        logger = get_logger(__name__)
        alert(logger, "database unreachable", service="app")
    """
    logger.critical(message, extra={"alert": True, "service": service,
                                     **kwargs})


# ---------------------------------------------------------------------------
# Alert webhook handler
# ---------------------------------------------------------------------------

class AlertHandler(logging.Handler):
    """Post alert-flagged log records to a webhook URL.

    Only records with ``record.alert == True`` are sent (set by
    :func:`alert` or via ``extra={"alert": True}``). Other records
    are silently ignored by this handler.

    The HTTP POST runs on a dedicated daemon worker thread so
    logging never blocks on network I/O. If the queue fills up
    (default limit 1000) the record is dropped — logging must never
    slow down the application.

    Args:
        webhook_url: Full URL to POST the JSON log line to.
        queue_size: Max buffered records before dropping.
        timeout: HTTP request timeout in seconds.
    """

    def __init__(self, webhook_url: str, queue_size: int = 1000,
                 timeout: int = 10) -> None:
        super().__init__()
        self._webhook_url = webhook_url
        self._timeout = timeout
        self._queue: queue.Queue[logging.LogRecord | None] = queue.Queue(
            maxsize=queue_size
        )
        # Default to JSONFormatter so webhooks receive structured JSON.
        self.setFormatter(JSONFormatter())
        self._worker = threading.Thread(
            target=self._worker_loop, daemon=True, name="alert-handler"
        )
        self._worker.start()

    def emit(self, record: logging.LogRecord) -> None:
        """Enqueue the record for async delivery."""
        if not getattr(record, "alert", False):
            return
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            # Queue full — drop the oldest alert to make room.
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(record)
            except queue.Full:
                self.handleError(record)

    def _worker_loop(self) -> None:
        """Drain the queue and POST each record to the webhook."""
        while True:
            record = self._queue.get()
            if record is None:
                break
            try:
                self._send(record)
            except Exception:
                pass  # Worker thread must not die

    def _send(self, record: logging.LogRecord) -> None:
        payload = self.format(record)
        data = payload.encode("utf-8") if isinstance(payload, str) else payload
        req = urllib.request.Request(
            self._webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=self._timeout)
        except urllib.error.URLError as exc:
            logging.getLogger(__name__).warning(
                "alert webhook delivery failed: %s", exc
            )

    def stop(self) -> None:
        """Signal the worker thread to exit."""
        try:
            self._queue.put(None, block=True, timeout=self._timeout)
        except queue.Full:
            pass
        self._worker.join(timeout=self._timeout + 5)


def init_logging(app: flask.Flask) -> None:
    """Configure the root logger from ``app.config``.

    Reads ``LOG_LEVEL``, ``LOG_FILE``, and ``ALERT_WEBHOOK_URL``
    from ``app.config``.

    When ``ALERT_WEBHOOK_URL`` is set, an ``AlertHandler`` is
    registered on the root logger so any log record with
    ``alert=True`` is posted to that webhook (async, non-blocking).

    Thread-safe: only the first call actually configures the root
    logger. Subsequent calls are no-ops. Call this at the top of
    ``create_app`` before any other initialization.
    """
    log_level = app.config.get("LOG_LEVEL", "INFO")
    log_file = app.config.get("LOG_FILE")
    _configure_root(log_level=log_level, log_file=log_file)

    webhook_url = (
        app.config.get("ALERT_WEBHOOK_URL")
        or os.environ.get("ALERT_WEBHOOK_URL", "")
    )
    if webhook_url:
        # Avoid duplicate handlers if init_logging is called
        # more than once (e.g. during tests).
        existing = any(
            isinstance(h, AlertHandler) and h._webhook_url == webhook_url
            for h in logging.getLogger().handlers
        )
        if not existing:
            formatter = JSONFormatter()
            handler = AlertHandler(webhook_url)
            handler.setFormatter(formatter)
            logging.getLogger().addHandler(handler)


__all__ = [
    "AlertHandler",
    "JSONFormatter",
    "RequestMetrics",
    "alert",
    "get_logger",
    "init_logging",
    "metrics",
    "request_middleware",
]
