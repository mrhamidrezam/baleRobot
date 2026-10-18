"""انواع مرتبط با دریافت آپدیت‌ها و وب‌هوک.

مستندات: Update، WebhookInfo، CallbackQuery.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, TypeVar

from .base import BaleObject
from .messages import Message
from .payments import PreCheckoutQuery
from .users import User

__all__ = ["UPDATE_KINDS", "CallbackQuery", "Update", "WebhookInfo"]

_T = TypeVar("_T", bound="Update")

#: فیلدهای اختیاری که می‌توانند در هر آپدیت وجود داشته باشند
UPDATE_KINDS = ("message", "edited_message", "callback_query", "pre_checkout_query")


@dataclass
class WebhookInfo(BaleObject):
    """وضعیت فعلی وب‌هوک (خروجی متد ``getWebhookInfo``)."""

    url: str = ""


@dataclass
class CallbackQuery(BaleObject):
    """فراخوانی برگشتیِ ناشی از فشردن یک دکمه‌ی inline.

    پس از دریافت آن، حتی اگر نیازی به نمایش پیام ندارید، باید با
    :meth:`baleRobot.AsyncBaleClient.answer_callback_query` پاسخ دهید تا دکمه از
    حالت انتظار خارج شود.
    """

    id: str = ""
    from_user: User = field(default_factory=User, metadata={"api": "from"})
    message: Message | None = None
    data: str | None = None


@dataclass
class Update(BaleObject):
    """یک آپدیت دریافتی از بازو.

    در هر آپدیت حداکثر یکی از فیلدهای اختیاری مقدار دارد؛ برای شناسایی نوع آپدیت
    می‌توانید از همین فیلدها یا از :attr:`effective_message` و
    :attr:`effective_user` استفاده کنید.
    """

    update_id: int = 0
    message: Message | None = None
    edited_message: Message | None = None
    callback_query: CallbackQuery | None = None
    pre_checkout_query: PreCheckoutQuery | None = None

    @classmethod
    def from_dict(cls: type[_T], data: Mapping[str, Any] | None) -> _T:
        """ساخت آپدیت با شناسایی خودکار نوع آن.

        اگر به هر دلیل چند فیلد همزمان مقدار داشته باشند، فقط فیلد نخستِ معتبر
        نگه داشته می‌شود تا ``kind`` همیشه قاطع باشد.
        """
        if not isinstance(data, Mapping):
            raise TypeError(f"Update.from_dict انتظار دیکشنری دارد، {type(data)!r} رسید")
        update = super().from_dict(data)
        for kind in UPDATE_KINDS:
            if getattr(update, kind, None) is not None:
                for other in UPDATE_KINDS:
                    if other != kind:
                        setattr(update, other, None)
                break
        return update

    @property
    def kind(self) -> str | None:
        """نوع آپدیت: ``message``، ``edited_message``، ``callback_query``، … ."""
        for kind in UPDATE_KINDS:
            if getattr(self, kind, None) is not None:
                return kind
        return None

    @property
    def effective_message(self) -> Message | None:
        """پیام مرتبط با این آپدیت (پیام عادی، ویرایش‌شده یا پیامِ کال‌بک‌کوئری)."""
        if self.message is not None:
            return self.message
        if self.edited_message is not None:
            return self.edited_message
        if self.callback_query is not None:
            return self.callback_query.message
        return None

    @property
    def effective_user(self) -> User | None:
        """کاربر مرتبط با این آپدیت (فرستنده‌ی پیام، فشرنده‌ی دکمه یا پرداخت‌کننده)."""
        if self.message is not None and self.message.from_user is not None:
            return self.message.from_user
        if self.edited_message is not None and self.edited_message.from_user is not None:
            return self.edited_message.from_user
        if self.callback_query is not None:
            return self.callback_query.from_user
        if self.pre_checkout_query is not None:
            return self.pre_checkout_query.from_user
        return None
