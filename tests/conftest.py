"""برنامه‌ریزهای مشترک تست‌ها.

از ``httpx.MockTransport`` استفاده می‌شود تا هیچ درخواست شبکه‌ای واقعی ارسال نشود.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from baleRobot import AsyncBaleClient

TOKEN = "123456:TEST-token_value"


def ok(result: Any) -> httpx.Response:
    """پاسخ موفق سرور بازو."""
    return httpx.Response(200, json={"ok": True, "result": result})


def fail(
    error_code: int,
    description: str,
    parameters: dict[str, Any] | None = None,
) -> httpx.Response:
    """پاسخ ناموفق سرور بازو."""
    payload: dict[str, Any] = {"ok": False, "error_code": error_code, "description": description}
    if parameters is not None:
        payload["parameters"] = parameters
    return httpx.Response(error_code, json=payload)


def msg_ok(message_id: int = 1, chat_id: int = 1, **extra: Any) -> httpx.Response:
    """پاسخ موفقِ یک Message ساده برای متدهایی که Message برمی‌گردانند."""
    body: dict[str, Any] = {
        "message_id": message_id,
        "date": 1,
        "chat": {"id": chat_id, "type": "private"},
    }
    body.update(extra)
    return ok(body)


class FakeAPI:
    """یک سرور جعلی که درخواست‌ها را ثبت و پاسخ‌های ازپیش‌تعریف‌شده برمی‌گرداند."""

    def __init__(self) -> None:
        self.calls: list[httpx.Request] = []
        self.handlers: dict[str, list[httpx.Response | Callable[[], httpx.Response]]] = {}

    def add(self, method_name: str, *responses: Any) -> None:
        """ثبت پاسخ(ها) برای یک متد API؛ اگر چند پاسخ داده شود، به ترتیب مصرف می‌شود."""
        self.handlers[method_name] = list(responses)

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handle)

    def client(self, **kwargs: Any) -> AsyncBaleClient:
        kwargs.setdefault("auto_retry", False)
        return AsyncBaleClient(TOKEN, transport=self.transport(), **kwargs)

    def sync_client(self, **kwargs: Any) -> Any:
        """ساخت کلاینت همزمان متصل به همین سرور جعلی."""
        from baleRobot import BaleClient

        kwargs.setdefault("auto_retry", False)
        return BaleClient(TOKEN, transport=self.transport(), **kwargs)

    def json_body(self, index: int = -1) -> dict[str, Any]:
        """بدنه‌ی JSON درخواست شماره‌ی index (آخرین به صورت پیش‌فرض)."""
        return json.loads(self.calls[index].content.decode("utf-8"))

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        method_name = request.url.path.rsplit("/", 1)[-1]
        queue = self.handlers.get(method_name)
        if not queue:
            return ok(True)
        response = queue.pop(0) if len(queue) > 1 else queue[0]
        if callable(response):
            return response()
        return response


@pytest.fixture
def fake_api() -> FakeAPI:
    """ساخت یک سرور جعلی برای هر تست."""
    return FakeAPI()


@pytest.fixture
def anyio_backend() -> str:
    """پشتیبان asyncio برای پلاگین anyio."""
    return "asyncio"
