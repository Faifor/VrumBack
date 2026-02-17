import base64
import json
import uuid
from urllib import error, request

from fastapi import HTTPException, status

from modules.utils.config import settings


class YooKassaClient:
    def __init__(self):
        if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="YooKassa credentials are not configured",
            )

        auth_str = f"{settings.YOOKASSA_SHOP_ID}:{settings.YOOKASSA_SECRET_KEY}".encode()
        self.auth_header = f"Basic {base64.b64encode(auth_str).decode()}"
        self.base_url = settings.YOOKASSA_API_URL.rstrip("/")

    def create_payment(self, payload: dict, idempotence_key: str | None = None) -> dict:
        return self._request("POST", "/payments", payload, idempotence_key=idempotence_key)

    def create_refund(self, payload: dict, idempotence_key: str | None = None) -> dict:
        return self._request("POST", "/refunds", payload, idempotence_key=idempotence_key)

    def _request(self, method: str, path: str, payload: dict, idempotence_key: str | None = None) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")

        req = request.Request(url, data=data, method=method)
        req.add_header("Authorization", self.auth_header)
        req.add_header("Content-Type", "application/json")
        req.add_header("Idempotence-Key", idempotence_key or str(uuid.uuid4()))

        try:
            with request.urlopen(req, timeout=20) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw)
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8") if exc.fp else ""
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"YooKassa error: {body or exc.reason}",
            ) from exc
        except error.URLError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"YooKassa connection error: {exc.reason}",
            ) from exc