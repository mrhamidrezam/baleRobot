<div dir="rtl">

# baleRobot

[![PyPI version](https://img.shields.io/pypi/v/baleRobot.svg)](https://pypi.org/project/baleRobot/)
[![Python versions](https://img.shields.io/pypi/pyversions/baleRobot.svg)](https://pypi.org/project/baleRobot/)
[![CI](https://github.com/mrhamidrezam/baleRobot/actions/workflows/ci.yml/badge.svg)](https://github.com/mrhamidrezam/baleRobot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/mrhamidrezam/baleRobot/blob/main/LICENSE)

کتابخانه‌ی کامل و تایپ‌شده‌ی پایتون برای **API بازو** (ربات‌ساز پیام‌رسان بله) — هم نسخه‌ی همزمان و هم ناهمگام، با پوشش **۱۰۰٪ مستندات رسمی**.

> 📄 نسخه‌ی فارسی این سند: [README.fa.md](./README.fa.md)

</div>

## Features

- **Full API coverage** — every method in the official Bale Bot API docs:
  messages, media, chat administration, stickers, payments, webhooks, `getUpdates`, plus
  Bale-only methods (`askReview`, `inquireTransaction`) that Telegram libraries don't have.
- **Async-first, sync-friendly** — `AsyncBaleClient` (asyncio) and `BaleClient` (blocking)
  with identical, fully typed signatures.
- **Typed results** — responses are parsed into dataclasses (`Message`, `User`,
  `ChatFullInfo`, `ChatMember` hierarchy, `SuccessfulPayment`, `Transaction`, …).
- **Smart uploads** — pass a `file_id`, an `https` URL, a `pathlib.Path`, `bytes` or an
  `InputFile`; media groups automatically use the `attach://` mechanism.
- **Rate-limit aware** — `429` becomes `TooManyRequests` with `retry_after`; automatic,
  configurable retries for `429`/`5xx` and transient network errors.
- **Business API** — one flag (`business=True`) switches to
  `https://tapi.bale.ai/business/bot<token>/…` for bulk messaging with a separate quota.
- **Mini App server-side helpers** — validate `initData` (HMAC-SHA-256) exactly as the
  official docs describe.
- **PEP 561** — full `py.typed` type hints for excellent IDE completion.

## Installation

```bash
pip install baleRobot
```

Requires Python 3.10+ and [`httpx`](https://www.python-httpx.org/).

## Quick start

### Synchronous

```python
from baleRobot import BaleClient

with BaleClient("YOUR_TOKEN") as client:
    me = client.get_me()
    print(me.first_name, me.username)

    keyboard = InlineKeyboardMarkup.quick([
        [("درباره ما", "about"), "پشتیبانی"],
    ])
    client.send_message(123456789, "سلام!", reply_markup=keyboard)
```

### Asynchronous

```python
import asyncio
from baleRobot import AsyncBaleClient, InlineKeyboardMarkup

async def main() -> None:
    async with AsyncBaleClient("YOUR_TOKEN") as client:
        me = await client.get_me()
        await client.send_message(
            123456789,
            f"سلام {me.first_name}!",
            reply_markup=InlineKeyboardMarkup.quick([[("تماس", "contact")]]),
        )

asyncio.run(main())
```

### Receiving updates (long polling)

```python
from baleRobot import AsyncBaleClient, Update, run_polling

client = AsyncBaleClient("YOUR_TOKEN")

async def handle(update: Update) -> None:
    message = update.effective_message
    if message is None or not message.text:
        return

    if message.command == "start":
        await client.send_message(message.chat_id, "خوش آمدید!")
    elif update.callback_query is not None:
        await client.answer_callback_query(update.callback_query.id, text="دریافت شد")
    else:
        await client.send_chat_action(message.chat_id, "typing")
        await client.send_message(message.chat_id, f"گفتید: {message.text}")

await run_polling(client, handle, skip_pending=True)
```

> Use `run_polling_sync(client, handler)` with the synchronous `BaleClient`.

## Sending files

```python
from pathlib import Path
from baleRobot import InputFile, InputMediaPhoto, InputMediaVideo

# file_id / URL / path / bytes / InputFile — all work
await client.send_photo(chat_id, "AgACAgIAAxkBAAI...")
await client.send_photo(chat_id, "https://example.com/pic.jpg", caption="از اینترنت")
await client.send_document(chat_id, Path("report.pdf"))
await client.send_document(chat_id, InputFile.from_bytes(b"...", filename="note.txt"))

# albums (uploads are sent with the attach:// mechanism automatically)
await client.send_media_group(chat_id, [
    InputMediaPhoto(Path("1.jpg"), caption="آلبوم"),
    InputMediaPhoto(Path("2.jpg")),
])

# download a file (valid for ~1 hour)
info = await client.get_file(file_id)
content = await client.download_file(info)
```

## Formatting (Bale Markdown rules)

```python
from baleRobot import bold, italic, link, inline_note

text = f"{bold('سلام')}، شما {link('اینجا', 'https://ble.ir')} هستید {italic('همین حالا')}"
await client.send_message(chat_id, text)

# inline note:  ```[متن]توضیحات```
await client.send_message(chat_id, inline_note("نکته", "این یک توضیح تکمیلی است"))
```

## Payments (Bale wallet)

```python
from baleRobot import LabeledPrice

invoice = await client.send_invoice(
    chat_id=chat_id,
    title="اشتراک ویژه",
    description="یک ماه دسترسی کامل",
    payload="order-42",              # returned in SuccessfulPayment
    provider_token="WALLET-...",     # from @botfather (test: WALLET-TEST-1111111111111111)
    prices=[LabeledPrice("اشتراک", 150_000)],  # amounts are IRR (integer)
)

# answer pre-checkout within 10 seconds
if update.pre_checkout_query is not None:
    q = update.pre_checkout_query
    await client.answer_pre_checkout_query(q.id, ok=True)

# and inspect a transaction any time
tx = await client.inquire_transaction("transaction-id")
```

## Business (bulk) API

```python
client = AsyncBaleClient("YOUR_TOKEN", business=True)
await client.send_message(user_id, "خبرنامه‌ی هفتگی")  # /business/bot<token>/…
```

## Mini App initData validation (server side)

```python
from baleRobot import InvalidInitData, validate_init_data

try:
    data = validate_init_data(init_data, token="YOUR_TOKEN", max_age=86400)
    user_id = data.user.id
except InvalidInitData:
    ...  # reject the request
```

## Webhooks

```python
from fastapi import FastAPI, Request
from baleRobot import AsyncBaleClient, parse_update

app = FastAPI()
client = AsyncBaleClient("YOUR_TOKEN")

@app.post("/webhook")
async def webhook(request: Request):
    update = parse_update(await request.json())
    message = update.effective_message
    if message is not None and message.text == "/ping":
        await client.send_message(message.chat_id, "pong")
    return {"ok": True}
```

## Error handling

```python
import baleRobot

try:
    await client.send_message(chat_id, text)
except baleRobot.TooManyRequests as e:          # 429
    print("retry after", e.retry_after)
except baleRobot.Forbidden as e:                # 403 (e.g. bot is not admin)
    print(e.description)
except baleRobot.APIError as e:                 # any other API error
    print(e.error_code, e.description)
except baleRobot.NetworkError:                  # connectivity
    print("network problem")
```

Automatic retries are enabled by default (`auto_retry=True`, `max_retries=3`); disable them
if you prefer explicit handling.

## API reference (all covered methods)

| Group | Methods |
| --- | --- |
| Bot info | `get_me` |
| Messages | `send_message`, `forward_message`, `copy_message`, `edit_message_text`, `edit_message_caption`, `edit_message_reply_markup`, `delete_message` |
| Media | `send_photo`, `send_audio`, `send_document`, `send_video`, `send_animation`, `send_voice`, `send_media_group`, `send_location`, `send_contact` |
| Chat | `send_chat_action`, `get_chat`, `get_chat_administrators`, `get_chat_members_count`, `get_chat_member`, `leave_chat`, `set_chat_title`, `set_chat_description`, `set_chat_photo`, `delete_chat_photo`, `create_chat_invite_link`, `revoke_chat_invite_link`, `export_chat_invite_link` |
| Members | `ban_chat_member`, `unban_chat_member`, `promote_chat_member` |
| Pins | `pin_chat_message`, `unpin_chat_message`, `unpin_all_chat_messages` |
| Files | `get_file`, `download_file`, `file_url` |
| Callbacks | `answer_callback_query` |
| Bale-only | `ask_review`, `inquire_transaction` |
| Stickers | `upload_sticker_file`, `create_new_sticker_set`, `add_sticker_to_set` |
| Payments | `send_invoice`, `create_invoice_link`, `answer_pre_checkout_query` |
| Updates & webhook | `get_updates`, `set_webhook`, `delete_webhook`, `get_webhook_info` |

Every method also accepts `**kwargs`, so any additional (or future) API parameter can be sent
without waiting for a library update.

## Running tests

```bash
pip install -e ".[test]"
pytest
```

## Publishing (maintainers)

Releases are published to PyPI automatically through **Trusted Publishing** (OIDC) when a
GitHub Release is published — see [`.github/workflows/publish.yml`](./.github/workflows/publish.yml).
Bump `src/baleRobot/_version.py`, tag the commit as `vX.Y.Z`, then publish the release.

## License

[MIT](./LICENSE) © Hamidreza (mrhamidrezam)
