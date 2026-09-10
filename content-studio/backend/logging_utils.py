import logging
import re
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get("-")
        return True


class SensitiveQueryFilter(logging.Filter):
    """Redact credentials that HTTP client logs may include in query strings."""

    _pattern = re.compile(
        r"([?&](?:key|api[_-]?key|token|secret|password|authorization)=)"
        r"[^&#\s]+",
        re.IGNORECASE,
    )

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
            redacted = self._pattern.sub(r"\1<redacted>", message)
            if redacted != message:
                # Formatter calls getMessage() again; clear args so the
                # already-rendered, redacted text is not interpolated twice.
                record.msg = redacted
                record.args = ()
        except Exception:
            # Logging must never be able to break the request path.
            pass
        return True


def _attach_filters(handler: logging.Handler) -> None:
    """Install request-id and query-redaction filters once per handler."""
    if not any(isinstance(item, RequestIdFilter) for item in handler.filters):
        handler.addFilter(RequestIdFilter())
    if not any(isinstance(item, SensitiveQueryFilter) for item in handler.filters):
        handler.addFilter(SensitiveQueryFilter())


def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    root = logging.getLogger()

    # Avoid duplicate handlers when reload mode imports twice.
    if root.handlers:
        root.setLevel(level)
        for handler in root.handlers:
            _attach_filters(handler)
        return

    handler = logging.StreamHandler()
    handler.setLevel(level)
    _attach_filters(handler)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(request_id)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root.setLevel(level)
    root.addHandler(handler)
