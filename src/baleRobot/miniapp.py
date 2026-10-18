"""کمک‌تابع‌های سمت سرور برای مینی‌اپ‌های بله.

بر خلاف مستندات جاوااسکریپتی مینی‌اپ (که در مرورگر کاربر اجرا می‌شود)، این ماژول
دقیقاً همان بخشی است که باید در **سرور بازو** پیاده‌سازی شود: اعتبارسنجی داده‌های
ورودی (``initData``) با امضای HMAC-SHA-256.

نمونه استفاده در یک سرویس وب:

.. code-block:: python

    from baleRobot import InvalidInitData, validate_init_data

    @app.post("/miniapp/data")
    def read_data(init_data: str):
        try:
            data = validate_init_data(init_data, token=BOT_TOKEN, max_age=86400)
        except InvalidInitData:
            raise HTTPException(status_code=403, detail="invalid init data")
        return {"user_id": data.user.id, "query_id": data.query_id}

.. warning::
    هرگز به داده‌های اعتبارسنجی‌نشده (``initDataUnsafe``) اعتماد نکنید؛ همیشه
    امضای ``hash`` را بررسی کنید.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl

from .errors import InvalidInitData
from .types.base import BaleObject

__all__ = [
    "WebAppInitData",
    "WebAppUser",
    "parse_init_data",
    "validate_init_data",
]


@dataclass
class WebAppUser(BaleObject):
    """اطلاعات کاربری که مینی‌اپ را باز کرده است."""

    id: int = 0
    first_name: str = ""
    username: str | None = None
    allows_write_to_pm: bool | None = None
    photo_url: str | None = None


@dataclass
class WebAppInitData(BaleObject):
    """داده‌های ورودی مینی‌اپ (پس از اعتبارسنجی موفق)."""

    query_id: str | None = None
    user: WebAppUser | None = None
    auth_date: int | None = None
    hash: str | None = None
    start_param: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> WebAppInitData:
        """ساخت شیء از داده‌های URL-encoded مینی‌اپ.

        فیلد ``user`` در رشته‌ی ورودی به صورت JSON-serialized است و قبل از
        تبدیل، رمزگشایی می‌شود.
        """
        if not isinstance(data, Mapping):
            raise TypeError(f"WebAppInitData.from_dict انتظار دیکشنری دارد، {type(data)!r}")
        payload = dict(data)
        user = payload.get("user")
        if isinstance(user, str):
            try:
                payload["user"] = json.loads(user)
            except ValueError:
                payload.pop("user", None)
        return super().from_dict(payload)


def parse_init_data(init_data: str) -> dict[str, str]:
    """تجزیه‌ی رشته‌ی ``initData`` به دیکشنری (بدون اعتبارسنجی امضا).

    Args:
        init_data: مقدار ``Bale.WebApp.initData`` دریافتی از مینی‌اپ.

    Returns:
        دیکشنری مقادیر (شامل ``hash`` و ``auth_date``).
    """
    if not isinstance(init_data, str) or not init_data:
        raise InvalidInitData("رشته‌ی initData خالی یا نامعتبر است")
    return dict(parse_qsl(init_data, keep_blank_values=True))


def validate_init_data(
    init_data: str,
    token: str,
    *,
    max_age: int | None = None,
) -> WebAppInitData:
    """اعتبارسنجی داده‌های ورودی مینی‌اپ طبق مستندات رسمی بله.

    روش کار:

    1. ``data-check-string`` از مقادیر مرتب‌شده‌ی کلید=مقدار (به جز ``hash``)
       با جداکننده‌ی خط جدید ساخته می‌شود.
    2. ``secret_key = HMAC_SHA256(token, "WebAppData")``
    3. امضای محاسبه‌شده با مقدار ``hash`` دریافتی مقایسه می‌شود.

    Args:
        init_data: رشته‌ی ورودی دریافتی از مینی‌اپ.
        token: توکن بازو.
        max_age: در صورت تعیین، حداکثر سن داده بر حسب ثانیه؛ اگر ``auth_date``
            قدیمی‌تر باشد، خطا داده می‌شود (برای جلوگیری از بازپخش).

    Returns:
        شیء :class:`WebAppInitData` معتبرشده.

    Raises:
        InvalidInitData: اگر امضا نادرست باشد، فیلد hash نباشد یا داده قدیمی باشد.
    """
    if not token:
        raise ValueError("توکن بازو برای اعتبارسنجی initData اجباری است")

    fields = parse_init_data(init_data)

    received_hash = fields.pop("hash", None)
    if not received_hash:
        raise InvalidInitData("فیلد hash در داده‌های مینی‌اپ وجود ندارد")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))

    secret_key = hmac.new(token.encode("utf-8"), b"WebAppData", hashlib.sha256).digest()
    calculated = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        raise InvalidInitData("امضای داده‌های مینی‌اپ معتبر نیست")

    result = WebAppInitData.from_dict({**fields, "hash": received_hash})

    if max_age is not None:
        auth_date = result.auth_date
        if auth_date is None:
            raise InvalidInitData("فیلد auth_date در داده‌های مینی‌اپ وجود ندارد")
        if time.time() - auth_date > max_age:
            raise InvalidInitData("داده‌های مینی‌اپ منقضی شده‌اند (قدیمی‌تر از حد مجاز)")

    return result
