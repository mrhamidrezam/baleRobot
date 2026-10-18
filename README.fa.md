<p align="center">
  <img src="https://raw.githubusercontent.com/mrhamidrezam/baleRobot/main/assets/banner.svg" alt="baleRobot — Complete Python SDK for the Bale Bot API" width="100%">
</p>

<div dir="rtl">

# baleRobot

[![PyPI version](https://img.shields.io/pypi/v/baleRobot.svg)](https://pypi.org/project/baleRobot/)
[![Python versions](https://img.shields.io/pypi/pyversions/baleRobot.svg)](https://pypi.org/project/baleRobot/)
[![CI](https://github.com/mrhamidrezam/baleRobot/actions/workflows/ci.yml/badge.svg)](https://github.com/mrhamidrezam/baleRobot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/mrhamidrezam/baleRobot/blob/main/LICENSE)

کتابخانه‌ی کامل، سریع و تایپ‌شده‌ی پایتون برای **API بازو** (ربات‌ساز پیام‌رسان بله).

این کتابخانه بر پایه‌ی [مستندات رسمی بازو](https://docs.bale.ai/) نوشته شده و **همه‌ی متدها و انواع داده‌ی مستندشده** را پوشش می‌دهد — از ارسال پیام و رسانه تا مدیریت گروه، استیکر، پرداخت کیف‌پول بله، وب‌هوک و دریافت آپدیت‌ها؛ به‌علاوه‌ی متدهای **اختصاصی بله** که در کتابخانه‌های تلگرام وجود ندارند (`askReview` و `inquireTransaction`).

</div>

## نصب

```bash
pip install baleRobot
```

> نیازمند پایتون ۳.۱۰ به بالا و کتابخانه `httpx` است.

## شروع سریع

### حالت همزمان (Sync)

```python
from baleRobot import BaleClient, InlineKeyboardMarkup

with BaleClient("TOKEN") as client:
    me = client.get_me()
    print(me.first_name, me.username)

    keyboard = InlineKeyboardMarkup.quick([
        [("درباره ما", "about"), "پشتیبانی"],
    ])
    client.send_message(123456789, "سلام!", reply_markup=keyboard)
```

### حالت ناهمگام (Async)

```python
import asyncio
from baleRobot import AsyncBaleClient, InlineKeyboardMarkup

async def main() -> None:
    async with AsyncBaleClient("TOKEN") as client:
        me = await client.get_me()
        await client.send_message(
            123456789,
            f"سلام {me.first_name}!",
            reply_markup=InlineKeyboardMarkup.quick([[("تماس", "contact")]]),
        )

asyncio.run(main())
```

### دریافت آپدیت‌ها (long polling)

```python
from baleRobot import AsyncBaleClient, Update, run_polling

client = AsyncBaleClient("TOKEN")

async def handle(update: Update) -> None:
    message = update.effective_message
    if message is None:
        return

    if update.callback_query is not None:
        # پاسخ به دکمه‌ی inline (حتی اگر پیامی نمی‌خواهید نشان دهید)
        await client.answer_callback_query(update.callback_query.id, text="دریافت شد")
        return

    if message.command == "start":
        await client.send_message(message.chat_id, "خوش آمدید!")
    elif message.text:
        await client.send_chat_action(message.chat_id, "typing")
        await client.send_message(message.chat_id, f"گفتید: {message.text}")

await run_polling(client, handle, skip_pending=True)
```

> در کد همزمان از `run_polling_sync(client, handler)` با کلاینت `BaleClient` استفاده کنید.

## ارسال فایل و رسانه

```python
from pathlib import Path
from baleRobot import InputFile, InputMediaPhoto

# file_id، URL، مسیر فایل، bytes یا InputFile — همه پشتیبانی می‌شوند
await client.send_photo(chat_id, "AgACAgIAAxkBAAI...")
await client.send_photo(chat_id, "https://example.com/pic.jpg", caption="از اینترنت")
await client.send_document(chat_id, Path("report.pdf"))
await client.send_voice(chat_id, InputFile("note.ogg"))

# آلبوم (فایل‌های محلی به صورت خودکار با مکانیزم attach:// آپلود می‌شوند)
await client.send_media_group(chat_id, [
    InputMediaPhoto(Path("1.jpg"), caption="آلبوم"),
    InputMediaPhoto(Path("2.jpg")),
])

# دانلود فایل (لینک دانلود یک ساعت اعتبار دارد)
info = await client.get_file(file_id)
content = await client.download_file(info, destination="file.bin")
```

## قالب‌بندی متن (قواعد Markdown بله)

```python
from baleRobot import bold, italic, link, inline_note

text = f"{bold('سلام')}، شما {link('اینجا', 'https://ble.ir')} هستید {italic('همین حالا')}"
await client.send_message(chat_id, text)

# نمایش آنی:  ```[متن]توضیحات```
await client.send_message(chat_id, inline_note("نکته", "توضیح تکمیلی زیر متن"))
```

## صفحه‌کلید

```python
from baleRobot import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)

inline = InlineKeyboardMarkup.quick([
    ["دکمه‌ی ساده", ("برچسب‌دار", "cb:1")],
    [{"text": "مینی‌اپ", "web_app": {"url": "https://example.com/app"}}],
])

reply = ReplyKeyboardMarkup.quick(
    [[KeyboardButton("ارسال شماره", request_contact=True)], ["منو"]],
    resize_keyboard=True,
)

await client.send_message(chat_id, "لطفاً انتخاب کنید", reply_markup=inline)
await client.send_message(chat_id, "ممنون!", reply_markup=ReplyKeyboardRemove())
```

## مدیریت گروه و اعضا

```python
member = await client.get_chat_member(chat_id, user_id)
if member.status == "administrator":
    print("مدیر است؛ می‌تواند اعضا را محدود کند:", member.can_restrict_members)

await client.ban_chat_member(chat_id, user_id)
await client.unban_chat_member(chat_id, user_id, only_if_banned=True)
await client.promote_chat_member(chat_id, user_id, can_delete_messages=True)
await client.pin_chat_message(chat_id, message_id)
await client.set_chat_title(chat_id, "عنوان جدید")
```

## پرداخت کیف‌پول بله

```python
from baleRobot import LabeledPrice

await client.send_invoice(
    chat_id=chat_id,
    title="اشتراک ویژه",
    description="یک ماه دسترسی کامل",
    payload="order-42",              # در SuccessfulPayment برمی‌گردد
    provider_token="WALLET-...",     # از @botfather (تست: WALLET-TEST-1111111111111111)
    prices=[LabeledPrice("اشتراک", 150_000)],  # مبالغ به ریال و عدد صحیح
)

# پاسخ به بررسی پیش از پرداخت (حداکثر ۱۰ ثانیه!)
if update.pre_checkout_query is not None:
    await client.answer_pre_checkout_query(update.pre_checkout_query.id, ok=True)

# استعلام وضعیت تراکنش (متد اختصاصی بله)
tx = await client.inquire_transaction("transaction-id")
print(tx.status, tx.amount)
```

## رضایت‌سنجی (متد اختصاصی بله)

```python
# بهترین زمان: بلافاصله پس از ارائه‌ی خدمت مفید
await client.ask_review(user_id, delay_seconds=30)
```

## API کسب‌وکاری (ارسال پیام انبوه)

برای ارسال پیام به کاربرانی که در جریان فعال گفتگو نیستند، از سهمیه‌ی مستقل و بالاتر API کسب‌وکاری استفاده کنید (نیازمند شارژ حساب از پنل کسب‌وکار بله):

```python
client = AsyncBaleClient("TOKEN", business=True)
await client.send_message(user_id, "خبرنامه‌ی هفتگی")
```

## مینی‌اپ: اعتبارسنجی initData در سمت سرور

```python
from baleRobot import InvalidInitData, validate_init_data

try:
    data = validate_init_data(init_data, token="TOKEN", max_age=86400)
    user_id = data.user.id
    print(data.query_id, data.start_param)
except InvalidInitData:
    ...  # درخواست را رد کنید
```

## وب‌هوک

```python
from fastapi import FastAPI, Request
from baleRobot import AsyncBaleClient, parse_update

app = FastAPI()
client = AsyncBaleClient("TOKEN")

@app.post("/webhook")
async def webhook(request: Request):
    update = parse_update(await request.json())
    message = update.effective_message
    if message is not None and message.text == "/ping":
        await client.send_message(message.chat_id, "pong")
    return {"ok": True}
```

## مدیریت خطاها

```python
import baleRobot

try:
    await client.send_message(chat_id, text)
except baleRobot.TooManyRequests as e:      # 429 — محدودیت نرخ ارسال
    print("چند ثانیه بعد دوباره تلاش کن:", e.retry_after)
except baleRobot.Forbidden as e:            # 403 — مثلاً بازو ادمین نیست
    print(e.description)
except baleRobot.APIError as e:             # هر خطای دیگر API
    print(e.error_code, e.description)
except baleRobot.NetworkError:              # مشکل اتصال
    print("خطای شبکه")
```

به صورت پیش‌فرض تلاش خودکار برای خطاهای موقت (429 و 5xx) فعال است؛ برای غیرفعال کردن: `BaleClient(token, auto_retry=False)`.

## فهرست کامل متدها

| دسته | متدها |
| --- | --- |
| اطلاعات بازو | `get_me` |
| پیام | `send_message`، `forward_message`، `copy_message`، `edit_message_text`، `edit_message_caption`، `edit_message_reply_markup`، `delete_message` |
| رسانه | `send_photo`، `send_audio`، `send_document`، `send_video`، `send_animation`، `send_voice`، `send_media_group`، `send_location`، `send_contact` |
| گفتگو | `send_chat_action`، `get_chat`، `get_chat_administrators`، `get_chat_members_count`، `get_chat_member`، `leave_chat`، `set_chat_title`، `set_chat_description`، `set_chat_photo`، `delete_chat_photo`، `create_chat_invite_link`، `revoke_chat_invite_link`، `export_chat_invite_link` |
| اعضا | `ban_chat_member`، `unban_chat_member`، `promote_chat_member` |
| سنجاق | `pin_chat_message`، `unpin_chat_message`، `unpin_all_chat_messages` |
| فایل | `get_file`، `download_file`، `file_url` |
| دکمه‌ی inline | `answer_callback_query` |
| اختصاصی بله | `ask_review`، `inquire_transaction` |
| استیکر | `upload_sticker_file`، `create_new_sticker_set`، `add_sticker_to_set` |
| پرداخت | `send_invoice`، `create_invoice_link`، `answer_pre_checkout_query` |
| آپدیت و وب‌هوک | `get_updates`، `set_webhook`، `delete_webhook`، `get_webhook_info` |

همه‌ی متدها پارامتر `**kwargs` هم دارند؛ پس هر پارامتر جدید یا تکمیلی API بازو (مثل `parse_mode` یا `allowed_updates`) را هم می‌توانید بفرستید، بی‌آنکه منتظر به‌روزرسانی کتابخانه بمانید.

## اجرای تست‌ها

```bash
pip install -e ".[test]"
pytest
```

## انتشار نسخه

انتشار در PyPI به صورت خودکار و با **Trusted Publishing** (OIDC) انجام می‌شود؛ کافی است نسخه را در `src/baleRobot/_version.py` بالا ببرید، نشان `vX.Y.Z` بزنید و یک Release در گیتهاب منتشر کنید.

## لایسنس

[MIT](https://github.com/mrhamidrezam/baleRobot/blob/main/LICENSE) © Hamidreza (mrhamidrezam)
