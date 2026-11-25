import re
import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUESTS = Counter(
    "leaflet_http_requests_total",
    "HTTP requests served by the API",
    ["method", "path", "status"],
)
LATENCY = Histogram(
    "leaflet_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
CAMPAIGNS_CREATED = Counter(
    "leaflet_campaigns_created_total",
    "Campaigns created",
)
CONTENT_GENERATED = Counter(
    "leaflet_content_generated_total",
    "Content drafts written",
    ["provider", "kind"],
)
POSTS_DISPATCHED = Counter(
    "leaflet_posts_dispatched_total",
    "Scheduled posts the worker finished",
    ["status"],
)

_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def path_label(path: str) -> str:
    parts = []
    for part in path.strip("/").split("/"):
        if not part:
            continue
        parts.append(":id" if _UUID.match(part) else part)
    return "/" + "/".join(parts) if parts else "/"


class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        if path == "/metrics":
            await self.app(scope, receive, send)
            return
        method = scope.get("method", "GET")
        label = path_label(path)
        started = time.perf_counter()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            LATENCY.labels(method=method, path=label).observe(time.perf_counter() - started)
            REQUESTS.labels(method=method, path=label, status=str(status_code)).inc()


def metrics_payload() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
