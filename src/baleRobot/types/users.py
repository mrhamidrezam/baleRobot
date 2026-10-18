"""انواع مرتبط با کاربر و گفتگو.

مستندات: User، Chat، ChatFullInfo، ChatPhoto و ResponseParameters.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaleObject

__all__ = ["Chat", "ChatFullInfo", "ChatPhoto", "ResponseParameters", "User"]


@dataclass
class User(BaleObject):
    """نشان‌دهنده‌ی یک کاربر بله یا یک بازو.

    .. note::
        شناسه ``id`` می‌تواند بزرگ‌تر از 2^31 باشد؛ در پایتون 3 اعداد صحیح بدون
        محدودیت هستند، اما در زبان‌های دیگر مراقب ۶۴ بیتی بودن آن باشید.
    """

    id: int = 0
    is_bot: bool = False
    first_name: str = ""
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


@dataclass
class Chat(BaleObject):
    """نشان‌دهنده‌ی یک گفتگو (شخصی، گروه یا کانال)."""

    id: int = 0
    type: str = ""
    title: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


@dataclass
class ChatPhoto(BaleObject):
    """تصویر پروفایل گفتگو."""

    small_file_id: str = ""
    small_file_unique_id: str = ""
    big_file_id: str = ""
    big_file_unique_id: str = ""


@dataclass
class ChatFullInfo(BaleObject):
    """اطلاعات کامل یک گفتگو (خروجی متد ``getChat``)."""

    id: int = 0
    type: str = ""
    title: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    photo: ChatPhoto | None = None
    bio: str | None = None
    description: str | None = None
    invite_link: str | None = None
    linked_chat_id: int | None = None


@dataclass
class ResponseParameters(BaleObject):
    """اطلاعات مربوط به یک درخواست ناموفق (فیلد ``parameters`` پاسخ خطا)."""

    retry_after: int | None = None
