"""ثابت‌ها و مقادیر مجاز مرتبط با API بازو.

همه‌ی این مقادیر از نوع ``str`` هستند، بنابراین هم می‌توانید از خود enum استفاده
کنید و هم از رشته‌ی ساده:

.. code-block:: python

    await client.send_chat_action(chat_id, ChatAction.UPLOAD_PHOTO)
    await client.send_chat_action(chat_id, "upload_photo")  # هم‌ارز
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "ChatAction",
    "ChatMemberStatus",
    "ChatType",
    "InvoiceStatus",
    "MessageEntityType",
    "StickerType",
    "TransactionStatus",
]


class ChatAction(str, Enum):
    """نوع عملی که در متد ``sendChatAction`` برای کاربر نمایش داده می‌شود."""

    TYPING = "typing"
    UPLOAD_PHOTO = "upload_photo"
    RECORD_VIDEO = "record_video"
    UPLOAD_VIDEO = "upload_video"
    RECORD_VOICE = "record_voice"
    UPLOAD_VOICE = "upload_voice"
    CHOOSE_STICKER = "choose_sticker"


class ChatType(str, Enum):
    """نوع گفتگو."""

    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"


class ChatMemberStatus(str, Enum):
    """وضعیت عضو در گفتگو."""

    OWNER = "creator"
    ADMINISTRATOR = "administrator"
    MEMBER = "member"
    RESTRICTED = "restricted"


class StickerType(str, Enum):
    """نوع استیکر."""

    REGULAR = "regular"
    MASK = "mask"


class MessageEntityType(str, Enum):
    """نوع بخش خاصی از متن پیام (طبق مستندات فعلی فقط دو مورد)."""

    MENTION = "mention"
    BOT_COMMAND = "bot_command"


class TransactionStatus(str, Enum):
    """وضعیت تراکنش در متد ``inquireTransaction``."""

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REJECTED = "rejected"


class InvoiceStatus(str, Enum):
    """وضعیت پرداختی که مینی‌اپ از طریق رویداد ``invoiceClosed`` دریافت می‌کند."""

    PAID = "paid"
    CANCELLED = "cancelled"
    FAILED = "failed"
    PENDING = "pending"
