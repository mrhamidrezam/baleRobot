"""کلاینت همزمان API بازو — پوشش کامل مستندات رسمی.

همان متدهای :class:`~baleRobot.client.AsyncBaleClient` را با امضای کاملاً یکسان
ارائه می‌دهد، اما به صورت همزمان (Blocking):

.. code-block:: python

    from baleRobot import BaleClient

    with BaleClient("TOKEN") as client:
        me = client.get_me()
        client.send_message(chat_id, f"سلام {me.first_name}!")

زیرساخت اجرا یک حلقه‌ی رویداد در نخ پس‌زمینه است؛ بنابراین:

* نتایج و خطاها دقیقاً مشابه نسخه‌ی ناهمگام هستند.
* می‌توانید این کلاینت را از چند نخ همزمان استفاده کنید.
* اگر درون کد ناهمگام هستید، از :class:`~baleRobot.client.AsyncBaleClient`
  استفاده کنید تا حلقه‌ی رویداد شما مسدود نشود.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ._portal import EventLoopThread
from .client import DEFAULT_BASE_URL, AsyncBaleClient, InputMedia, ReplyMarkup
from .types.chat_members import ChatMember
from .types.files import File
from .types.input import InputSticker
from .types.keyboards import InlineKeyboardMarkup
from .types.messages import Message, MessageId
from .types.payments import LabeledPrice, Transaction
from .types.updates import Update, WebhookInfo
from .types.users import ChatFullInfo, User

__all__ = ["BaleClient"]


class BaleClient:
    """کلاینت همزمان API بازو.

    Args:
        token: توکن احراز هویت بازو از @botfather.
        business: استفاده از API کسب‌وکاری (پیام انبوه) به جای API عادی.
        base_url: آدرس پایه‌ی API.
        timeout: مهلت کل هر درخواست بر حسب ثانیه.
        connect_timeout: مهلت برقراری اتصال بر حسب ثانیه.
        auto_retry: تلاش خودکار هنگام خطاهای موقت (429 و 5xx).
        max_retries: حداکثر تعداد تلاش مجدد.
        retry_backoff: مکث اولیه‌ی تلاش مجدد (در هر تلاش دو برابر می‌شود).
        max_retry_delay: سقف مکث بین تلاش‌ها.
        headers: هدرهای دلخواه HTTP.
        transport: ترنسپورت httpx سفارشی (برای تست).
        httpx_client: یک شیء ``httpx.AsyncClient`` آماده.
    """

    base_url: str = DEFAULT_BASE_URL

    def __init__(self, token: str, **kwargs: Any) -> None:
        self._async = AsyncBaleClient(token, **kwargs)
        self._portal = EventLoopThread(name=f"baleRobot-{id(self):x}")
        self._closed = False

    # ------------------------------------------------------------------ #
    # مشخصات
    # ------------------------------------------------------------------ #
    @property
    def token(self) -> str:
        """توکن بازو."""
        return self._async.token

    @property
    def business(self) -> bool:
        """آیا از API کسب‌وکاری استفاده می‌شود؟"""
        return self._async.business

    @property
    def async_client(self) -> AsyncBaleClient:
        """کلاینت ناهمگام زیرین (برای استفاده در کد asyncio)."""
        return self._async

    def _run(self, coro: Any) -> Any:
        if self._closed:
            coro.close()  # جلوگیری از هشدار coroutine never awaited
            raise RuntimeError("کلاینت بسته شده است؛ ابتدا یک نمونه‌ی جدید بسازید")
        return self._portal.run(coro)

    # ------------------------------------------------------------------ #
    # دانلود فایل
    # ------------------------------------------------------------------ #
    def file_url(self, file_path: str) -> str:
        """لینک مستقیم دانلود یک فایل (اعتبار: یک ساعت)."""
        return self._async.file_url(file_path)

    def get_file(self, file_id: str, **kwargs: Any) -> File:
        """دریافت اطلاعات پایه‌ی یک فایل و آماده‌سازی برای دانلود (متد ``getFile``)."""
        return self._run(self._async.get_file(file_id, **kwargs))

    def download_file(
        self,
        file: str | File,
        *,
        destination: str | None = None,
        timeout: float | None = 300.0,
        **kwargs: Any,
    ) -> bytes | str:
        """دانلود کامل یک فایل؛ در صورت تعیین ``destination`` روی دیسک ذخیره می‌شود."""
        return self._run(
            self._async.download_file(file, destination=destination, timeout=timeout, **kwargs)
        )

    # ------------------------------------------------------------------ #
    # متدهای عمومی بازو
    # ------------------------------------------------------------------ #
    def get_me(self, **kwargs: Any) -> User:
        """تست توکن و دریافت اطلاعات پایه‌ی بازو (متد ``getMe``)."""
        return self._run(self._async.get_me(**kwargs))

    def send_message(
        self,
        chat_id: str | int,
        text: str,
        *,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال پیام متنی (متد ``sendMessage``)."""
        return self._run(
            self._async.send_message(
                chat_id,
                text,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
                **kwargs,
            )
        )

    def forward_message(
        self,
        chat_id: str | int,
        from_chat_id: str | int,
        message_id: int,
        **kwargs: Any,
    ) -> Message:
        """بازارسال (فوروارد) هر نوع پیام (متد ``forwardMessage``)."""
        return self._run(self._async.forward_message(chat_id, from_chat_id, message_id, **kwargs))

    def copy_message(
        self,
        chat_id: str | int,
        from_chat_id: str | int,
        message_id: int,
        **kwargs: Any,
    ) -> MessageId:
        """کپی پیام بدون لینک به پیام اصلی (متد ``copyMessage``)."""
        return self._run(self._async.copy_message(chat_id, from_chat_id, message_id, **kwargs))

    def send_photo(
        self,
        chat_id: str | int,
        photo: Any,
        *,
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال تصویر (متد ``sendPhoto``)."""
        return self._run(
            self._async.send_photo(
                chat_id,
                photo,
                caption=caption,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
                **kwargs,
            )
        )

    def send_audio(
        self,
        chat_id: str | int,
        audio: Any,
        *,
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال فایل صوتی (متد ``sendAudio``)."""
        return self._run(
            self._async.send_audio(
                chat_id,
                audio,
                caption=caption,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
                **kwargs,
            )
        )

    def send_document(
        self,
        chat_id: str | int,
        document: Any,
        *,
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال سند/فایل عمومی (متد ``sendDocument``)."""
        return self._run(
            self._async.send_document(
                chat_id,
                document,
                caption=caption,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
                **kwargs,
            )
        )

    def send_video(
        self,
        chat_id: str | int,
        video: Any,
        *,
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال ویدیو (متد ``sendVideo``)."""
        return self._run(
            self._async.send_video(
                chat_id,
                video,
                caption=caption,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
                **kwargs,
            )
        )

    def send_animation(
        self,
        chat_id: str | int,
        animation: Any,
        *,
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال انیمیشن (متد ``sendAnimation``)."""
        return self._run(
            self._async.send_animation(
                chat_id,
                animation,
                caption=caption,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
                **kwargs,
            )
        )

    def send_voice(
        self,
        chat_id: str | int,
        voice: Any,
        *,
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال پیام صوتی (متد ``sendVoice``)."""
        return self._run(
            self._async.send_voice(
                chat_id,
                voice,
                caption=caption,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
                **kwargs,
            )
        )

    def send_media_group(
        self,
        chat_id: str | int,
        media: Sequence[InputMedia],
        *,
        reply_to_message_id: int | None = None,
        **kwargs: Any,
    ) -> list[Message]:
        """ارسال آلبوم تصاویر/ویدیوها/اسناد/صوت (متد ``sendMediaGroup``)."""
        return self._run(
            self._async.send_media_group(
                chat_id, media, reply_to_message_id=reply_to_message_id, **kwargs
            )
        )

    def send_location(
        self,
        chat_id: str | int,
        latitude: float,
        longitude: float,
        *,
        horizontal_accuracy: float | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال موقعیت روی نقشه (متد ``sendLocation``)."""
        return self._run(
            self._async.send_location(
                chat_id,
                latitude,
                longitude,
                horizontal_accuracy=horizontal_accuracy,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
                **kwargs,
            )
        )

    def send_contact(
        self,
        chat_id: str | int,
        phone_number: str | int,
        first_name: str,
        *,
        last_name: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال مخاطب تلفن (متد ``sendContact``)."""
        return self._run(
            self._async.send_contact(
                chat_id,
                phone_number,
                first_name,
                last_name=last_name,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
                **kwargs,
            )
        )

    def send_chat_action(self, chat_id: str | int, action: str | Any, **kwargs: Any) -> bool:
        """نمایش وضعیت عملیات بازو برای کاربر (متد ``sendChatAction``)."""
        return self._run(self._async.send_chat_action(chat_id, action, **kwargs))

    def answer_callback_query(
        self,
        callback_query_id: str,
        *,
        text: str | None = None,
        show_alert: bool | None = None,
        **kwargs: Any,
    ) -> bool:
        """پاسخ به فراخوانی دکمه‌ی inline (متد ``answerCallbackQuery``)."""
        return self._run(
            self._async.answer_callback_query(
                callback_query_id, text=text, show_alert=show_alert, **kwargs
            )
        )

    def ask_review(self, user_id: int, delay_seconds: int, **kwargs: Any) -> bool:
        """نمایش فرم رضایت‌سنجی بازو به کاربر (متد اختصاصی بله ``askReview``)."""
        return self._run(self._async.ask_review(user_id, delay_seconds, **kwargs))

    # ------------------------------------------------------------------ #
    # مدیریت گفتگو و اعضا
    # ------------------------------------------------------------------ #
    def ban_chat_member(self, chat_id: str | int, user_id: int, **kwargs: Any) -> bool:
        """مسدودکردن کاربر در گروه/کانال (متد ``banChatMember``)."""
        return self._run(self._async.ban_chat_member(chat_id, user_id, **kwargs))

    def unban_chat_member(
        self,
        chat_id: str | int,
        user_id: int,
        *,
        only_if_banned: bool | None = None,
        **kwargs: Any,
    ) -> bool:
        """رفع مسدودیت کاربر (متد ``unbanChatMember``)."""
        return self._run(
            self._async.unban_chat_member(chat_id, user_id, only_if_banned=only_if_banned, **kwargs)
        )

    def promote_chat_member(
        self,
        chat_id: str | int,
        user_id: int,
        *,
        can_change_info: bool | None = None,
        can_post_messages: bool | None = None,
        can_edit_messages: bool | None = None,
        can_delete_messages: bool | None = None,
        can_manage_video_chats: bool | None = None,
        can_invite_users: bool | None = None,
        can_restrict_members: bool | None = None,
        **kwargs: Any,
    ) -> bool:
        """ارتقا/تنزل سطح کاربر (متد ``promoteChatMember``)."""
        return self._run(
            self._async.promote_chat_member(
                chat_id,
                user_id,
                can_change_info=can_change_info,
                can_post_messages=can_post_messages,
                can_edit_messages=can_edit_messages,
                can_delete_messages=can_delete_messages,
                can_manage_video_chats=can_manage_video_chats,
                can_invite_users=can_invite_users,
                can_restrict_members=can_restrict_members,
                **kwargs,
            )
        )

    def set_chat_photo(self, chat_id: str | int, photo: Any, **kwargs: Any) -> bool:
        """تغییر تصویر پروفایل گفتگو (متد ``setChatPhoto``)."""
        return self._run(self._async.set_chat_photo(chat_id, photo, **kwargs))

    def leave_chat(self, chat_id: str | int, **kwargs: Any) -> bool:
        """خروج بازو از گروه/کانال (متد ``leaveChat``)."""
        return self._run(self._async.leave_chat(chat_id, **kwargs))

    def get_chat(self, chat_id: str | int, **kwargs: Any) -> ChatFullInfo:
        """دریافت اطلاعات به‌روز گفتگو (متد ``getChat``)."""
        return self._run(self._async.get_chat(chat_id, **kwargs))

    def get_chat_administrators(self, chat_id: str | int, **kwargs: Any) -> list[ChatMember]:
        """دریافت فهرست مدیران گفتگو (متد ``getChatAdministrators``)."""
        return self._run(self._async.get_chat_administrators(chat_id, **kwargs))

    def get_chat_members_count(self, chat_id: str | int, **kwargs: Any) -> int:
        """دریافت تعداد اعضای گفتگو (متد ``getChatMembersCount``)."""
        return self._run(self._async.get_chat_members_count(chat_id, **kwargs))

    def get_chat_member(self, chat_id: str | int, user_id: int, **kwargs: Any) -> ChatMember:
        """دریافت اطلاعات یک عضو گفتگو (متد ``getChatMember``)."""
        return self._run(self._async.get_chat_member(chat_id, user_id, **kwargs))

    def pin_chat_message(self, chat_id: str | int, message_id: int, **kwargs: Any) -> bool:
        """سنجاق‌کردن پیام (متد ``pinChatMessage``)."""
        return self._run(self._async.pin_chat_message(chat_id, message_id, **kwargs))

    def unpin_chat_message(self, chat_id: str | int, message_id: int, **kwargs: Any) -> bool:
        """حذف سنجاق یک پیام مشخص (متد ``unPinChatMessage``)."""
        return self._run(self._async.unpin_chat_message(chat_id, message_id, **kwargs))

    def unpin_all_chat_messages(self, chat_id: str | int, **kwargs: Any) -> bool:
        """حذف سنجاق همه‌ی پیام‌ها (متد ``unpinAllChatMessages``)."""
        return self._run(self._async.unpin_all_chat_messages(chat_id, **kwargs))

    def set_chat_title(self, chat_id: str | int, title: str, **kwargs: Any) -> bool:
        """تغییر عنوان گفتگو (متد ``setChatTitle``)."""
        return self._run(self._async.set_chat_title(chat_id, title, **kwargs))

    def set_chat_description(self, chat_id: str | int, description: str, **kwargs: Any) -> bool:
        """تغییر توضیحات گروه/کانال (متد ``setChatDescription``)."""
        return self._run(self._async.set_chat_description(chat_id, description, **kwargs))

    def delete_chat_photo(self, chat_id: str | int, **kwargs: Any) -> bool:
        """حذف تصویر پروفایل گفتگو (متد ``deleteChatPhoto``)."""
        return self._run(self._async.delete_chat_photo(chat_id, **kwargs))

    def create_chat_invite_link(self, chat_id: str | int, **kwargs: Any) -> Any:
        """ایجاد لینک دعوت جدید (متد ``createChatInviteLink``)."""
        return self._run(self._async.create_chat_invite_link(chat_id, **kwargs))

    def revoke_chat_invite_link(self, chat_id: str | int, invite_link: str, **kwargs: Any) -> Any:
        """ابطال لینک عضویت و ساخت لینک جدید (متد ``revokeChatInviteLink``)."""
        return self._run(self._async.revoke_chat_invite_link(chat_id, invite_link, **kwargs))

    def export_chat_invite_link(self, chat_id: str | int, **kwargs: Any) -> Any:
        """ساخت/بازسازی لینک عضویت (متد ``exportChatInviteLink``)."""
        return self._run(self._async.export_chat_invite_link(chat_id, **kwargs))

    # ------------------------------------------------------------------ #
    # ویرایش و حذف پیام
    # ------------------------------------------------------------------ #
    def edit_message_text(
        self,
        chat_id: str | int,
        message_id: int,
        text: str,
        *,
        reply_markup: InlineKeyboardMarkup | None = None,
        **kwargs: Any,
    ) -> Message | bool:
        """ویرایش پیام متنی (متد ``editMessageText``)."""
        return self._run(
            self._async.edit_message_text(
                chat_id, message_id, text, reply_markup=reply_markup, **kwargs
            )
        )

    def edit_message_caption(
        self,
        chat_id: str | int,
        message_id: int,
        *,
        caption: str | None = None,
        reply_markup: InlineKeyboardMarkup | None = None,
        **kwargs: Any,
    ) -> Message | bool:
        """ویرایش زیرنویس پیام رسانه‌ای (متد ``editMessageCaption``)."""
        return self._run(
            self._async.edit_message_caption(
                chat_id, message_id, caption=caption, reply_markup=reply_markup, **kwargs
            )
        )

    def edit_message_reply_markup(
        self,
        chat_id: str | int,
        message_id: int,
        *,
        reply_markup: InlineKeyboardMarkup | None = None,
        **kwargs: Any,
    ) -> Message | bool:
        """ویرایش صفحه‌کلید پیام (متد ``editMessageReplyMarkup``)."""
        return self._run(
            self._async.edit_message_reply_markup(
                chat_id, message_id, reply_markup=reply_markup, **kwargs
            )
        )

    def delete_message(self, chat_id: str | int, message_id: int, **kwargs: Any) -> bool:
        """حذف پیام (متد ``deleteMessage``)."""
        return self._run(self._async.delete_message(chat_id, message_id, **kwargs))

    # ------------------------------------------------------------------ #
    # استیکرها
    # ------------------------------------------------------------------ #
    def upload_sticker_file(self, user_id: int, sticker: Any, **kwargs: Any) -> File:
        """آپلود فایل استیکر برای استفاده در متدهای بعدی (متد ``uploadStickerFile``)."""
        return self._run(self._async.upload_sticker_file(user_id, sticker, **kwargs))

    def create_new_sticker_set(
        self,
        user_id: int,
        name: str,
        title: str,
        sticker: Sequence[InputSticker],
        **kwargs: Any,
    ) -> bool:
        """ایجاد بسته‌ی استیکر جدید (متد ``createNewStickerSet``)."""
        return self._run(
            self._async.create_new_sticker_set(user_id, name, title, sticker, **kwargs)
        )

    def add_sticker_to_set(
        self, user_id: int, name: str, sticker: InputSticker, **kwargs: Any
    ) -> bool:
        """افزودن استیکر به یک بسته‌ی موجود (متد ``addStickerToSet``)."""
        return self._run(self._async.add_sticker_to_set(user_id, name, sticker, **kwargs))

    # ------------------------------------------------------------------ #
    # پرداخت (کیف‌پول بله)
    # ------------------------------------------------------------------ #
    def send_invoice(
        self,
        chat_id: str | int,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        prices: Sequence[LabeledPrice],
        *,
        photo_url: str | None = None,
        reply_to_message_id: int | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال درخواست پول/صورتحساب (متد ``sendInvoice``)."""
        return self._run(
            self._async.send_invoice(
                chat_id,
                title,
                description,
                payload,
                provider_token,
                prices,
                photo_url=photo_url,
                reply_to_message_id=reply_to_message_id,
                **kwargs,
            )
        )

    def create_invoice_link(
        self,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        prices: Sequence[LabeledPrice],
        **kwargs: Any,
    ) -> str:
        """ایجاد لینک پرداخت برای مینی‌اپ (متد ``createInvoiceLink``)."""
        return self._run(
            self._async.create_invoice_link(
                title, description, payload, provider_token, prices, **kwargs
            )
        )

    def answer_pre_checkout_query(
        self,
        pre_checkout_query_id: str,
        ok: bool,
        *,
        error_message: str | None = None,
        **kwargs: Any,
    ) -> bool:
        """پاسخ به درخواست بررسی پیش از پرداخت (متد ``answerPreCheckoutQuery``)."""
        return self._run(
            self._async.answer_pre_checkout_query(
                pre_checkout_query_id, ok, error_message=error_message, **kwargs
            )
        )

    def inquire_transaction(self, transaction_id: str, **kwargs: Any) -> Transaction:
        """استعلام وضعیت یک تراکنش (متد اختصاصی بله ``inquireTransaction``)."""
        return self._run(self._async.inquire_transaction(transaction_id, **kwargs))

    # ------------------------------------------------------------------ #
    # وب‌هوک و دریافت آپدیت‌ها
    # ------------------------------------------------------------------ #
    def set_webhook(self, url: str, **kwargs: Any) -> bool:
        """تنظیم وب‌هوک (متد ``setWebhook``)."""
        return self._run(self._async.set_webhook(url, **kwargs))

    def delete_webhook(self, **kwargs: Any) -> bool:
        """حذف وب‌هوک (متد ``deleteWebhook``)."""
        return self._run(self._async.delete_webhook(**kwargs))

    def get_webhook_info(self, **kwargs: Any) -> WebhookInfo:
        """دریافت وضعیت فعلی وب‌هوک (متد ``getWebhookInfo``)."""
        return self._run(self._async.get_webhook_info(**kwargs))

    def get_updates(
        self,
        *,
        offset: int | None = None,
        limit: int | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> list[Update]:
        """دریافت آپدیت‌ها با long polling (متد ``getUpdates``)."""
        return self._run(
            self._async.get_updates(offset=offset, limit=limit, timeout=timeout, **kwargs)
        )

    # ------------------------------------------------------------------ #
    # چرخه‌ی عمر
    # ------------------------------------------------------------------ #
    def close(self) -> None:
        """بستن کلاینت و توقف حلقه‌ی پس‌زمینه."""
        if self._closed:
            return
        try:
            self._portal.run(self._async.aclose())
        finally:
            self._closed = True
            self._portal.close()

    @property
    def is_closed(self) -> bool:
        """آیا کلاینت بسته شده است؟"""
        return self._closed

    def __enter__(self) -> BaleClient:
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def __repr__(self) -> str:  # pragma: no cover - ابزاری
        mode = "business" if self.business else "bot"
        return f"BaleClient(base={self.base_url!r}, mode={mode!r})"
