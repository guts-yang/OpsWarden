import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("opswarden")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        method = request.method
        url = str(request.url.path)
        query = str(request.query_params)
        client_ip = request.client.host if request.client else "unknown"

        response = await call_next(request)

        duration = round((time.time() - start_time) * 1000, 2)
        status_code = response.status_code

        log_msg = (
            f"{method} {url}"
            f" | query={query}"
            f" | status={status_code}"
            f" | {duration}ms"
            f" | ip={client_ip}"
        )

        if status_code >= 500:
            logger.error(log_msg)
        elif status_code >= 400:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        response.headers["X-Process-Time"] = str(duration)
        return response