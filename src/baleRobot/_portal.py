"""اجرای یک حلقه‌ی رویداد asyncio در نخ پس‌زمینه.

کلاینت همزمان :class:`~baleRobot.client.BaleClient` از همین سازوکار استفاده می‌کند
تا پیاده‌سازی متدها تنها یک بار (به صورت ناهمگام) نوشته شود و نسخه‌ی همزمان
دقیقاً همان رفتار را داشته باشد — بدون دوباره‌کاری و بدون اشکالات ناشی از دو
پیاده‌سازی مجزا.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from typing import Any, TypeVar

__all__ = ["EventLoopThread"]

T = TypeVar("T")


class EventLoopThread:
    """یک حلقه‌ی asyncio که در نخ اختصاصی خودش اجرا می‌شود.

    استفاده:

    .. code-block:: python

        portal = EventLoopThread()
        result = portal.run(some_async_callable())  # از هر نخی امن است
        portal.close()
    """

    def __init__(self, name: str = "baleRobot-loop") -> None:
        self._name = name
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """حلقه‌ی رویداد فعال (در صورت نیاز ساخته می‌شود)."""
        with self._lock:
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
                self._thread = threading.Thread(
                    target=self._run,
                    name=self._name,
                    args=(self._loop,),
                    daemon=True,
                )
                self._thread.start()
            return self._loop

    @staticmethod
    def _run(loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        try:
            loop.run_forever()
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                asyncio.set_event_loop(None)
                loop.close()

    # ------------------------------------------------------------------ #
    def run(self, coro: Coroutine[Any, Any, T], timeout: float | None = None) -> T:
        """اجرای یک coroutine در حلقه‌ی پس‌زمینه و بازگرداندن نتیجه‌ی آن.

        Args:
            coro: coroutine مورد اجرا.
            timeout: حداکثر مهلت انتظار بر حسب ثانیه؛ ``None`` یعنی بدون سقف
                (مهلت‌های شبکه همچنان توسط httpx اعمال می‌شوند).

        Raises:
            TimeoutError: اگر اجرا از مهلت بیشتر شود (و درخواست لغو می‌شود).
        """
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout)
        except TimeoutError:
            future.cancel()
            raise

    # ------------------------------------------------------------------ #
    def close(self, timeout: float = 5.0) -> None:
        """توقف حلقه و انتظار برای پایان نخ پس‌زمینه."""
        with self._lock:
            loop, thread = self._loop, self._thread
            self._loop, self._thread = None, None
        if loop is None or loop.is_closed():
            return
        loop.call_soon_threadsafe(loop.stop)
        if thread is not None:
            thread.join(timeout)

    @property
    def is_closed(self) -> bool:
        """آیا حلقه‌ی پس‌زمینه بسته یا هرگز ساخته نشده است؟"""
        loop = self._loop
        return loop is None or loop.is_closed()

    def __enter__(self) -> EventLoopThread:
        _ = self.loop  # راه‌اندازی تنبل حلقه پیش از خروج از context manager
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()
