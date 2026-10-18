"""تست رفتار کلاینت ناهمگام در برابر پاسخ‌های جعلی سرور."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from baleRobot import (
    AsyncBaleClient,
    BadRequest,
    ChatMemberAdministrator,
    ChatMemberOwner,
    InputMediaPhoto,
    LabeledPrice,
    Message,
    TooManyRequests,
    Transaction,
    Unauthorized,
    Update,
    User,
)
from baleRobot.types.keyboards import InlineKeyboardMarkup
from conftest import TOKEN, FakeAPI, fail, msg_ok, ok

pytestmark = pytest.mark.anyio


async def test_get_me_builds_expected_url_and_parses_user(fake_api: FakeAPI) -> None:
    fake_api.add("getMe", ok({"id": 1, "is_bot": True, "first_name": "ربات", "username": "my_bot"}))
    client = fake_api.client()

    me = await client.get_me()

    request = fake_api.calls[0]
    assert request.method == "POST"
    assert request.url.path == f"/bot{TOKEN}/getMe"
    assert str(request.url).startswith("https://tapi.bale.ai/")
    assert isinstance(me, User)
    assert me.username == "my_bot"
    assert me.is_bot is True

    await client.aclose()


async def test_send_message_json_body_and_typed_result(fake_api: FakeAPI) -> None:
    fake_api.add(
        "sendMessage",
        msg_ok(message_id=42, chat_id=7, text="سلام"),
    )
    client = fake_api.client()
    keyboard = InlineKeyboardMarkup.quick([[("تست", "cb:1")]])

    message = await client.send_message(7, "سلام", reply_markup=keyboard, parse_mode="Markdown")

    body = fake_api.json_body()
    assert body["chat_id"] == 7
    assert body["text"] == "سلام"
    assert body["parse_mode"] == "Markdown"  # عبور kwargsهای دلخواه
    assert body["reply_markup"] == {"inline_keyboard": [[{"text": "تست", "callback_data": "cb:1"}]]}
    assert isinstance(message, Message)
    assert message.message_id == 42

    await client.aclose()


async def test_none_params_are_not_sent(fake_api: FakeAPI) -> None:
    fake_api.add("sendMessage", msg_ok())
    client = fake_api.client()

    await client.send_message(1, "متن")

    body = fake_api.json_body()
    assert set(body) == {"chat_id", "text"}

    await client.aclose()


async def test_api_error_raises_typed_exception(fake_api: FakeAPI) -> None:
    fake_api.add("sendMessage", fail(400, "Bad Request: chat not found"))
    client = fake_api.client()

    with pytest.raises(BadRequest) as excinfo:
        await client.send_message(1, "سلام")

    assert "chat not found" in str(excinfo.value)
    assert excinfo.value.error_code == 400

    await client.aclose()


async def test_unauthorized_bad_token(fake_api: FakeAPI) -> None:
    fake_api.add("getMe", fail(401, "Unauthorized"))
    client = fake_api.client()

    with pytest.raises(Unauthorized):
        await client.get_me()

    await client.aclose()


async def test_too_many_requests_exposes_retry_after(fake_api: FakeAPI) -> None:
    fake_api.add("sendMessage", fail(429, "Too Many Requests: retry after 5", {"retry_after": 5}))
    client = fake_api.client()

    with pytest.raises(TooManyRequests) as excinfo:
        await client.send_message(1, "سلام")

    assert excinfo.value.retry_after == 5

    await client.aclose()


async def test_auto_retry_waits_and_succeeds(fake_api: FakeAPI) -> None:
    fake_api.add(
        "sendMessage",
        fail(429, "Too Many Requests", {"retry_after": 0}),
        ok({"message_id": 9, "date": 1, "chat": {"id": 1, "type": "private"}}),
    )
    client = AsyncBaleClient(
        TOKEN, transport=fake_api.transport(), retry_backoff=0.0, max_retry_delay=0.0
    )

    message = await client.send_message(1, "سلام")

    assert message.message_id == 9
    assert len(fake_api.calls) == 2  # یک تلاش اولیه + یک تلاش مجدد

    await client.aclose()


async def test_retry_exhausted_raises_original_error(fake_api: FakeAPI) -> None:
    fake_api.add("sendMessage", fail(500, "Internal Server Error"))
    client = AsyncBaleClient(
        TOKEN, transport=fake_api.transport(), max_retries=2, retry_backoff=0.0, max_retry_delay=0.0
    )

    with pytest.raises(Exception) as excinfo:
        await client.send_message(1, "سلام")

    assert type(excinfo.value).__name__ == "ServerError"
    assert len(fake_api.calls) == 3  # اولی + دو تلاش مجدد

    await client.aclose()


async def test_send_photo_with_input_file_uses_multipart(tmp_path: Path, fake_api: FakeAPI) -> None:
    fake_api.add("sendPhoto", msg_ok(message_id=3))
    client = fake_api.client()
    target = tmp_path / "pic.jpg"
    target.write_bytes(b"JPEG-BYTES")

    await client.send_photo(1, target, caption="تصویر")

    request = fake_api.calls[0]
    assert request.headers["content-type"].startswith("multipart/form-data")
    body = request.content
    assert b'name="chat_id"' in body
    assert b'name="photo"; filename="pic.jpg"' in body
    assert b"JPEG-BYTES" in body

    await client.aclose()


async def test_send_photo_by_file_id_uses_json(fake_api: FakeAPI) -> None:
    fake_api.add("sendPhoto", msg_ok(message_id=3))
    client = fake_api.client()

    await client.send_photo(1, "AgACAgIAAxkBAAI")

    request = fake_api.calls[0]
    assert request.headers["content-type"] == "application/json"
    assert fake_api.json_body()["photo"] == "AgACAgIAAxkBAAI"

    await client.aclose()


async def test_send_media_group_uses_attach_mechanism(tmp_path: Path, fake_api: FakeAPI) -> None:
    fake_api.add(
        "sendMediaGroup",
        ok(
            [
                {"message_id": 1, "date": 1, "chat": {"id": 1, "type": "private"}},
                {"message_id": 2, "date": 1, "chat": {"id": 1, "type": "private"}},
            ]
        ),
    )
    client = fake_api.client()
    first = tmp_path / "1.jpg"
    first.write_bytes(b"ONE")

    messages = await client.send_media_group(
        1, [InputMediaPhoto(first, caption="اول"), InputMediaPhoto("AgACAgID")]
    )

    request = fake_api.calls[0]
    assert request.headers["content-type"].startswith("multipart/form-data")
    body = request.content
    assert b"attach://file_0" in body
    assert b'name="file_0"; filename="1.jpg"' in body
    assert b"ONE" in body
    assert len(messages) == 2
    assert isinstance(messages[0], Message)

    await client.aclose()


async def test_business_mode_changes_base_path(fake_api: FakeAPI) -> None:
    fake_api.add("sendMessage", msg_ok(message_id=5))
    client = fake_api.client(business=True)

    await client.send_message(1, "خبرنامه")

    assert fake_api.calls[0].url.path == f"/business/bot{TOKEN}/sendMessage"
    assert client.business is True

    await client.aclose()


async def test_get_updates_parses_message_update(fake_api: FakeAPI) -> None:
    fake_api.add(
        "getUpdates",
        ok(
            [
                {
                    "update_id": 100,
                    "message": {
                        "message_id": 7,
                        "date": 1700000000,
                        "chat": {"id": 5, "type": "private", "first_name": "x"},
                        "from": {"id": 5, "is_bot": False, "first_name": "x"},
                        "text": "/start پارامتر",
                    },
                }
            ]
        ),
    )
    client = fake_api.client()

    updates = await client.get_updates(offset=42, limit=50, timeout=20)

    body = fake_api.json_body()
    assert body == {"offset": 42, "limit": 50, "timeout": 20}
    update = updates[0]
    assert isinstance(update, Update)
    assert update.kind == "message"
    message = update.effective_message
    assert message is not None
    assert message.command == "start"
    assert message.args == ["پارامتر"]
    assert update.effective_user is not None and update.effective_user.id == 5

    await client.aclose()


async def test_get_updates_extends_read_timeout(fake_api: FakeAPI) -> None:
    fake_api.add("getUpdates", ok([]))
    client = fake_api.client(timeout=5.0)

    await client.get_updates(timeout=30)

    request = fake_api.calls[0]
    assert request.extensions["timeout"]["read"] == pytest.approx(40.0)

    await client.aclose()


async def test_callback_query_update_dispatch(fake_api: FakeAPI) -> None:
    fake_api.add(
        "getUpdates",
        ok(
            [
                {
                    "update_id": 101,
                    "callback_query": {
                        "id": "cbq",
                        "from": {"id": 3, "is_bot": False, "first_name": "کاربر"},
                        "data": "about",
                        "message": {
                            "message_id": 8,
                            "date": 1,
                            "chat": {"id": 3, "type": "private"},
                            "text": "پیام",
                        },
                    },
                }
            ]
        ),
    )
    client = fake_api.client()

    updates = await client.get_updates()

    update = updates[0]
    assert update.kind == "callback_query"
    assert update.callback_query is not None
    assert update.callback_query.data == "about"
    assert update.effective_message is not None

    await client.aclose()


async def test_get_chat_member_dispatches_by_status(fake_api: FakeAPI) -> None:
    fake_api.add(
        "getChatMember",
        ok(
            {
                "status": "administrator",
                "user": {"id": 2, "is_bot": False, "first_name": "مدیر"},
                "can_delete_messages": True,
                "can_restrict_members": False,
            }
        ),
    )
    client = fake_api.client()

    member = await client.get_chat_member(-100, 2)

    assert isinstance(member, ChatMemberAdministrator)
    assert member.can_delete_messages is True
    assert member.user is not None and member.user.first_name == "مدیر"

    await client.aclose()


async def test_get_chat_administrators_owner_status(fake_api: FakeAPI) -> None:
    fake_api.add(
        "getChatAdministrators",
        ok(
            [
                {"status": "creator", "user": {"id": 1, "is_bot": False, "first_name": "مالک"}},
                {
                    "status": "administrator",
                    "user": {"id": 2, "is_bot": True, "first_name": "ربات"},
                },
            ]
        ),
    )
    client = fake_api.client()

    admins = await client.get_chat_administrators(-100)

    assert isinstance(admins[0], ChatMemberOwner)
    assert admins[1].status == "administrator"

    await client.aclose()


async def test_edit_message_text_accepts_message_or_bool(fake_api: FakeAPI) -> None:
    fake_api.add(
        "editMessageText",
        ok({"message_id": 8, "date": 1, "chat": {"id": 1, "type": "private"}, "text": "جدید"}),
        ok(True),
    )
    client = fake_api.client()

    edited = await client.edit_message_text(1, 8, "جدید")
    assert isinstance(edited, Message)

    unchanged = await client.edit_message_text(1, 8, "جدید")
    assert unchanged is True

    await client.aclose()


async def test_ask_review_is_supported(fake_api: FakeAPI) -> None:
    fake_api.add("askReview", ok(True))
    client = fake_api.client()

    assert await client.ask_review(user_id=5, delay_seconds=30) is True
    assert fake_api.json_body() == {"user_id": 5, "delay_seconds": 30}

    await client.aclose()


async def test_inquire_transaction_maps_non_snake_case_fields(fake_api: FakeAPI) -> None:
    fake_api.add(
        "inquireTransaction",
        ok(
            {
                "id": "tx-1",
                "status": "paid",
                "userID": 42,
                "amount": 25000,
                "createdAt": 1700000000,
            }
        ),
    )
    client = fake_api.client()

    transaction = await client.inquire_transaction("tx-1")

    assert isinstance(transaction, Transaction)
    assert transaction.user_id == 42
    assert transaction.created_at == 1700000000
    assert transaction.status == "paid"

    await client.aclose()


async def test_answer_pre_checkout_query_requires_error_message_when_rejected(
    fake_api: FakeAPI,
) -> None:
    client = fake_api.client()

    with pytest.raises(ValueError):
        await client.answer_pre_checkout_query("q1", ok=False)

    fake_api.add("answerPreCheckoutQuery", ok(True))
    assert await client.answer_pre_checkout_query("q1", ok=False, error_message="ناموجود") is True

    await client.aclose()


async def test_send_invoice_serializes_prices(fake_api: FakeAPI) -> None:
    fake_api.add("sendInvoice", msg_ok(message_id=6))
    client = fake_api.client()

    await client.send_invoice(
        chat_id=1,
        title="کالا",
        description="توضیح",
        payload="p-1",
        provider_token="WALLET-TEST-1111111111111111",
        prices=[LabeledPrice("قلم اول", 1000)],
    )

    body = fake_api.json_body()
    assert body["prices"] == [{"label": "قلم اول", "amount": 1000}]
    assert body["provider_token"] == "WALLET-TEST-1111111111111111"

    await client.aclose()


async def test_get_chat_members_count_returns_int(fake_api: FakeAPI) -> None:
    fake_api.add("getChatMembersCount", ok(1500))
    client = fake_api.client()

    count = await client.get_chat_members_count(-100)

    assert count == 1500 and isinstance(count, int)

    await client.aclose()


async def test_file_url_format(fake_api: FakeAPI) -> None:
    client = fake_api.client()

    assert client.file_url("documents/file_1.jpg") == (
        f"https://tapi.bale.ai/file/bot{TOKEN}/documents/file_1.jpg"
    )

    await client.aclose()


async def test_invalid_json_response_raises_network_error(fake_api: FakeAPI) -> None:
    fake_api.add("getMe", httpx.Response(200, text="<html>oops</html>"))
    client = fake_api.client()

    from baleRobot import NetworkError

    with pytest.raises(NetworkError):
        await client.get_me()

    await client.aclose()


async def test_token_is_required() -> None:
    with pytest.raises(ValueError):
        AsyncBaleClient("")
