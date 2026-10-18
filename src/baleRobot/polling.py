"""حلقه‌ی دریافت آپدیت‌ها با long polling (نسخه‌های ناهمگام و همزمان).

نمونه‌ی کامل یک بازوی ساده:

.. code-block:: python

    import asyncio
    from baleRobot import AsyncBaleClient, Update, run_polling

    async def handle(update: Update) -> None:
        message = update.effective_message
        if message is not None and message.text:
            await client.send_message(message.chat_id, f"گفتید: {message.text}")

    async def main() -> None:
        global client
        client = AsyncBaleClient("TOKEN")
        await run_polling(client, handle)

    asyncio.run(main())

نکته: بازو باید با یکی از دو روش ``getUpdates`` یا وب‌هوک آپدیت بگیرد؛ استفاده‌ی
همزمان از هر دو مجاز نیست.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import threading
from collections.abc import Awaitable, Callable
from typing import Any

from .errors import BaleError, NetworkError, ServerError
from .types.updates import Update

__all__ = ["UpdateHandler", "run_polling", "run_polling_sync"]

logger = logging.getLogger("baleRobot")

#: امضای تابع هندلر: هم می‌تواند همزمان باشد و هم ناهمگام
UpdateHandler = Callable[[Update], Any | Awaitable[Any]]
ErrorHandler = Callable[[Update | None, BaseException], Any]


async def _call_handler(
    handler: UpdateHandler,
    update: Update,
    on_error: ErrorHandler | None,
) -> None:
    """فراخوانی هندلر (همگام یا ناهمگام) و مدیریت خطای آن."""
    try:
        result = handler(update)
        if inspect.isawaitable(result):
            await result
    except asyncio.CancelledError:
        raise
    except BaseException as exc:
        if on_error is not None:
            on_error(update, exc)
        else:
            logger.exception("خطا در اجرای هندلر آپدیت %s", update.update_id, exc_info=exc)


async def run_polling(
    client: Any,
    handler: UpdateHandler,
    *,
    timeout: int = 30,
    limit: int = 100,
    skip_pending: bool = False,
    on_error: ErrorHandler | None = None,
    stop_event: asyncio.Event | None = None,
    network_backoff: float = 3.0,
) -> None:
    """حلقه‌ی دریافت آپدیت‌ها (ناهمگام) تا لغو شدن یا ست شدن ``stop_event``.

    Args:
        client: نمونه‌ای از :class:`~baleRobot.client.AsyncBaleClient`.
        handler: تابعی که هر :class:`~baleRobot.types.updates.Update` را دریافت
            می‌کند؛ می‌تواند همزمان یا ناهمگام باشد.
        timeout: مهلت long polling بر حسب ثانیه (سرور خالی برنمی‌گرداند).
        limit: حداکثر تعداد آپدیت در هر فراخوانی (۱ تا ۱۰۰).
        skip_pending: اگر ``True`` باشد، آپدیت‌های انباشته‌ی قبلی نادیده گرفته
            می‌شوند (با ``offset=-1`` طبق مستندات بازو).
        on_error: در صورت استفاده، خطاهای هندلر و شبکه به این تابع سپرده
            می‌شود؛ در غیر این صورت خطای هندلر فقط لاگ می‌شود.
        stop_event: رویدادی که با ست شدن، حلقه متوقف می‌شود.
        network_backoff: مکث (بر حسب ثانیه) پس از خطای شبکه.

    .. note::
        آپدیت پس از پردازش هر مورد، به عنوان «دیده‌شده» علامت می‌خورد؛ بنابراین
        خطای یک پیام، پیام‌های بعدی را از کار نمی‌اندازد.
    """
    offset: int | None = None

    if skip_pending:
        try:
            pending = await client.get_updates(offset=-1, limit=1)
        except BaleError:
            pending = []
        if pending:
            offset = pending[-1].update_id + 1

    while stop_event is None or not stop_event.is_set():
        try:
            updates = await client.get_updates(offset=offset, limit=limit, timeout=timeout)
        except (NetworkError, ServerError) as exc:
            if on_error is not None:
                on_error(None, exc)
            else:
                logger.warning("خطای شبکه در دریافت آپدیت‌ها: %s", exc)
            await asyncio.sleep(network_backoff)
            continue

        for update in updates:
            offset = update.update_id + 1
            await _call_handler(handler, update, on_error)


def run_polling_sync(
    client: Any,
    handler: UpdateHandler,
    *,
    timeout: int = 30,
    limit: int = 100,
    skip_pending: bool = False,
    on_error: ErrorHandler | None = None,
    stop_event: threading.Event | None = None,
    network_backoff: float = 3.0,
) -> None:
    """حلقه‌ی دریافت آپدیت‌ها (همزمان) با کلاینت :class:`~baleRobot.BaleClient`.

    رفتار دقیقاً مانند :func:`run_polling` است؛ با این تفاوت که هندلر باید
    همزمان باشد و ``stop_event`` از جنس :class:`threading.Event` است.
    """
    offset: int | None = None

    if skip_pending:
        try:
            pending = client.get_updates(offset=-1, limit=1)
        except BaleError:
            pending = []
        if pending:
            offset = pending[-1].update_id + 1

    while stop_event is None or not stop_event.is_set():
        try:
            updates = client.get_updates(offset=offset, limit=limit, timeout=timeout)
        except (NetworkError, ServerError) as exc:
            if on_error is not None:
                on_error(None, exc)
            else:
                logger.warning("خطای شبکه در دریافت آپدیت‌ها: %s", exc)
            threading.Event().wait(network_backoff)
            continue

        for update in updates:
            offset = update.update_id + 1
            _call_handler_sync(handler, update, on_error)


def _call_handler_sync(
    handler: UpdateHandler,
    update: Update,
    on_error: ErrorHandler | None,
) -> None:
    """فراخوانی هندلر همزمان و مدیریت خطای آن."""
    try:
        handler(update)
    except KeyboardInterrupt:
        raise
    except BaseException as exc:
        if on_error is not None:
            on_error(update, exc)
        else:
            logger.exception("خطا در اجرای هندلر آپدیت %s", update.update_id, exc_info=exc)
