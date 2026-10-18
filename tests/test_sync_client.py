"""تست کلاینت همزمان (همان پوشش، به صورت Blocking)."""

from __future__ import annotations

import threading

import pytest

from baleRobot import Message, TooManyRequests, Update
from conftest import FakeAPI, fail, msg_ok, ok


def test_sync_get_me(fake_api: FakeAPI) -> None:
    fake_api.add("getMe", ok({"id": 1, "is_bot": True, "first_name": "ربات"}))
    client = fake_api.sync_client()

    me = client.get_me()

    assert me.first_name == "ربات"
    client.close()


def test_sync_send_message_returns_message(fake_api: FakeAPI) -> None:
    fake_api.add("sendMessage", msg_ok(message_id=3, chat_id=9))
    client = fake_api.sync_client()

    message = client.send_message(9, "سلام")

    assert isinstance(message, Message)
    assert message.message_id == 3
    client.close()


def test_sync_error_handling(fake_api: FakeAPI) -> None:
    fake_api.add("sendMessage", fail(429, "slow down", {"retry_after": 3}))
    client = fake_api.sync_client()

    with pytest.raises(TooManyRequests) as excinfo:
        client.send_message(1, "سلام")

    assert excinfo.value.retry_after == 3
    client.close()


def test_sync_context_manager(fake_api: FakeAPI) -> None:
    fake_api.add("getMe", ok({"id": 1, "is_bot": True, "first_name": "ربات"}))

    with fake_api.sync_client() as client:
        assert client.get_me().id == 1
        assert client.is_closed is False

    assert client.is_closed is True


def test_sync_client_rejects_use_after_close(fake_api: FakeAPI) -> None:
    client = fake_api.sync_client()
    client.close()

    with pytest.raises(RuntimeError):
        client.get_me()


def test_sync_polling_style_get_updates(fake_api: FakeAPI) -> None:
    fake_api.add(
        "getUpdates",
        ok(
            [
                {
                    "update_id": 1,
                    "message": {
                        "message_id": 1,
                        "date": 1,
                        "chat": {"id": 1, "type": "private"},
                        "text": "سلام",
                    },
                }
            ]
        ),
    )
    client = fake_api.sync_client()

    updates = client.get_updates(timeout=0)

    assert len(updates) == 1
    assert isinstance(updates[0], Update)
    assert updates[0].message is not None
    client.close()


def test_sync_client_is_thread_safe(fake_api: FakeAPI) -> None:
    fake_api.add("getMe", ok({"id": 1, "is_bot": True, "first_name": "ربات"}))
    client = fake_api.sync_client()
    results: list[int] = []
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            results.append(client.get_me().id)
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors
    assert results == [1, 1, 1, 1]
    client.close()
