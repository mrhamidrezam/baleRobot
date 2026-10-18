"""ساختار خطاهای baleRobot.

هر خطای سطح شبکه زیر :class:`NetworkError` و هر خطای سطح API بازو زیر
:class:`APIError` قرار می‌گیرد. برای مدیریت خطا کافی است یکی از این دو کلاس را
بگیرید:

.. code-block:: python

    try:
        await client.send_message(chat_id, text)
    except baleRobot.TooManyRequests as e:
        await asyncio.sleep(e.retry_after or 1)
    except baleRobot.APIError as e:
        print(e.error_code, e.description)
    except baleRobot.NetworkError:
        # مشکل اتصال به سرور بله
        ...
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from .types.users import ResponseParameters

__all__ = [
    "APIError",
    "BadRequest",
    "BaleError",
    "Conflict",
    "Forbidden",
    "InvalidInitData",
    "NetworkError",
    "NotFound",
    "ServerError",
    "TimedOut",
    "TooManyRequests",
    "Unauthorized",
    "build_api_error",
]


class BaleError(Exception):
    """کلاس پایه برای همه خطاهای این کتابخانه."""


class NetworkError(BaleError):
    """خطای سطح شبکه: قطعی اتصال، خطای HTTP، پاسخ نامعتبر و… ."""


class TimedOut(NetworkError):
    """مهلت تعیین‌شده برای درخواست به پایان رسیده است."""


class APIError(BaleError):
    """خطایی که سرور بازو با پاسخ ``{"ok": false, ...}`` برگردانده است.

    Attributes:
        description: شرح خطای برگشتی از سرور.
        error_code: کد خطای HTTP/منطقی (مثلاً 400).
        parameters: پارامترهای تکمیلی از جنس :class:`~baleRobot.types.users.ResponseParameters`.
    """

    def __init__(
        self,
        description: str = "",
        *,
        error_code: int | None = None,
        parameters: ResponseParameters | None = None,
    ) -> None:
        self.description = description
        self.error_code = error_code
        self.parameters = parameters
        message = description or "خطای ناشناخته از سرور بازو"
        if error_code is not None:
            message = f"[{error_code}] {message}"
        super().__init__(message)

    @property
    def retry_after(self) -> int | None:
        """تعداد ثانیه‌های باقی‌مانده تا امکان ارسال دوباره درخواست (در صورت وجود)."""
        return self.parameters.retry_after if self.parameters is not None else None


class BadRequest(APIError):
    """پارامترهای درخواست نامعتبر هستند (کد 400)."""


class Unauthorized(APIError):
    """توکن بازو نامعتبر است یا به سرور دسترسی ندارید (کد 401)."""


class Forbidden(APIError):
    """دسترسی لازم را ندارید؛ مثلاً بازو مدیر گفتگو نیست (کد 403)."""


class NotFound(APIError):
    """منبع درخواست‌شده پیدا نشد (کد 404)."""


class Conflict(APIError):
    """درگیری وضعیت؛ مثلاً چند درخواست getUpdates همزمان (کد 409)."""


class TooManyRequests(APIError):
    """از سقف نرخ ارسال درخواست عبور کرده‌اید (کد 429).

    مقدار :attr:`~APIError.retry_after` برای برنامه‌ریزی تلاش بعدی مفید است.
    """


class ServerError(APIError):
    """خطای داخلی سرور بازو (کدهای 5xx)."""


class InvalidInitData(BaleError):
    """داده‌های ورودی مینی‌اپ (initData) معتبر نیست یا امضای آن درست نیست."""


def build_api_error(
    error_code: int | None,
    description: str,
    parameters: ResponseParameters | None = None,
) -> APIError:
    """ساخت شیء خطای مناسب بر اساس کد خطا.

    Args:
        error_code: کد خطای برگشتی از سرور.
        description: شرح خطای برگشتی از سرور.
        parameters: پارامترهای تکمیلی (مانند ``retry_after``).

    Returns:
        نمونه‌ای از زیرکلاس مناسب :class:`APIError`.
    """
    code: Any = error_code
    kwargs: dict[str, Any] = {"error_code": error_code, "parameters": parameters}
    if code == 400:
        return BadRequest(description, **kwargs)
    if code == 401:
        return Unauthorized(description, **kwargs)
    if code == 403:
        return Forbidden(description, **kwargs)
    if code == 404:
        return NotFound(description, **kwargs)
    if code == 409:
        return Conflict(description, **kwargs)
    if code == 429:
        return TooManyRequests(description, **kwargs)
    if isinstance(code, int) and code >= 500:
        return ServerError(description, **kwargs)
    return APIError(description, **kwargs)
