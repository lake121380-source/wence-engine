import logging
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get("-")
        return True


def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    root = logging.getLogger()

    # Avoid duplicate handlers when reload mode imports twice.
    if root.handlers:
        root.setLevel(level)
        for handler in root.handlers:
            handler.addFilter(RequestIdFilter())
        return

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(request_id)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root.setLevel(level)
    root.addHandler(handler)
