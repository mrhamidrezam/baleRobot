"""تست اعتبارسنجی داده‌های ورودی مینی‌اپ."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from baleRobot import InvalidInitData, WebAppInitData, validate_init_data
from baleRobot.miniapp import parse_init_data

TOKEN = "7000000001:AAF-test-token"


def _sign(fields: dict[str, str], token: str = TOKEN) -> str:
    """ساخت امضای درست طبق الگوریتم رسمی مستندات مینی‌اپ."""
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    secret_key = hmac.new(token.encode(), b"WebAppData", hashlib.sha256).digest()
    return hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()


def _init_data(fields: dict[str, str], token: str = TOKEN) -> str:
    return urlencode({**fields, "hash": _sign(fields, token)})


def test_validate_valid_init_data() -> None:
    fields = {
        "query_id": "AAHk2",
        "user": json.dumps({"id": 42, "first_name": "کاربر", "username": "user"}),
        "auth_date": str(int(time.time())),
    }

    data = validate_init_data(_init_data(fields), TOKEN)

    assert isinstance(data, WebAppInitData)
    assert data.query_id == "AAHk2"
    assert data.user is not None
    assert data.user.id == 42
    assert data.user.username == "user"
    assert data.hash is not None


def test_tampered_signature_is_rejected() -> None:
    fields = {
        "user": json.dumps({"id": 42, "first_name": "کاربر"}),
        "auth_date": str(int(time.time())),
    }
    init_data = _init_data(fields)
    # تغییر یک کاراکتر در user بدون امضای مجدد
    tampered = init_data.replace("42", "43")

    with pytest.raises(InvalidInitData):
        validate_init_data(tampered, TOKEN)


def test_wrong_token_is_rejected() -> None:
    fields = {"auth_date": str(int(time.time())), "user": json.dumps({"id": 1, "first_name": "a"})}

    with pytest.raises(InvalidInitData):
        validate_init_data(_init_data(fields, token="123:OTHER"), TOKEN)


def test_missing_hash_is_rejected() -> None:
    with pytest.raises(InvalidInitData):
        validate_init_data("user=%7B%22id%22%3A1%7D", TOKEN)


def test_max_age_rejects_old_data() -> None:
    fields = {
        "user": json.dumps({"id": 1, "first_name": "a"}),
        "auth_date": str(int(time.time()) - 7200),
    }

    with pytest.raises(InvalidInitData):
        validate_init_data(_init_data(fields), TOKEN, max_age=3600)

    # و در صورت مهلت کافی، معتبر است
    assert validate_init_data(_init_data(fields), TOKEN, max_age=86400).user is not None


def test_parse_init_data_returns_pairs() -> None:
    parsed = parse_init_data("a=1&b=%D8%B3%D9%84%D8%A7%D9%85")
    assert parsed == {"a": "1", "b": "سلام"}


def test_parse_init_data_rejects_empty() -> None:
    with pytest.raises(InvalidInitData):
        parse_init_data("")
