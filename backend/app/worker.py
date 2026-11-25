import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from redis import Redis
from sqlalchemy import text

from app.config import Settings
from app.db import make_engine, make_session_factory
from app.metrics import metrics_payload
from app.services.dispatch import LoggingSender, RedisBroker, run_once

logger = logging.getLogger("leaflet.worker")


def _write(handler: BaseHTTPRequestHandler, status: int, body: bytes, content_type: str) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def serve_health(port: int, ready_check) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0]
            if path == "/healthz":
                _write(self, 200, b"ok\n", "text/plain; charset=utf-8")
                return
            if path == "/readyz":
                try:
                    ready_check()
                except Exception:
                    logger.exception("worker not ready")
                    _write(self, 503, b"not ready\n", "text/plain; charset=utf-8")
                    return
                _write(self, 200, b"ready\n", "text/plain; charset=utf-8")
                return
            if path == "/metrics":
                payload, content_type = metrics_payload()
                _write(self, 200, payload, content_type)
                return
            _write(self, 404, b"not found\n", "text/plain; charset=utf-8")

        def log_message(self, _format: str, *_args) -> None:
            return

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    thread = threading.Thread(target=server.serve_forever, name="worker-health", daemon=True)
    thread.start()
    return server


def main() -> None:
    settings = Settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    if not settings.redis_url:
        raise SystemExit("REDIS_URL is required for the worker")
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    broker = RedisBroker(redis, ttl=settings.dispatch_lock_seconds)
    sender = LoggingSender()

    def ready_check() -> None:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        broker.ping()

    serve_health(settings.worker_port, ready_check)
    logger.info("worker polling every %ss", settings.worker_poll_seconds)
    while True:
        try:
            with session_factory() as session:
                run_once(session, broker, sender)
        except Exception:
            logger.exception("worker pass failed")
        time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    main()
