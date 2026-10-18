"""انواع مرتبط با پیام.

مستندات: Message، MessageId، MessageEntity، Contact، Location و WebAppData.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .base import BaleObject
from .files import Animation, Audio, Document, PhotoSize, Sticker, Video, Voice
from .keyboards import InlineKeyboardMarkup
from .payments import Invoice, SuccessfulPayment
from .users import Chat, User

if TYPE_CHECKING:  # pragma: no cover
    pass

__all__ = [
    "Contact",
    "Location",
    "Message",
    "MessageEntity",
    "MessageId",
    "WebAppData",
]


@dataclass
class MessageEntity(BaleObject):
    """بخش خاصی از متن پیام؛ مثل نام کاربری (@username) یا دستور بازو (/command).

    .. note::
        ``offset`` و ``length`` بر حسب واحدهای UTF-16 اندازه‌گیری می‌شوند.
    """

    type: str = ""
    offset: int = 0
    length: int = 0


@dataclass
class MessageId(BaleObject):
    """شناسه‌ی منحصربه‌فرد یک پیام (خروجی متد ``copyMessage``)."""

    message_id: int = 0


@dataclass
class Contact(BaleObject):
    """یک مخاطب تلفن به اشتراک‌گذاشته‌شده."""

    phone_number: str = ""
    first_name: str = ""
    last_name: str | None = None
    user_id: int | None = None


@dataclass
class Location(BaleObject):
    """یک نقطه روی نقشه."""

    longitude: float = 0.0
    latitude: float = 0.0


@dataclass
class WebAppData(BaleObject):
    """داده‌ای که از طرف مینی‌اپ برای بازو ارسال شده است.

    .. warning::
        مقدار ``data`` می‌تواند جعلی باشد؛ آن را در سرور بازو اعتبارسنجی کنید.
    """

    data: str = ""


@dataclass
class Message(BaleObject):
    """یک پیام دریافتی یا ارسال‌شده.

    بسته به نوع پیام، فقط یکی از فیلدهای رسانه‌ای (``text``، ``photo``،
    ``video``، ``document`` و…) مقدار خواهد داشت.
    """

    message_id: int = 0
    date: int = 0
    chat: Chat | None = None
    from_user: User | None = field(default=None, metadata={"api": "from"})
    sender_chat: Chat | None = None
    forward_from: User | None = None
    forward_from_chat: Chat | None = None
    forward_from_message_id: int | None = None
    forward_date: int | None = None
    reply_to_message: Message | None = None
    edit_date: int | None = None
    media_group_id: str | None = None
    text: str | None = None
    entities: list[MessageEntity] | None = None
    animation: Animation | None = None
    audio: Audio | None = None
    document: Document | None = None
    photo: list[PhotoSize] | None = None
    sticker: Sticker | None = None
    video: Video | None = None
    voice: Voice | None = None
    caption: str | None = None
    caption_entities: list[MessageEntity] | None = None
    contact: Contact | None = None
    location: Location | None = None
    new_chat_members: list[User] | None = None
    left_chat_member: User | None = None
    invoice: Invoice | None = None
    successful_payment: SuccessfulPayment | None = None
    web_app_data: WebAppData | None = None
    reply_markup: InlineKeyboardMarkup | None = None

    @property
    def chat_id(self) -> int | None:
        """شناسه‌ی گفتگوی این پیام (در صورت وجود)."""
        return self.chat.id if self.chat is not None else None

    @property
    def user_id(self) -> int | None:
        """شناسه‌ی فرستنده‌ی پیام (در صورت وجود)."""
        return self.from_user.id if self.from_user is not None else None

    @property
    def is_command(self) -> bool:
        """آیا پیام با یک دستور بازو (مثل ``/start``) آغاز شده است؟"""
        return bool(self.text) and self.text.lstrip().startswith("/")

    @property
    def command(self) -> str | None:
        """دستورِ پیام بدون «/» و بدون پارامترها؛ مثلاً ``start``."""
        if not self.text:
            return None
        first = self.text.strip().split(maxsplit=1)[0]
        if not first.startswith("/"):
            return None
        return first[1:].split("@", 1)[0] or None

    @property
    def args(self) -> list[str]:
        """پارامترهای پیام پس از دستور (جداشده با فاصله)."""
        if not self.text:
            return []
        parts = self.text.strip().split()
        return parts[1:] if parts and parts[0].startswith("/") else []

    @property
    def content_type(self) -> str | None:
        """نوع محتوای پیام: ``text``، ``photo``، ``video``، ``document``، … ."""
        for name in (
            "text",
            "photo",
            "animation",
            "audio",
            "document",
            "video",
            "voice",
            "sticker",
            "contact",
            "location",
            "invoice",
            "web_app_data",
            "successful_payment",
        ):
            if getattr(self, name, None) is not None:
                return name
        return None
