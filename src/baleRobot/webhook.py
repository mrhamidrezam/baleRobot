"""کمک‌تابع‌های سمت سرور برای دریافت آپدیت از طریق وب‌هوک.

اگر بازوی شما به جای long polling از وب‌هوک استفاده می‌کند، کافی است بدنه‌ی
درخواست POST سرور بله را با :func:`parse_update` به شیء
:class:`~baleRobot.types.updates.Update` تبدیل کنید.

نمونه با FastAPI:

.. code-block:: python

    from fastapi import FastAPI, Request
    from baleRobot import AsyncBaleClient, parse_update

    app = FastAPI()
    client = AsyncBaleClient("TOKEN")

    @app.post("/webhook")
    async def webhook(request: Request):
        update = parse_update(await request.json())
        message = update.effective_message
        if message is not None and message.text == "/start":
            await client.send_message(message.chat_id, "سلام!")
        return {"ok": True}

.. important::
    فراموش نکنید ابتدا با
    :meth:`~baleRobot.client.AsyncBaleClient.set_webhook` آدرس وب‌هوک را ثبت کنید.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .types.updates import Update

__all__ = ["parse_update"]


def parse_update(payload: Mapping[str, Any] | str | bytes | bytearray) -> Update:
    """تبدیل بدنه‌ی درخواست وب‌هوک به شیء :class:`~baleRobot.types.updates.Update`.

    Args:
        payload: دیکشنری JSON، یا رشته/بایت‌های حاوی JSON.

    Returns:
        شیء آپدیت با شناسایی خودکار نوع آن.

    Raises:
        ValueError: اگر رشته‌ی ورودی JSON معتبر نباشد.
        TypeError: اگر ساختار ورودی پشتیبانی نشود.
    """
    if isinstance(payload, (str, bytes, bytearray)):
        try:
            payload = json.loads(payload)
        except ValueError as exc:
            raise ValueError(f"بدنه‌ی وب‌هوک JSON معتبر نیست: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise TypeError(f"ساختار آپدیت پشتیبانی نمی‌شود: {type(payload)!r}")
    return Update.from_dict(payload)
