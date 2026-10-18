"""کلاینت ناهمگام API بازو — پوشش کامل مستندات رسمی.

این کلاس همه‌ی متدهای مستندشده در «مستندات بازوی بله» را با امضا و نوع‌بندی کامل
ارائه می‌دهد. نتیجه‌ی هر متد به شیء تایپ‌شده تبدیل می‌شود (برای مثال
``sendMessage`` خروجی‌اش یک :class:`~baleRobot.types.messages.Message` است).

.. code-block:: python

    import asyncio
    from baleRobot import AsyncBaleClient

    async def main() -> None:
        async with AsyncBaleClient("TOKEN") as client:
            me = await client.get_me()
            print(me.first_name, me.username)

    asyncio.run(main())

نکته‌های مهم:

* همه‌ی متدها پارامتر اختیاری ``**kwargs`` دارند تا پارامترهای تکمیلی/جدید API
  بازو (مثل ``parse_mode`` یا ``allowed_updates``) نیز قابل ارسال باشند.
* فایل‌ها می‌توانند ``file_id`` (رشته)، URL (رشته)، :class:`pathlib.Path`،
  ``bytes`` یا :class:`~baleRobot.types.input.InputFile` باشند.
* محدودیت نرخ ارسال (429) به صورت شفاف به خطای :class:`~baleRobot.errors.TooManyRequests`
  با فیلد ``retry_after`` تبدیل می‌شود؛ با ``auto_retry=True`` (پیش‌فرض) کتابخانه
  خودش منتظر می‌ماند و تلاش می‌کند.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping, Sequence
from typing import Any

import httpx

from ._serializers import build_url, dump_params
from ._version import __version__
from .errors import (
    BaleError,
    NetworkError,
    ServerError,
    TimedOut,
    TooManyRequests,
    build_api_error,
)
from .types.chat_members import ChatMember
from .types.files import File
from .types.input import (
    InputMediaAnimation,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    InputSticker,
)
from .types.keyboards import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .types.messages import Message, MessageId
from .types.payments import LabeledPrice, Transaction
from .types.updates import Update, WebhookInfo
from .types.users import ChatFullInfo, ResponseParameters, User

__all__ = ["AsyncBaleClient"]

#: آدرس پایه‌ی API بازو
DEFAULT_BASE_URL = "https://tapi.bale.ai"

InputMedia = (
    InputMediaPhoto | InputMediaVideo | InputMediaAnimation | InputMediaAudio | InputMediaDocument
)
ReplyMarkup = InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | dict | list


def _message_or_bool(result: Any) -> Message | bool:
    """برخی متدهای ویرایش پیام هم Message و هم True برمی‌گردانند."""
    if isinstance(result, Mapping):
        return Message.from_dict(result)
    return bool(result)


class AsyncBaleClient:
    """کلاینت ناهمگام API بازو.

    Args:
        token: توکن احراز هویت بازو که از @botfather دریافت کرده‌اید.
        business: اگر ``True`` باشد، درخواست‌ها با Base URL کسب‌وکاری
            (``/business/bot<token>/…``) ارسال می‌شوند که سهمیه‌ی نرخ درخواست
            مستقل و بالاتری دارد.
        base_url: آدرس پایه‌ی API؛ فقط در صورت نیاز تغییر دهید.
        timeout: مهلت کل هر درخواست بر حسب ثانیه.
        connect_timeout: مهلت برقراری اتصال بر حسب ثانیه.
        auto_retry: تلاش خودکار هنگام خطاهای موقت (429 و 5xx) و قطعی اتصال.
        max_retries: حداکثر تعداد تلاش مجدد (فقط وقتی ``auto_retry`` فعال است).
        retry_backoff: مکث اولیه‌ی تلاش مجدد بر حسب ثانیه؛ در هر تلاش دو برابر
            می‌شود.
        max_retry_delay: سقف مکث بین تلاش‌ها بر حسب ثانیه.
        headers: هدرهای دلخواه HTTP.
        transport: ترنسپورت httpx سفارشی (برای تست با ``httpx.MockTransport``).
        httpx_client: یک شیء ``httpx.AsyncClient`` آماده؛ در صورت استفاده،
            مدیریت عمر آن بر عهده‌ی شماست.
    """

    #: آدرس پایه‌ی پیش‌فرض API بازو
    base_url: str = DEFAULT_BASE_URL

    def __init__(
        self,
        token: str,
        *,
        business: bool = False,
        base_url: str | None = None,
        timeout: float | httpx.Timeout | None = 60.0,
        connect_timeout: float = 10.0,
        auto_retry: bool = True,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
        max_retry_delay: float = 60.0,
        headers: Mapping[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not token or not isinstance(token, str):
            raise ValueError("توکن بازو (token) اجباری است و نمی‌تواند خالی باشد")

        self._token = token
        self._business = bool(business)
        self._base_url = (base_url or self.base_url).rstrip("/")
        self._auto_retry = bool(auto_retry)
        self._max_retries = max(0, int(max_retries))
        self._retry_backoff = float(retry_backoff)
        self._max_retry_delay = float(max_retry_delay)
        self._connect_timeout = float(connect_timeout)

        if isinstance(timeout, httpx.Timeout):
            self._timeout: httpx.Timeout | None = timeout
        elif timeout is None:
            self._timeout = None
        else:
            self._timeout = httpx.Timeout(float(timeout), connect=self._connect_timeout)

        default_headers = {"User-Agent": f"baleRobot/{__version__}"}
        if headers:
            default_headers.update(headers)

        self._owns_client = httpx_client is None
        self._http = httpx_client or httpx.AsyncClient(
            headers=default_headers,
            timeout=self._timeout,
            follow_redirects=True,
            transport=transport,
        )
        if httpx_client is not None and headers:
            self._http.headers.update(headers)

    # ------------------------------------------------------------------ #
    # مشخصات کلاینت
    # ------------------------------------------------------------------ #
    @property
    def token(self) -> str:
        """توکن بازو."""
        return self._token

    @property
    def business(self) -> bool:
        """آیا درخواست‌ها با API کسب‌وکاری ارسال می‌شوند؟"""
        return self._business

    @property
    def http(self) -> httpx.AsyncClient:
        """شیء ``httpx.AsyncClient`` زیرین (برای استفاده‌های پیشرفته)."""
        return self._http

    def _url(self, method: str) -> str:
        return build_url(self._base_url, self._token, method, business=self._business)

    # ----------------------------------------------------------------─ #
    # هسته‌ی درخواست
    # ------------------------------------------------------------------ #
    async def _request(
        self,
        method: str,
        *,
        _request_timeout: float | httpx.Timeout | None = None,
        **params: Any,
    ) -> Any:
        """ارسال یک درخواست به API و برگرداندن فیلد ``result`` پاسخ.

        درخواست به صورت JSON ارسال می‌شود؛ اگر پارامتری فایل قابل آپلود داشته
        باشد، به صورت ``multipart/form-data`` (و برای فایل‌های توکار با
        ``attach://``) ارسال می‌گردد.
        """
        url = self._url(method)
        data, uploads = dump_params(params)

        files: dict[str, tuple[str, bytes, str | None]] | None = None
        if uploads:
            files = {name: upload.as_httpx_files() for name, upload in uploads.items()}
            payload: Any = {
                key: json.dumps(value, ensure_ascii=False)
                if isinstance(value, (dict, list))
                else str(value)
                for key, value in data.items()
            }
        else:
            payload = data

        attempt = 0
        while True:
            retry_after: int | None = None
            try:
                if files is not None:
                    response = await self._http.post(
                        url, data=payload, files=files, timeout=_request_timeout
                    )
                else:
                    response = await self._http.post(url, json=payload, timeout=_request_timeout)
                return self._parse_response(response, method)
            except _ApiErrorResponse as signal:
                error: BaleError = signal.error
                retry_after = error.retry_after if isinstance(error, TooManyRequests) else None
            except httpx.TimeoutException as exc:
                error = TimedOut(f"مهلت درخواست {method} به پایان رسید: {exc}")
            except httpx.HTTPError as exc:
                error = NetworkError(f"خطای شبکه در درخواست {method}: {exc}")

            if self._can_retry(attempt) and self._is_retryable(error):
                await asyncio.sleep(self._retry_delay(attempt, retry_after))
                attempt += 1
                continue
            raise error

    def _parse_response(self, response: httpx.Response, method: str) -> Any:
        """اعتبارسنجی و تفسیر پاسخ HTTP سرور بازو.

        در صورت موفقیت، فیلد ``result`` برمی‌گردد؛ در غیر این صورت
        :class:`_ApiErrorResponse` پرتاب می‌شود تا تصمیم تلاش مجدد در
        :meth:`_request` گرفته شود.
        """
        try:
            payload = response.json()
        except ValueError:
            raise NetworkError(
                f"پاسخ نامعتبر از سرور بازو برای {method} "
                f"(HTTP {response.status_code}): {response.text[:200]!r}"
            ) from None

        if not isinstance(payload, dict):
            raise NetworkError(f"ساختار پاسخ {method} غیرمنتظره است: {type(payload)!r}")

        if payload.get("ok"):
            return payload.get("result")

        error_code = payload.get("error_code") or response.status_code
        description = str(payload.get("description") or "")
        raw_parameters = payload.get("parameters")
        parameters = (
            ResponseParameters.from_dict(raw_parameters)
            if isinstance(raw_parameters, Mapping)
            else None
        )
        raise _ApiErrorResponse(build_api_error(error_code, description, parameters))

    def _can_retry(self, attempt: int) -> bool:
        return self._auto_retry and attempt < self._max_retries

    @staticmethod
    def _is_retryable(error: BaleError) -> bool:
        """خطاهای موقت: محدودیت نرخ، خطای سرور و مشکلات موقت شبکه."""
        return isinstance(error, (TooManyRequests, ServerError, NetworkError))

    def _retry_delay(self, attempt: int, retry_after: int | None) -> float:
        base = float(retry_after) if retry_after else self._retry_backoff * (2**attempt)
        return max(0.0, min(base, self._max_retry_delay))

    # ------------------------------------------------------------------ #
    # دانلود فایل
    # ------------------------------------------------------------------ #
    def file_url(self, file_path: str) -> str:
        """لینک مستقیم دانلود یک فایل (اعتبار: یک ساعت).

        Args:
            file_path: فیلد ``file_path`` شیء :class:`~baleRobot.types.files.File`.
        """
        return f"{self._base_url}/file/bot{self._token}/{file_path.lstrip('/')}"

    async def get_file(self, file_id: str, **kwargs: Any) -> File:
        """دریافت اطلاعات پایه‌ی یک فایل و آماده‌سازی برای دانلود (متد ``getFile``).

        حداکثر حجم قابل دانلود ۲۰ مگابایت است.

        Args:
            file_id: شناسه‌ی فایل.

        Returns:
            شیء :class:`~baleRobot.types.files.File`؛ با :meth:`file_url` لینک
            دانلود ساخته می‌شود.
        """
        result = await self._request("getFile", file_id=file_id, **kwargs)
        return File.from_dict(result)

    async def download_file(
        self,
        file: str | File,
        *,
        destination: str | None = None,
        timeout: float | None = 300.0,
        **kwargs: Any,
    ) -> bytes | str:
        """دانلود کامل یک فایل.

        Args:
            file: ``file_id`` یا شیء :class:`~baleRobot.types.files.File`.
            destination: در صورت تعیین، فایل در این مسیر ذخیره و همان مسیر
                برگردانده می‌شود؛ در غیر این صورت محتوای باینری برمی‌گردد.
            timeout: مهلت دانلود بر حسب ثانیه.

        Returns:
            محتوای فایل (``bytes``) یا مسیر ذخیره‌سازی (``str``).
        """
        info = file if isinstance(file, File) else await self.get_file(file, **kwargs)
        if not info.file_path:
            raise NetworkError("سرور file_path برنگرداند؛ امکان دانلود وجود ندارد")
        url = self.file_url(info.file_path)
        try:
            response = await self._http.get(url, timeout=timeout)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise TimedOut(f"مهلت دانلود فایل به پایان رسید: {exc}") from exc
        except httpx.HTTPError as exc:
            raise NetworkError(f"خطا در دانلود فایل: {exc}") from exc

        if destination:
            with open(destination, "wb") as handle:
                handle.write(response.content)
            return destination
        return response.content

    # ------------------------------------------------------------------ #
    # متدهای عمومی بازو
    # ------------------------------------------------------------------ #
    async def get_me(self, **kwargs: Any) -> User:
        """تست توکن و دریافت اطلاعات پایه‌ی بازو (متد ``getMe``)."""
        result = await self._request("getMe", **kwargs)
        return User.from_dict(result)

    async def send_message(
        self,
        chat_id: str | int,
        text: str,
        *,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال پیام متنی (متد ``sendMessage``).

        متن باید بین ۱ تا ۴۰۹۶ کاراکتر باشد. قالب‌بندی متن در بله به شکل
        Markdown است؛ از کمک‌تابع‌های ماژول :mod:`baleRobot.formatting` استفاده
        کنید.

        Args:
            chat_id: شناسه‌ی گفتگو یا نام‌کاربری کانال با فرمت ``@channelusername``.
            text: متن پیام.
            reply_to_message_id: شناسه‌ی پیامی که این پیام پاسخ آن است.
            reply_markup: صفحه‌کلید inline، صفحه‌کلید پاسخ یا دستور حذف صفحه‌کلید.

        Returns:
            پیام ارسال‌شده.
        """
        result = await self._request(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
            **kwargs,
        )
        return Message.from_dict(result)

    async def forward_message(
        self,
        chat_id: str | int,
        from_chat_id: str | int,
        message_id: int,
        **kwargs: Any,
    ) -> Message:
        """بازارسال (فوروارد) هر نوع پیام (متد ``forwardMessage``)."""
        result = await self._request(
            "forwardMessage",
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_id=message_id,
            **kwargs,
        )
        return Message.from_dict(result)

    async def copy_message(
        self,
        chat_id: str | int,
        from_chat_id: str | int,
        message_id: int,
        **kwargs: Any,
    ) -> MessageId:
        """کپی پیام بدون لینک به پیام اصلی (متد ``copyMessage``).

        پیام‌های سرویس و رسید پرداخت قابل کپی نیستند.
        """
        result = await self._request(
            "copyMessage",
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_id=message_id,
            **kwargs,
        )
        return MessageId.from_dict(result)

    async def send_photo(
        self,
        chat_id: str | int,
        photo: Any,
        *,
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال تصویر (متد ``sendPhoto``).

        ``photo`` می‌تواند ``file_id``، URL یا فایل محلی (:class:`pathlib.Path` /
        :class:`~baleRobot.types.input.InputFile`) باشد. زیرنویس تا ۴۰۹۶ کاراکتر.
        """
        result = await self._request(
            "sendPhoto",
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
            **kwargs,
        )
        return Message.from_dict(result)

    async def send_audio(
        self,
        chat_id: str | int,
        audio: Any,
        *,
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال فایل صوتی (متد ``sendAudio``)؛ فرمت پشتیبانی‌شده ‎.MP3‎ یا ‎.M4A‎ (تا ۵۰ مگابایت).

        برای ارسال پیام صوتی (Voice) از :meth:`send_voice` استفاده کنید.
        """
        result = await self._request(
            "sendAudio",
            chat_id=chat_id,
            audio=audio,
            caption=caption,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
            **kwargs,
        )
        return Message.from_dict(result)

    async def send_document(
        self,
        chat_id: str | int,
        document: Any,
        *,
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال سند/فایل عمومی (متد ``sendDocument``؛ حداکثر ۵۰ مگابایت)."""
        result = await self._request(
            "sendDocument",
            chat_id=chat_id,
            document=document,
            caption=caption,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
            **kwargs,
        )
        return Message.from_dict(result)

    async def send_video(
        self,
        chat_id: str | int,
        video: Any,
        *,
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال ویدیو (متد ``sendVideo``؛ کلاینت‌های بله از MPEG4 پشتیبانی می‌کنند)."""
        result = await self._request(
            "sendVideo",
            chat_id=chat_id,
            video=video,
            caption=caption,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
            **kwargs,
        )
        return Message.from_dict(result)

    async def send_animation(
        self,
        chat_id: str | int,
        animation: Any,
        *,
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال انیمیشن (GIF یا ویدیوی H.264/MPEG-4 AVC بدون صدا)."""
        result = await self._request(
            "sendAnimation",
            chat_id=chat_id,
            animation=animation,
            caption=caption,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
            **kwargs,
        )
        return Message.from_dict(result)

    async def send_voice(
        self,
        chat_id: str | int,
        voice: Any,
        *,
        caption: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: ReplyMarkup | None = None,
        **kwargs: Any,
    ) -> Message:
        """ارسال پیام صوتی (متد ``sendVoice``).

        برای ارسال با URL، فایل باید از نوع ``audio/ogg`` و حداکثر ۱ مگابایت باشد.
        """
        result = await self._request(
            "sendVoice",
            chat_id=chat_id,
            voice=voice,
            caption=caption,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
            **kwargs,
        )
        return Message.from_dict(result)

    async def send_media_group(
        self,
        chat_id: str | int,
        media: Sequence[InputMedia],
        *,
        reply_to_message_id: int | None = None,
        **kwargs: Any,
    ) -> list[Message]:
        """ارسال آلبومی از تصاویر/ویدیوها/اسناد/صوت (متد ``sendMediaGroup``).

        اسناد و فایل‌های صوتی فقط با پیام‌هایی از نوع خود در یک آلبوم می‌آیند.
        فایل‌های محلی داخل :class:`~baleRobot.types.input.InputMedia*`
        به صورت خودکار با مکانیزم ``attach://`` آپلود می‌شوند.

        Args:
            chat_id: شناسه‌ی گفتگو.
            media: آرایه‌ای از InputMediaPhoto/Video/Audio/Document.
        """
        result = await self._request(
            "sendMediaGroup",
            chat_id=chat_id,
            media=list(media),
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        )
        return [Message.from_dict(item) for item in (result or [])]

    async def send_location(
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
        """ارسال موقعیت روی نقشه (متد ``sendLocation``).

        ``horizontal_accuracy`` شعاع عدم قطعیت به متر (۰ تا ۱۵۰۰) است.
        """
        result = await self._request(
            "sendLocation",
            chat_id=chat_id,
            latitude=latitude,
            longitude=longitude,
            horizontal_accuracy=horizontal_accuracy,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
            **kwargs,
        )
        return Message.from_dict(result)

    async def send_contact(
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
        result = await self._request(
            "sendContact",
            chat_id=chat_id,
            phone_number=str(phone_number),
            first_name=first_name,
            last_name=last_name,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
            **kwargs,
        )
        return Message.from_dict(result)

    async def send_chat_action(
        self,
        chat_id: str | int,
        action: str | Any,
        **kwargs: Any,
    ) -> bool:
        """نمایش وضعیت عملیات بازو برای کاربر (متد ``sendChatAction``).

        این وضعیت حداکثر ۶ ثانیه نمایش داده می‌شود. مقادیر مجاز از
        :class:`~baleRobot.constants.ChatAction`: ``typing``، ``upload_photo``،
        ``record_video``، ``upload_video``، ``record_voice``، ``upload_voice`` و
        ``choose_sticker``.
        """
        result = await self._request("sendChatAction", chat_id=chat_id, action=action, **kwargs)
        return bool(result)

    async def answer_callback_query(
        self,
        callback_query_id: str,
        *,
        text: str | None = None,
        show_alert: bool | None = None,
        **kwargs: Any,
    ) -> bool:
        """پاسخ به فراخوانی دکمه‌ی inline (متد ``answerCallbackQuery``).

        .. important::
            حتی اگر نیازی به نمایش پیام ندارید، این متد را فراخوانی کنید؛ در غیر
            این صورت دکمه در حالت انتظار باقی می‌ماند. متن حداکثر ۲۰۰ کاراکتر.

        .. note::
            اگر ``callback_query_id`` با عدد ۱ شروع شود، کاربر از نسخه‌ی قدیمی
            کلاینت استفاده می‌کند و این قابلیت را ندارد.
        """
        result = await self._request(
            "answerCallbackQuery",
            callback_query_id=callback_query_id,
            text=text,
            show_alert=show_alert,
            **kwargs,
        )
        return bool(result)

    async def ask_review(
        self,
        user_id: int,
        delay_seconds: int,
        **kwargs: Any,
    ) -> bool:
        """نمایش فرم رضایت‌سنجی بازو به کاربر (متد اختصاصی بله ``askReview``).

        بهترین زمان فراخوانی، بلافاصله پس از ارائه‌ی خدمت مفید است. نمایش قطعی
        فرم تضمین نمی‌شود و فرم فقط وقتی نمایش داده می‌شود که کاربر در صفحه‌ی
        بازو (یا مینی‌اپ آن) حاضر باشد.

        Args:
            user_id: شناسه‌ی کاربر هدف.
            delay_seconds: تأخیر تا نمایش فرم بر حسب ثانیه.
        """
        result = await self._request(
            "askReview", user_id=user_id, delay_seconds=delay_seconds, **kwargs
        )
        return bool(result)

    # ------------------------------------------------------------------ #
    # مدیریت گفتگو و اعضا
    # ------------------------------------------------------------------ #
    async def ban_chat_member(
        self,
        chat_id: str | int,
        user_id: int,
        **kwargs: Any,
    ) -> bool:
        """مسدودکردن کاربر در گروه/کانال (متد ``banChatMember``).

        بازو باید مدیر گفتگو باشد. کاربر مسدودشده تا رفع مسدودیت امکان بازگشت
        از طریق لینک دعوت را ندارد.
        """
        result = await self._request("banChatMember", chat_id=chat_id, user_id=user_id, **kwargs)
        return bool(result)

    async def unban_chat_member(
        self,
        chat_id: str | int,
        user_id: int,
        *,
        only_if_banned: bool | None = None,
        **kwargs: Any,
    ) -> bool:
        """رفع مسدودیت کاربر (متد ``unbanChatMember``).

        با پیش‌فرض، کاربر از گفتگو هم حذف می‌شود؛ برای جلوگیری از این کار
        ``only_if_banned=True`` بگذارید.
        """
        result = await self._request(
            "unbanChatMember",
            chat_id=chat_id,
            user_id=user_id,
            only_if_banned=only_if_banned,
            **kwargs,
        )
        return bool(result)

    async def promote_chat_member(
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
        """ارتقا/تنزل سطح کاربر (متد ``promoteChatMember``).

        برای تنزل، همه‌ی پارامترهای بولین را ``False`` بفرستید.
        """
        result = await self._request(
            "promoteChatMember",
            chat_id=chat_id,
            user_id=user_id,
            can_change_info=can_change_info,
            can_post_messages=can_post_messages,
            can_edit_messages=can_edit_messages,
            can_delete_messages=can_delete_messages,
            can_manage_video_chats=can_manage_video_chats,
            can_invite_users=can_invite_users,
            can_restrict_members=can_restrict_members,
            **kwargs,
        )
        return bool(result)

    async def set_chat_photo(self, chat_id: str | int, photo: Any, **kwargs: Any) -> bool:
        """تغییر تصویر پروفایل گفتگو (متد ``setChatPhoto``؛ فقط آپلود multipart)."""
        result = await self._request("setChatPhoto", chat_id=chat_id, photo=photo, **kwargs)
        return bool(result)

    async def leave_chat(self, chat_id: str | int, **kwargs: Any) -> bool:
        """خروج بازو از گروه/کانال (متد ``leaveChat``)."""
        result = await self._request("leaveChat", chat_id=chat_id, **kwargs)
        return bool(result)

    async def get_chat(self, chat_id: str | int, **kwargs: Any) -> ChatFullInfo:
        """دریافت اطلاعات به‌روز گفتگو (متد ``getChat``)."""
        result = await self._request("getChat", chat_id=chat_id, **kwargs)
        return ChatFullInfo.from_dict(result)

    async def get_chat_administrators(self, chat_id: str | int, **kwargs: Any) -> list[ChatMember]:
        """دریافت فهرست مدیران گفتگو (متد ``getChatAdministrators``)."""
        result = await self._request("getChatAdministrators", chat_id=chat_id, **kwargs)
        return [ChatMember.from_dict(item) for item in (result or [])]

    async def get_chat_members_count(self, chat_id: str | int, **kwargs: Any) -> int:
        """دریافت تعداد اعضای گفتگو (متد ``getChatMembersCount``)."""
        result = await self._request("getChatMembersCount", chat_id=chat_id, **kwargs)
        return int(result)

    async def get_chat_member(self, chat_id: str | int, user_id: int, **kwargs: Any) -> ChatMember:
        """دریافت اطلاعات یک عضو گفتگو (متد ``getChatMember``).

        بازو باید مدیر گفتگو باشد. نوع شیء برگشتی بر اساس ``status`` یکی از
        زیرکلاس‌های :class:`~baleRobot.types.chat_members.ChatMember` است.
        """
        result = await self._request("getChatMember", chat_id=chat_id, user_id=user_id, **kwargs)
        return ChatMember.from_dict(result)

    async def pin_chat_message(self, chat_id: str | int, message_id: int, **kwargs: Any) -> bool:
        """سنجاق‌کردن پیام (متد ``pinChatMessage``)."""
        result = await self._request(
            "pinChatMessage", chat_id=chat_id, message_id=message_id, **kwargs
        )
        return bool(result)

    async def unpin_chat_message(self, chat_id: str | int, message_id: int, **kwargs: Any) -> bool:
        """حذف سنجاق یک پیام مشخص (متد ``unPinChatMessage``)."""
        result = await self._request(
            "unPinChatMessage", chat_id=chat_id, message_id=message_id, **kwargs
        )
        return bool(result)

    async def unpin_all_chat_messages(self, chat_id: str | int, **kwargs: Any) -> bool:
        """حذف سنجاق همه‌ی پیام‌ها (متد ``unpinAllChatMessages``)."""
        result = await self._request("unpinAllChatMessages", chat_id=chat_id, **kwargs)
        return bool(result)

    async def set_chat_title(self, chat_id: str | int, title: str, **kwargs: Any) -> bool:
        """تغییر عنوان گفتگو (متد ``setChatTitle``؛ در چت خصوصی کاربرد ندارد)."""
        result = await self._request("setChatTitle", chat_id=chat_id, title=title, **kwargs)
        return bool(result)

    async def set_chat_description(
        self, chat_id: str | int, description: str, **kwargs: Any
    ) -> bool:
        """تغییر توضیحات گروه/کانال (متد ``setChatDescription``)."""
        result = await self._request(
            "setChatDescription", chat_id=chat_id, description=description, **kwargs
        )
        return bool(result)

    async def delete_chat_photo(self, chat_id: str | int, **kwargs: Any) -> bool:
        """حذف تصویر پروفایل گفتگو (متد ``deleteChatPhoto``)."""
        result = await self._request("deleteChatPhoto", chat_id=chat_id, **kwargs)
        return bool(result)

    async def create_chat_invite_link(self, chat_id: str | int, **kwargs: Any) -> Any:
        """ایجاد لینک دعوت جدید برای گروه/کانال (متد ``createChatInviteLink``).

        خروجی مستندنشده است؛ معمولاً رشته‌ی لینک یا شیء حاوی آن برمی‌گردد،
        بنابراین مقدار خام برمی‌گردد.
        """
        return await self._request("createChatInviteLink", chat_id=chat_id, **kwargs)

    async def revoke_chat_invite_link(
        self, chat_id: str | int, invite_link: str, **kwargs: Any
    ) -> Any:
        """ابطال لینک عضویت و ساخت لینک جدید (متد ``revokeChatInviteLink``)."""
        return await self._request(
            "revokeChatInviteLink", chat_id=chat_id, invite_link=invite_link, **kwargs
        )

    async def export_chat_invite_link(self, chat_id: str | int, **kwargs: Any) -> Any:
        """ساخت (و در صورت وجود، ابطال و ساخت مجدد) لینک عضویت (متد ``exportChatInviteLink``)."""
        return await self._request("exportChatInviteLink", chat_id=chat_id, **kwargs)

    # ------------------------------------------------------------------ #
    # ویرایش و حذف پیام
    # ------------------------------------------------------------------ #
    async def edit_message_text(
        self,
        chat_id: str | int,
        message_id: int,
        text: str,
        *,
        reply_markup: InlineKeyboardMarkup | None = None,
        **kwargs: Any,
    ) -> Message | bool:
        """ویرایش پیام متنی (متد ``editMessageText``؛ متن ۱ تا ۴۰۹۶ کاراکتر)."""
        result = await self._request(
            "editMessageText",
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs,
        )
        return _message_or_bool(result)

    async def edit_message_caption(
        self,
        chat_id: str | int,
        message_id: int,
        *,
        caption: str | None = None,
        reply_markup: InlineKeyboardMarkup | None = None,
        **kwargs: Any,
    ) -> Message | bool:
        """ویرایش زیرنویس پیام رسانه‌ای (متد ``editMessageCaption``)."""
        result = await self._request(
            "editMessageCaption",
            chat_id=chat_id,
            message_id=message_id,
            caption=caption,
            reply_markup=reply_markup,
            **kwargs,
        )
        return _message_or_bool(result)

    async def edit_message_reply_markup(
        self,
        chat_id: str | int,
        message_id: int,
        *,
        reply_markup: InlineKeyboardMarkup | None = None,
        **kwargs: Any,
    ) -> Message | bool:
        """ویرایش صفحه‌کلید پیام بدون تغییر محتوا (متد ``editMessageReplyMarkup``)."""
        result = await self._request(
            "editMessageReplyMarkup",
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
            **kwargs,
        )
        return _message_or_bool(result)

    async def delete_message(self, chat_id: str | int, message_id: int, **kwargs: Any) -> bool:
        """حذف پیام (متد ``deleteMessage``).

        پیام فقط تا ۴۸ ساعت پس از ارسال قابل حذف است و بازو باید مجوز لازم را
        داشته باشد.
        """
        result = await self._request(
            "deleteMessage", chat_id=chat_id, message_id=message_id, **kwargs
        )
        return bool(result)

    # ------------------------------------------------------------------ #
    # استیکرها
    # ------------------------------------------------------------------ #
    async def upload_sticker_file(self, user_id: int, sticker: Any, **kwargs: Any) -> File:
        """آپلود فایل استیکر برای استفاده در متدهای بعدی (متد ``uploadStickerFile``).

        فرمت‌های مجاز: ‎.WEBP‎، ‎.PNG‎، ‎.TGS‎ و ‎.WEBM‎.
        """
        result = await self._request(
            "uploadStickerFile", user_id=user_id, sticker=sticker, **kwargs
        )
        return File.from_dict(result)

    async def create_new_sticker_set(
        self,
        user_id: int,
        name: str,
        title: str,
        sticker: Sequence[InputSticker],
        **kwargs: Any,
    ) -> bool:
        """ایجاد بسته‌ی استیکر جدید (متد ``createNewStickerSet``).

        ``name`` باید با حرف شروع شود، شامل حروف انگلیسی/عدد/``_`` باشد و با
        ``by_bot_username_`` ختم شود (حساس به بزرگ/کوچک).
        """
        result = await self._request(
            "createNewStickerSet",
            user_id=user_id,
            name=name,
            title=title,
            sticker=list(sticker),
            **kwargs,
        )
        return bool(result)

    async def add_sticker_to_set(
        self,
        user_id: int,
        name: str,
        sticker: InputSticker,
        **kwargs: Any,
    ) -> bool:
        """افزودن استیکر به یک بسته‌ی موجود (متد ``addStickerToSet``).

        قالب استیکر جدید باید با بقیه‌ی استیکرهای بسته یکسان باشد.
        """
        result = await self._request(
            "addStickerToSet", user_id=user_id, name=name, sticker=sticker, **kwargs
        )
        return bool(result)

    # ------------------------------------------------------------------ #
    # پرداخت (کیف‌پول بله)
    # ------------------------------------------------------------------ #
    async def send_invoice(
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
        """ارسال درخواست پول/صورتحساب (متد ``sendInvoice``).

        مبالغ به ریال و عدد صحیح هستند. توکن پرداخت را از @botfather بگیرید؛
        برای تست می‌توان از ``WALLET-TEST-1111111111111111`` استفاده کرد.

        Args:
            title: نام محصول (۱ تا ۳۲ کاراکتر).
            description: توصیف محصول (۱ تا ۲۵۵ کاراکتر).
            payload: داده‌ی دلخواه شما که در ``SuccessfulPayment`` برمی‌گردد
                (۱ تا ۱۲۸ بایت؛ برای کاربر نمایش داده نمی‌شود).
            provider_token: توکن پرداخت کیف‌پولی.
            prices: اقلام صورتحساب؛ مجموع آن‌ها مبلغ نهایی است.
        """
        result = await self._request(
            "sendInvoice",
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            prices=list(prices),
            photo_url=photo_url,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        )
        return Message.from_dict(result)

    async def create_invoice_link(
        self,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        prices: Sequence[LabeledPrice],
        **kwargs: Any,
    ) -> str:
        """ایجاد لینک پرداخت برای استفاده در مینی‌اپ (متد ``createInvoiceLink``).

        خروجی را بدون تغییر به متد ``openInvoice`` مینی‌اپ پاس دهید.
        """
        result = await self._request(
            "createInvoiceLink",
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            prices=list(prices),
            **kwargs,
        )
        return str(result)

    async def answer_pre_checkout_query(
        self,
        pre_checkout_query_id: str,
        ok: bool,
        *,
        error_message: str | None = None,
        **kwargs: Any,
    ) -> bool:
        """پاسخ به درخواست بررسی پیش از پرداخت (متد ``answerPreCheckoutQuery``).

        .. important::
            بازو باید حداکثر ظرف ۱۰ ثانیه پاسخ دهد، وگرنه پرداخت لغو می‌شود.
            اگر ``ok=False`` باشد، ``error_message`` الزامی است.
        """
        if not ok and not error_message:
            raise ValueError("با ok=False باید error_message نیز ارسال شود")
        result = await self._request(
            "answerPreCheckoutQuery",
            pre_checkout_query_id=pre_checkout_query_id,
            ok=ok,
            error_message=error_message,
            **kwargs,
        )
        return bool(result)

    async def inquire_transaction(self, transaction_id: str, **kwargs: Any) -> Transaction:
        """استعلام وضعیت یک تراکنش (متد اختصاصی بله ``inquireTransaction``).

        وضعیت‌های ممکن: ``pending``، ``paid``، ``failed`` و ``rejected``.
        """
        result = await self._request("inquireTransaction", transaction_id=transaction_id, **kwargs)
        return Transaction.from_dict(result)

    # ------------------------------------------------------------------ #
    # وب‌هوک و دریافت آپدیت‌ها
    # ------------------------------------------------------------------ #
    async def set_webhook(self, url: str, **kwargs: Any) -> bool:
        """تنظیم وب‌هوک (متد ``setWebhook``).

        آدرس باید HTTPS باشد؛ پورت‌های پشتیبانی‌شده 443 و 88. برای حذف وب‌هوک
        رشته‌ی خالی بفرستید.

        .. note::
            در مستندات فعلی بازو پارامتر ``secret_token`` ذکر نشده است؛ در صورت
            نیاز می‌توانید آن را با ``**kwargs`` ارسال کنید.
        """
        result = await self._request("setWebhook", url=url, **kwargs)
        return bool(result)

    async def delete_webhook(self, **kwargs: Any) -> bool:
        """حذف وب‌هوک و بازگشت به حالت دریافت با ``getUpdates`` (متد ``deleteWebhook``)."""
        result = await self._request("deleteWebhook", **kwargs)
        return bool(result)

    async def get_webhook_info(self, **kwargs: Any) -> WebhookInfo:
        """دریافت وضعیت فعلی وب‌هوک (متد ``getWebhookInfo``)."""
        result = await self._request("getWebhookInfo", **kwargs)
        return WebhookInfo.from_dict(result)

    async def get_updates(
        self,
        *,
        offset: int | None = None,
        limit: int | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> list[Update]:
        """دریافت آپدیت‌ها با long polling (متد ``getUpdates``).

        Args:
            offset: شناسه‌ی اولین آپدیت مورد انتظار؛ باید یکی بیشتر از بیشترین
                ``update_id`` دریافتی قبلی باشد. مقدار منفی صف را از انتها
                می‌خواند و آپدیت‌های قبلی را فراموش می‌کند.
            limit: حداکثر تعداد آپدیت (۱ تا ۱۰۰؛ پیش‌فرض سرور ۱۰۰).
            timeout: مدت انتظار بر حسب ثانیه؛ اگر آپدیتی نباشد پاسخ خالی
                برمی‌گردد. مهلت HTTP به صورت خودکار متناسب با آن افزایش می‌یابد.

        Returns:
            فهرستی از :class:`~baleRobot.types.updates.Update`.
        """
        request_timeout: float | httpx.Timeout | None = None
        if timeout:
            request_timeout = httpx.Timeout(float(timeout) + 10.0, connect=self._connect_timeout)
        result = await self._request(
            "getUpdates",
            offset=offset,
            limit=limit,
            timeout=timeout,
            _request_timeout=request_timeout,
            **kwargs,
        )
        return [Update.from_dict(item) for item in (result or [])]

    # ------------------------------------------------------------------ #
    # چرخه‌ی عمر
    # ------------------------------------------------------------------ #
    async def aclose(self) -> None:
        """بستن کلاینت HTTP زیرین."""
        if self._owns_client:
            await self._http.aclose()

    async def __aenter__(self) -> AsyncBaleClient:
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.aclose()

    def __repr__(self) -> str:  # pragma: no cover - ابزاری
        mode = "business" if self._business else "bot"
        return f"AsyncBaleClient(base={self._base_url!r}, mode={mode!r})"


class _ApiErrorResponse(Exception):
    """حامل خطای API برای انتقال تصمیم تلاش مجدد به لایه‌ی درخواست."""

    def __init__(self, error: BaleError) -> None:
        super().__init__(str(error))
        self.error = error
