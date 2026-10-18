"""تست حلقه‌ی دریافت آپدیت‌ها و کمک‌تابع وب‌هوک."""

from __future__ import annotations

import asyncio
import threading
from typing import Any

import pytest

from baleRobot import Update, parse_update, run_polling, run_polling_sync
from conftest import FakeAPI, ok


def _message_update(update_id: int, text: str = "سلام") -> dict[str, Any]:
    return {
        "update_id": update_id,
        "message": {
            "message_id": update_id,
            "date": 1,
            "chat": {"id": 1, "type": "private"},
            "text": text,
        },
    }


pytestmark = pytest.mark.anyio


async def test_run_polling_delivers_updates_and_advances_offset(fake_api: FakeAPI) -> None:
    fake_api.add("getUpdates", ok([_message_update(10)]), ok([_message_update(11)]))
    client = fake_api.client()
    received: list[Update] = []

    async def handler(update: Update) -> None:
        received.append(update)
        if len(received) == 2:
            stop.set()

    stop = asyncio.Event()
    await asyncio.wait_for(run_polling(client, handler, timeout=0, stop_event=stop), 5)

    assert [u.update_id for u in received] == [10, 11]
    # در فراخوانی دوم باید offset به‌روز شده باشد
    assert fake_api.json_body(1) == {"offset": 11, "limit": 100, "timeout": 0}

    await client.aclose()


async def test_run_polling_skip_pending_uses_negative_offset(fake_api: FakeAPI) -> None:
    fake_api.add("getUpdates", ok([]), ok([_message_update(50)]))
    client = fake_api.client()
    received: list[Update] = []

    async def handler(update: Update) -> None:
        received.append(update)
        stop.set()

    stop = asyncio.Event()
    await asyncio.wait_for(
        run_polling(client, handler, timeout=0, skip_pending=True, stop_event=stop), 5
    )

    assert fake_api.calls[0].content == b'{"offset":-1,"limit":1}'
    assert [u.update_id for u in received] == [50]

    await client.aclose()


async def test_run_polling_reports_handler_errors_and_continues(fake_api: FakeAPI) -> None:
    fake_api.add("getUpdates", ok([_message_update(1)]), ok([_message_update(2)]))
    client = fake_api.client()
    handled: list[int] = []
    errors: list[BaseException] = []

    async def handler(update: Update) -> None:
        handled.append(update.update_id)
        if update.update_id == 1:
            raise RuntimeError("خرابی هندلر")
        stop.set()

    def on_error(update: Any, exc: BaseException) -> None:
        errors.append(exc)

    stop = asyncio.Event()
    await asyncio.wait_for(
        run_polling(client, handler, timeout=0, on_error=on_error, stop_event=stop), 5
    )

    assert handled == [1, 2]
    assert len(errors) == 1 and "خرابی هندلر" in str(errors[0])

    await client.aclose()


def test_run_polling_sync(fake_api: FakeAPI) -> None:
    fake_api.add("getUpdates", ok([_message_update(3)]))
    client = fake_api.sync_client()
    received: list[Update] = []
    stop = threading.Event()

    def handler(update: Update) -> None:
        received.append(update)
        stop.set()

    run_polling_sync(client, handler, timeout=0, stop_event=stop)

    assert [u.update_id for u in received] == [3]
    client.close()


def test_parse_update_from_dict_and_json() -> None:
    raw = _message_update(7, "سلام")

    from_dict = parse_update(raw)
    from_json = parse_update(__import__("json").dumps(raw))

    assert from_dict.kind == "message"
    assert from_json.effective_message is not None


def test_parse_update_rejects_invalid_json() -> None:
    with pytest.raises(ValueError):
        parse_update("{not json")

    with pytest.raises(TypeError):
        parse_update(42)  # type: ignore[arg-type]
