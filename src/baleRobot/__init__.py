"""baleRobot — کتابخانه‌ی کامل پایتون برای API بازو (ربات‌ساز پیام‌رسان بله).

این کتابخانه **کل مستندات رسمی API بازو** را پوشش می‌دهد: ارسال پیام و رسانه،
مدیریت گفتگو و اعضا، ویرایش پیام، استیکرها، پرداخت کیف‌پول بله، وب‌هوک،
دریافت آپدیت‌ها، متدهای اختصاصی بله (``askReview`` و ``inquireTransaction``) و
API کسب‌وکاری برای پیام انبوه.

سریع‌شروع (همزمان):

.. code-block:: python

    from baleRobot import BaleClient

    with BaleClient("TOKEN") as client:
        print(client.get_me())
        client.send_message(123456789, "سلام دنیا!")

سریع‌شروع (ناهمگام):

.. code-block:: python

    import asyncio
    from baleRobot import AsyncBaleClient

    async def main() -> None:
        async with AsyncBaleClient("TOKEN") as client:
            print(await client.get_me())

    asyncio.run(main())
"""

from __future__ import annotations

from ._version import VERSION_INFO, __version__
from .client import DEFAULT_BASE_URL, AsyncBaleClient
from .constants import (
    ChatAction,
    ChatMemberStatus,
    ChatType,
    InvoiceStatus,
    MessageEntityType,
    StickerType,
    TransactionStatus,
)
from .errors import (
    APIError,
    BadRequest,
    BaleError,
    Conflict,
    Forbidden,
    InvalidInitData,
    NetworkError,
    NotFound,
    ServerError,
    TimedOut,
    TooManyRequests,
    Unauthorized,
)
from .formatting import bold, escape_markdown, inline_note, italic, link
from .miniapp import WebAppInitData, WebAppUser, parse_init_data, validate_init_data
from .polling import run_polling, run_polling_sync
from .sync import BaleClient
from .types import (
    Animation,
    Audio,
    BaleObject,
    CallbackQuery,
    Chat,
    ChatFullInfo,
    ChatMember,
    ChatMemberAdministrator,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
    ChatPhoto,
    Contact,
    CopyTextButton,
    Document,
    File,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    InputMediaAnimation,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    InputSticker,
    Invoice,
    KeyboardButton,
    LabeledPrice,
    Location,
    Message,
    MessageEntity,
    MessageId,
    PhotoSize,
    PreCheckoutQuery,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ResponseParameters,
    Sticker,
    StickerSet,
    SuccessfulPayment,
    Transaction,
    Update,
    User,
    Video,
    Voice,
    WebAppData,
    WebAppInfo,
    WebhookInfo,
)
from .webhook import parse_update

__all__ = [  # noqa: RUF022 - گروه‌بندی با کامنت‌های فارسی عمداً حفظ شده است
    "__version__",
    "VERSION_INFO",
    "DEFAULT_BASE_URL",
    # کلاینت‌ها
    "AsyncBaleClient",
    "BaleClient",
    # دریافت آپدیت و وب‌هوک
    "run_polling",
    "run_polling_sync",
    "parse_update",
    # قالب‌بندی متن
    "bold",
    "italic",
    "link",
    "inline_note",
    "escape_markdown",
    # مینی‌اپ
    "validate_init_data",
    "parse_init_data",
    "WebAppInitData",
    "WebAppUser",
    # ثابت‌ها
    "ChatAction",
    "ChatType",
    "ChatMemberStatus",
    "StickerType",
    "MessageEntityType",
    "TransactionStatus",
    "InvoiceStatus",
    # خطاها
    "BaleError",
    "NetworkError",
    "TimedOut",
    "APIError",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "Conflict",
    "TooManyRequests",
    "ServerError",
    "InvalidInitData",
    # انواع
    "BaleObject",
    "User",
    "Chat",
    "ChatFullInfo",
    "ChatPhoto",
    "ResponseParameters",
    "Message",
    "MessageId",
    "MessageEntity",
    "Contact",
    "Location",
    "WebAppData",
    "PhotoSize",
    "Animation",
    "Audio",
    "Document",
    "Video",
    "Voice",
    "File",
    "Sticker",
    "StickerSet",
    "WebAppInfo",
    "CopyTextButton",
    "ReplyKeyboardRemove",
    "KeyboardButton",
    "ReplyKeyboardMarkup",
    "InlineKeyboardButton",
    "InlineKeyboardMarkup",
    "ChatMember",
    "ChatMemberOwner",
    "ChatMemberAdministrator",
    "ChatMemberMember",
    "ChatMemberRestricted",
    "LabeledPrice",
    "Invoice",
    "PreCheckoutQuery",
    "SuccessfulPayment",
    "Transaction",
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
