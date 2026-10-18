"""کلاس پایه‌ی همه‌ی اشیای API بازو و کمک‌تابع‌های تبدیل."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any, TypeVar

from .._serializers import dump_value, load_value, type_hints

__all__ = ["BaleObject"]

_T = TypeVar("_T", bound="BaleObject")


@dataclasses.dataclass
class BaleObject:
    """پایه‌ی همه‌ی انواع داده‌ی API بازو.

    ویژگی‌ها:

    * :meth:`from_dict` شیء را از پاسخ JSON سرور می‌سازد و شناسایی تو در تو را
      بر عهده دارد.
    * :meth:`to_dict` شیء را برای ارسال به سرور تبدیل می‌کند؛ فیلدهای ``None``
      حذف می‌شوند و نام فیلدهای رزروشده (مثل ``from``) به نام واقعی API برمی‌گردند.

    برای فیلدهایی که نام‌شان در API با کلمات پایتون متفاوت است، از metadata با
    کلید ``api`` استفاده کنید:

    .. code-block:: python

        from_user: Optional[User] = field(default=None, metadata={"api": "from"})
    """

    @classmethod
    def from_dict(cls: type[_T], data: Mapping[str, Any] | None) -> _T:
        """ساخت شیء از یک دیکشنری خام (پاسخ سرور بازو).

        Args:
            data: دیکشنری JSON دریافتی از سرور.

        Returns:
            نمونه‌ای از کلاس جاری؛ فیلدهای ناموجود نادیده گرفته می‌شوند.

        Raises:
            TypeError: اگر ``data`` یک دیکشنری نباشد.
        """
        if not isinstance(data, Mapping):
            raise TypeError(f"{cls.__name__}.from_dict انتظار دیکشنری دارد، {type(data)!r} رسید")
        hints = type_hints(cls)
        kwargs: dict[str, Any] = {}
        for field in dataclasses.fields(cls):
            key = field.metadata.get("api", field.name)
            if key not in data:
                continue
            raw = data[key]
            if raw is None:
                continue
            kwargs[field.name] = load_value(hints.get(field.name, Any), raw)
        return cls(**kwargs)

    def to_dict(self) -> dict[str, Any]:
        """تبدیل شیء به دیکشنری مناسب ارسال به سرور (حذف فیلدهای ``None``)."""
        result: dict[str, Any] = {}
        for field in dataclasses.fields(self):
            raw = getattr(self, field.name)
            if raw is None:
                continue
            key = field.metadata.get("api", field.name)
            result[key] = dump_value(raw)
        return result
