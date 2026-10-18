"""همه‌ی انواع داده‌ی API بازو در یک جا.

این انواع هم برای دریافت پاسخ سرور (``from_dict``) و هم برای ساخت درخواست
(``to_dict``) استفاده می‌شوند؛ مثال:

.. code-block:: python

    from baleRobot import Message, InlineKeyboardMarkup

    message: Message = Message.from_dict(raw_json)
    keyboard = InlineKeyboardMarkup.quick([["دکمه"]])
"""

from __future__ import annotations

from .base import BaleObject
from .chat_members import (
    ChatMember,
    ChatMemberAdministrator,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
)
from .files import (
    Animation,
    Audio,
    Document,
    File,
    PhotoSize,
    Sticker,
    StickerSet,
    Video,
    Voice,
)
from .input import (
    InputFile,
    InputMediaAnimation,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    InputSticker,
)
from .keyboards import (
    CopyTextButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)
from .messages import (
    Contact,
    Location,
    Message,
    MessageEntity,
    MessageId,
    WebAppData,
)
from .payments import (
    Invoice,
    LabeledPrice,
    PreCheckoutQuery,
    SuccessfulPayment,
    Transaction,
)
from .updates import CallbackQuery, Update, WebhookInfo
from .users import Chat, ChatFullInfo, ChatPhoto, ResponseParameters, User

__all__ = [  # noqa: RUF022 - گروه‌بندی با کامنت‌های فارسی عمداً حفظ شده است
    "BaleObject",
    # کاربر و گفتگو
    "User",
    "Chat",
    "ChatFullInfo",
    "ChatPhoto",
    "ResponseParameters",
    # پیام
    "Message",
    "MessageId",
    "MessageEntity",
    "Contact",
    "Location",
    "WebAppData",
    # فایل‌ها
    "PhotoSize",
    "Animation",
    "Audio",
    "Document",
    "Video",
    "Voice",
    "File",
    "Sticker",
    "StickerSet",
    # صفحه‌کلید
    "WebAppInfo",
    "CopyTextButton",
    "ReplyKeyboardRemove",
    "KeyboardButton",
    "ReplyKeyboardMarkup",
    "InlineKeyboardButton",
    "InlineKeyboardMarkup",
    # عضویت
    "ChatMember",
    "ChatMemberOwner",
    "ChatMemberAdministrator",
    "ChatMemberMember",
    "ChatMemberRestricted",
    # پرداخت
    "LabeledPrice",
    "Invoice",
    "PreCheckoutQuery",
    "SuccessfulPayment",
    "Transaction",
    # آپدیت
    "Update",
    "WebhookInfo",
    "CallbackQuery",
    # ورودی‌ها
    "InputFile",
    "InputMediaPhoto",
    "InputMediaVideo",
    "InputMediaAnimation",
    "InputMediaAudio",
    "InputMediaDocument",
    "InputSticker",
]
