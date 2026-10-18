"""تست انواع داده، روابط چندوجهی و ثابت‌ها."""

from __future__ import annotations

import pytest

from baleRobot import (
    CallbackQuery,
    ChatAction,
    ChatMember,
    ChatMemberMember,
    ChatMemberRestricted,
    ChatType,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    PreCheckoutQuery,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    TransactionStatus,
    Update,
    WebhookInfo,
)
from baleRobot.types.messages import WebAppData


def test_chat_member_dispatch_unknown_status_falls_back_to_base() -> None:
    member = ChatMember.from_dict({"status": "left", "user": {"id": 1, "first_name": "x"}})

    assert type(member) is ChatMember
    assert member.status == "left"


def test_chat_member_restricted_fields() -> None:
    member = ChatMember.from_dict(
        {
            "status": "restricted",
            "user": {"id": 1, "first_name": "x"},
            "is_member": True,
            "can_send_messages": False,
            "can_send_photos": True,
        }
    )

    assert isinstance(member, ChatMemberRestricted)
    assert member.can_send_messages is False
    assert member.can_send_photos is True


def test_chat_member_member_type() -> None:
    member = ChatMember.from_dict({"status": "member", "user": {"id": 2, "first_name": "y"}})
    assert isinstance(member, ChatMemberMember)


def test_update_dispatch_and_effective_helpers() -> None:
    update = Update.from_dict(
        {
            "update_id": 5,
            "message": {
                "message_id": 1,
                "date": 1,
                "chat": {"id": 1, "type": "private"},
                "from": {"id": 1, "first_name": "a"},
                "text": "سلام",
            },
        }
    )

    assert update.kind == "message"
    assert update.effective_message is not None
    assert update.effective_user is not None and update.effective_user.id == 1
    assert update.edited_message is None


def test_update_pre_checkout_dispatch() -> None:
    update = Update.from_dict(
        {
            "update_id": 6,
            "pre_checkout_query": {
                "id": "pcq",
                "from": {"id": 9, "first_name": "b"},
                "currency": "IRR",
                "total_amount": 1000,
                "invoice_payload": "p",
            },
        }
    )

    assert update.kind == "pre_checkout_query"
    assert isinstance(update.pre_checkout_query, PreCheckoutQuery)
    assert update.pre_checkout_query.total_amount == 1000


def test_callback_query_type() -> None:
    query = CallbackQuery.from_dict({"id": "1", "from": {"id": 2, "first_name": "x"}, "data": "d"})
    assert query.from_user.id == 2
    assert query.data == "d"


def test_message_command_helpers() -> None:
    message = Message.from_dict(
        {
            "message_id": 1,
            "date": 1,
            "chat": {"id": 1, "type": "private"},
            "text": "/help@my_bot یک دو سه",
        }
    )

    assert message.is_command is True
    assert message.command == "help"
    assert message.args == ["یک", "دو", "سه"]

    plain = Message.from_dict(
        {"message_id": 2, "date": 1, "chat": {"id": 1, "type": "private"}, "text": "سلام"}
    )
    assert plain.is_command is False
    assert plain.command is None
    assert plain.args == []


def test_message_web_app_data_content_type() -> None:
    message = Message.from_dict(
        {
            "message_id": 3,
            "date": 1,
            "chat": {"id": 1, "type": "private"},
            "web_app_data": {"data": "payload"},
        }
    )

    assert isinstance(message.web_app_data, WebAppData)
    assert message.content_type == "web_app_data"


def test_inline_keyboard_button_accepts_dict_web_app() -> None:
    button = InlineKeyboardButton(text="مینی‌اپ", web_app={"url": "https://example.com"})
    markup = InlineKeyboardMarkup(inline_keyboard=[[button]])

    dumped = markup.to_dict()
    assert dumped["inline_keyboard"][0][0]["web_app"]["url"] == "https://example.com"


def test_inline_keyboard_quick_with_tuples_and_strings() -> None:
    markup = InlineKeyboardMarkup.quick(
        [
            ["ساده", ("برچسب", "data")],
            [{"text": "لینک", "url": "https://ble.ir"}],
        ]
    )

    first_row = markup.inline_keyboard[0]
    assert first_row[0].text == "ساده"
    assert first_row[1].callback_data == "data"
    assert markup.inline_keyboard[1][0].url == "https://ble.ir"


def test_reply_keyboard_markup_quick_and_remove() -> None:
    markup = ReplyKeyboardMarkup.quick(
        [["متن"], [KeyboardButton("شماره", request_contact=True)]],
        resize_keyboard=True,
    )

    assert markup.resize_keyboard is True
    assert markup.keyboard[0][0] == "متن"
    assert markup.keyboard[1][0].request_contact is True
    assert ReplyKeyboardRemove().to_dict() == {"remove_keyboard": True}


def test_transaction_status_and_chat_type_constants() -> None:
    assert TransactionStatus.PAID == "paid"
    assert ChatType.CHANNEL == "channel"
    assert ChatAction.UPLOAD_PHOTO == "upload_photo"
    # مقادیر enum باید به صورت رشته هم قابل استفاده باشند
    assert ChatAction("typing") is ChatAction.TYPING


def test_webhook_info_from_dict() -> None:
    info = WebhookInfo.from_dict({"url": "https://example.com/hook"})
    assert info.url == "https://example.com/hook"


def test_transaction_amount_mapping() -> None:
    from baleRobot import Transaction

    tx = Transaction.from_dict({"id": "1", "status": "pending", "userID": 7, "createdAt": 100})
    assert tx.user_id == 7
    assert tx.created_at == 100
    assert tx.to_dict()["userID"] == 7


@pytest.mark.parametrize("bad", [None, 5, "متن"])
def test_from_dict_rejects_non_mapping(bad: object) -> None:
    with pytest.raises(TypeError):
        Message.from_dict(bad)  # type: ignore[arg-type]
