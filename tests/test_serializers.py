"""تست سریالایز/دی‌سریالایز انواع داده."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from baleRobot import InlineKeyboardMarkup, LabeledPrice, Message, User
from baleRobot._serializers import ATTACH_PREFIX, dump_params, dump_value, is_uploadable
from baleRobot.types.input import InputFile, InputMediaPhoto


def test_dump_skips_none_and_applies_api_alias() -> None:
    message = Message(message_id=5, from_user=User(id=7, first_name="a"))
    dumped = dump_value(message)

    assert dumped["message_id"] == 5
    assert dumped["from"] == {"id": 7, "is_bot": False, "first_name": "a"}
    assert "from_user" not in dumped
    assert "text" not in dumped  # مقدار None نباید ارسال شود


def test_dump_nested_keyboard() -> None:
    markup = InlineKeyboardMarkup.quick([[("تست", "cb:1")]])
    dumped = dump_value(markup)

    assert dumped == {
        "inline_keyboard": [[{"text": "تست", "callback_data": "cb:1"}]],
    }


def test_is_uploadable_distinguishes_ids_paths_and_bytes() -> None:
    assert is_uploadable(b"raw")
    assert is_uploadable(Path("README.md"))
    assert is_uploadable(InputFile(b"x", filename="a.txt"))
    # رشته‌ها هرگز فایل نیستند (file_id یا URL)
    assert not is_uploadable("AgACAgIAAxkB")
    assert not is_uploadable("https://example.com/a.jpg")
    assert not is_uploadable(42)


def test_dump_params_top_level_file_uses_field_name() -> None:
    data, files = dump_params({"chat_id": 1, "photo": InputFile(b"IMG", filename="pic.jpg")})

    assert data == {"chat_id": 1}
    assert set(files) == {"photo"}
    assert files["photo"].filename == "pic.jpg"
    assert files["photo"].content == b"IMG"


def test_dump_params_nested_file_uses_attach(tmp_path: Path) -> None:
    target = tmp_path / "a.jpg"
    target.write_bytes(b"JPEGDATA")

    media = [InputMediaPhoto(target, caption="کپشن")]
    data, files = dump_params({"chat_id": 1, "media": media})

    assert data["media"][0]["media"] == f"{ATTACH_PREFIX}file_0"
    assert data["media"][0]["type"] == "photo"
    assert data["media"][0]["caption"] == "کپشن"
    assert files["file_0"].content == b"JPEGDATA"
    assert files["file_0"].filename == "a.jpg"


def test_labeled_price_to_dict() -> None:
    price = LabeledPrice("کالا", 1500)
    assert price.to_dict() == {"label": "کالا", "amount": 1500}


def test_message_from_dict_nested_types() -> None:
    raw = {
        "message_id": 10,
        "date": 1700000000,
        "chat": {"id": -100, "type": "supergroup", "title": "گروه"},
        "from": {"id": 1, "is_bot": False, "first_name": "علی"},
        "photo": [
            {"file_id": "p1", "file_unique_id": "u1", "width": 90, "height": 50},
            {"file_id": "p2", "file_unique_id": "u2", "width": 800, "height": 450},
        ],
        "caption": "زیرنویس",
    }
    message = Message.from_dict(raw)

    assert message.chat is not None and message.chat.title == "گروه"
    assert message.from_user is not None and message.from_user.first_name == "علی"
    assert message.photo is not None and message.photo[1].width == 800
    assert message.content_type == "photo"
    assert message.chat_id == -100
    assert message.user_id == 1


def test_input_file_from_bytes_and_path(tmp_path: Path) -> None:
    target = tmp_path / "voice.ogg"
    target.write_bytes(b"OGG")

    from_bytes = InputFile.from_bytes(b"\x89PNG", filename="x.png")
    assert from_bytes.filename == "x.png"
    assert from_bytes.content_type == "image/png"

    from_path = InputFile.from_path(target)
    assert from_path.filename == "voice.ogg"
    assert from_path.content == b"OGG"
    assert from_path.content_type == "audio/ogg"


def test_input_file_rejects_unsupported_source() -> None:
    with pytest.raises(TypeError):
        InputFile(object())  # type: ignore[arg-type]


def test_dataclass_fields_are_all_defaults_for_output_types() -> None:
    """انواع خروجی باید بدون آرگومان اجباری قابل ساخت باشند (سخاوتمندی در پارس)."""
    for cls in (Message, User):
        instance = cls()
        assert isinstance(instance, cls)
        assert dataclasses.is_dataclass(instance)
