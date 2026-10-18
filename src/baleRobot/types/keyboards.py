"""انواع صفحه‌کلید و رابط‌های کاربری پیوست‌شده به پیام‌ها.

مستندات: ReplyKeyboardMarkup، KeyboardButton، InlineKeyboardMarkup،
InlineKeyboardButton، ReplyKeyboardRemove، WebAppInfo، CopyTextButton.

نمونه سریع ساخت صفحه‌کلید inline:

.. code-block:: python

    from baleRobot import InlineKeyboardMarkup

    keyboard = InlineKeyboardMarkup.quick([
        ["منوی اصلی", ("پشتیبانی", "support")],
        [{"text": "مینی‌اپ", "web_app": {"url": "https://example.com/app"}}],
    ])
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from .base import BaleObject

__all__ = [
    "CopyTextButton",
    "InlineKeyboardButton",
    "InlineKeyboardMarkup",
    "KeyboardButton",
    "ReplyKeyboardMarkup",
    "ReplyKeyboardRemove",
    "WebAppInfo",
]


@dataclass
class WebAppInfo(BaleObject):
    """مشخصات یک مینی‌اپ (فقط با پروتکل HTTPS)."""

    url: str


@dataclass
class CopyTextButton(BaleObject):
    """دکمه‌ی inline که با فشردن آن، متن مشخص‌شده رونوشت می‌شود (۱ تا ۲۵۶ کاراکتر)."""

    text: str


@dataclass
class ReplyKeyboardRemove(BaleObject):
    """با ارسال این شیء، صفحه‌کلید سفارشی کاربر حذف می‌شود."""

    remove_keyboard: bool = True


@dataclass
class KeyboardButton(BaleObject):
    """دکمه‌ی صفحه‌کلید پاسخ.

    برای دکمه‌های متنی ساده می‌توان به جای این شیء، مستقیماً رشته ارسال کرد.
    """

    text: str
    request_contact: bool | None = None
    request_location: bool | None = None
    web_app: WebAppInfo | dict[str, Any] | None = None


@dataclass
class ReplyKeyboardMarkup(BaleObject):
    """صفحه‌کلید سفارشی (پایین کادر پیام)."""

    keyboard: list[list[KeyboardButton | str]]
    resize_keyboard: bool | None = None
    one_time_keyboard: bool | None = None
    is_persistent: bool | None = None
    input_field_placeholder: str | None = None
    selective: bool | None = None

    @classmethod
    def quick(
        cls,
        rows: Sequence[Sequence[str | KeyboardButton | dict[str, Any]]],
        **kwargs: Any,
    ) -> ReplyKeyboardMarkup:
        """ساخت سریع صفحه‌کلید پاسخ از ردیف‌هایی از رشته یا دیکشنری.

        Args:
            rows: ردیف‌های دکمه؛ هر دکمه می‌تواند رشته، :class:`KeyboardButton`
                یا دیکشنری قابل تبدیل به KeyboardButton باشد.
            **kwargs: سایر پارامترهای :class:`ReplyKeyboardMarkup`.

        Returns:
            شیء آماده‌ی استفاده در پارامتر ``reply_markup``.
        """
        keyboard: list[list[KeyboardButton | str]] = []
        for row in rows:
            buttons: list[KeyboardButton | str] = []
            for item in row:
                if isinstance(item, (str, KeyboardButton)):
                    buttons.append(item)
                elif isinstance(item, dict):
                    buttons.append(KeyboardButton(**item))
                else:
                    raise TypeError(f"دکمه‌ی صفحه‌کلید پشتیبانی نمی‌شود: {type(item)!r}")
            keyboard.append(buttons)
        return cls(keyboard=keyboard, **kwargs)


@dataclass
class InlineKeyboardButton(BaleObject):
    """دکمه‌ی صفحه‌کلید inline؛ فقط یکی از فیلدهای اختیاری باید استفاده شود."""

    text: str
    url: str | None = None
    callback_data: str | None = None
    web_app: WebAppInfo | dict[str, Any] | None = None
    copy_text: CopyTextButton | dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if isinstance(self.web_app, dict):
            self.web_app = WebAppInfo(**self.web_app)
        if isinstance(self.copy_text, dict):
            self.copy_text = CopyTextButton(**self.copy_text)

    @classmethod
    def quick(cls, item: str | InlineKeyboardButton | dict[str, Any]) -> InlineKeyboardButton:
        """ساخت سریع دکمه: رشته (فقط متن)، دیکشنری یا شیء آماده."""
        if isinstance(item, InlineKeyboardButton):
            return item
        if isinstance(item, str):
            return cls(text=item)
        if isinstance(item, dict):
            data = dict(item)
            if isinstance(data.get("web_app"), dict):
                data["web_app"] = WebAppInfo(**data["web_app"])
            if isinstance(data.get("copy_text"), dict):
                data["copy_text"] = CopyTextButton(**data["copy_text"])
            return cls(**data)
        raise TypeError(f"دکمه‌ی inline پشتیبانی نمی‌شود: {type(item)!r}")


@dataclass
class InlineKeyboardMarkup(BaleObject):
    """صفحه‌کلید inline که درست زیر پیام نمایش داده می‌شود."""

    inline_keyboard: list[list[InlineKeyboardButton]] = field(default_factory=list)

    @classmethod
    def quick(
        cls,
        rows: Sequence[Sequence[str | InlineKeyboardButton | dict[str, Any]]],
    ) -> InlineKeyboardMarkup:
        """ساخت سریع صفحه‌کلید inline.

        هر ردیف می‌تواند ترکیبی از این موارد باشد:

        * رشته خالص: دکمه‌ای فقط با متن.
        * ``("متن", "callback_data")`` یا ``{"text": ..., "url": ...}``
        * شیء :class:`InlineKeyboardButton`

        .. code-block:: python

            InlineKeyboardMarkup.quick([
                ["دکمه فقط-متن", ("برچسب‌دار", "cb:1")],
                [{"text": "وب‌سایت", "url": "https://ble.ir"}],
            ])
        """
        inline_keyboard: list[list[InlineKeyboardButton]] = []
        for row in rows:
            buttons: list[InlineKeyboardButton] = []
            for item in row:
                if isinstance(item, tuple) and len(item) == 2:
                    text, payload = item
                    buttons.append(
                        InlineKeyboardButton.quick({"text": text, "callback_data": payload})
                    )
                else:
                    buttons.append(InlineKeyboardButton.quick(item))
            inline_keyboard.append(buttons)
        return cls(inline_keyboard=inline_keyboard)
