import logging
import re

# The WebSocket carries its credential in the query string (browsers cannot set headers on it)
_SECRET_PARAMS = re.compile(r"((?:token|api_key)=)[^&\s\"]+", re.IGNORECASE)


class AccessLogRedactor(logging.Filter):
    """Masks `token=` / `api_key=` values in uvicorn request lines.

    HTTP requests are logged by `uvicorn.access`, WebSocket handshakes ("[accepted]") by `uvicorn.error`.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _SECRET_PARAMS.sub(r"\1***", record.msg)
        if record.args:
            record.args = tuple(_SECRET_PARAMS.sub(r"\1***", a) if isinstance(a, str) else a for a in record.args)
        return True

    @classmethod
    def install(cls) -> None:
        for name in ("uvicorn.access", "uvicorn.error"):
            logging.getLogger(name).addFilter(cls())
