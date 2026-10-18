"""تبدیل اشیای پایتونی به JSON سازگار با API بازو و بالعکس.

قوانین مهم:

* پارامترهای ``None`` ارسال نمی‌شوند.
* رشته‌ها و اعداد همان‌طور که هستند ارسال می‌شوند (شناسه گفتگو می‌تواند int یا
  رشته‌ی ``@channelusername`` باشد).
* اشیای داده‌کلاس به دیکشنری تبدیل می‌شوند؛ نام فیلد با متدادا ``{"api": "from"}``
  می‌تواند نام واقعی فیلد در API را تعیین کند (برای فیلدهایی مثل ``from``).
* هر فایل قابل ارسال (:class:`~baleRobot.types.input.InputFile`، ``bytes``،
  :class:`pathlib.Path`، شیء دارای ``read``) به صورت آپلود multipart درمی‌آید.
  در سطح بالای درخواست (مثلاً پارامتر ``photo``) نام فیلد همان نام پارامتر است و
  در عمق ساختارها (مثلاً داخل ``media`` متد sendMediaGroup) به شکل
  ``attach://file_0`` بازنویسی می‌شود.
"""

from __future__ import annotations

import dataclasses
import enum
import itertools
import mimetypes
import os
import types as _py_types
import typing
from collections import abc as cabc
from collections.abc import Mapping
from typing import Any, Union
from urllib.parse import quote

ATTACH_PREFIX = "attach://"

__all__ = [
    "ATTACH_PREFIX",
    "Upload",
    "build_url",
    "dump_params",
    "dump_value",
    "is_uploadable",
    "json_default",
    "load_value",
    "to_upload",
    "type_hints",
]


# --------------------------------------------------------------------------- #
# آپلود فایل
# --------------------------------------------------------------------------- #
@dataclasses.dataclass(frozen=True)
class Upload:
    """یک فایل آماده‌ی ارسال با multipart/form-data."""

    filename: str
    content: bytes
    content_type: str | None = None

    def as_httpx_files(self) -> tuple[str, bytes, str | None]:
        """تبدیل به ساختار پذیرفته‌شده توسط httpx برای پارامتر ``files``."""
        return (self.filename, self.content, self.content_type)


def is_uploadable(value: Any) -> bool:
    """تشخیص اینکه آیا مقدار باید به صورت فایل آپلود شود یا خیر.

    رشته‌های معمولی آپلود نمی‌شوند تا بتوان از آن‌ها به عنوان ``file_id`` یا URL
    استفاده کرد. برای ارسال یک فایل محلی به صورت رشته، :class:`pathlib.Path`
    یا کلاس :class:`~baleRobot.types.input.InputFile` به کار ببرید.
    """
    if isinstance(value, (bytes, bytearray, memoryview)):
        return True
    if isinstance(value, (str, os.PathLike)):
        # PathLike (مثل pathlib.Path) فایل محلی است؛ رشته file_id/URL محسوب می‌شود
        return not isinstance(value, str) and hasattr(value, "__fspath__")
    if getattr(value, "_bale_upload", False):
        return True
    return hasattr(value, "read") and not isinstance(value, (Mapping, list, tuple))


def to_upload(value: Any) -> Upload:
    """تبدیل هر منبع فایل به :class:`Upload` (با خواندن محتوا در حافظه).

    بافر کردن محتوا در حافظه، ارسال مجدد (retry) درخواست‌های فایلی را ممکن می‌کند
    و برای سقف ۵۰ مگابایتی فایل‌های بازو کاملاً مناسب است.
    """
    if isinstance(value, Upload):
        return value

    # InputFile (بدون وابستگی چرخه‌ای به ماژول types)
    if getattr(value, "_bale_upload", False) and hasattr(value, "to_upload"):
        return value.to_upload()

    if isinstance(value, (bytes, bytearray, memoryview)):
        return Upload(filename="file.bin", content=bytes(value), content_type=None)

    if isinstance(value, os.PathLike) and not isinstance(value, str):
        path = os.fspath(value)
        with open(path, "rb") as handle:
            content = handle.read()
        filename = os.path.basename(path) or "file.bin"
        return Upload(filename=filename, content=content, content_type=_guess_type(filename))

    if hasattr(value, "read"):
        content = value.read()
        if isinstance(content, str):
            content = content.encode("utf-8")
        raw_name = getattr(value, "name", "") or ""
        filename = os.path.basename(str(raw_name)) or "file.bin"
        return Upload(filename=filename, content=bytes(content), content_type=_guess_type(filename))

    raise TypeError(f"مقدار قابل ارسال به عنوان فایل نیست: {type(value)!r}")


def _guess_type(filename: str) -> str | None:
    return mimetypes.guess_type(filename)[0]


# --------------------------------------------------------------------------- #
# URL
# --------------------------------------------------------------------------- #
def build_url(base_url: str, token: str, method: str, *, business: bool = False) -> str:
    """ساخت URL کامل درخواست: ``{base}/bot{token}/{method}``."""
    prefix = "business/bot" if business else "bot"
    return f"{base_url.rstrip('/')}/{prefix}{quote(token, safe=':')}/{method}"


# --------------------------------------------------------------------------- #
# سریالایز (پایتون → JSON)
# --------------------------------------------------------------------------- #
def dump_value(
    value: Any,
    uploads: dict[str, Upload] | None = None,
    counter: itertools.count[int] | None = None,
) -> Any:
    """تبدیل مقدار پایتونی به مقدار قابل سریال‌شدن با JSON.

    Args:
        value: مقدار ورودی (شی داده‌کلاس، لیست، دیکشنری، عدد، رشته، فایل و…).
        uploads: دیکشنری آپلودهای شناسایی‌شده؛ اگر ``None`` باشد فایل توکار (attach)
            مجاز نیست.
        counter: شمارنده‌ی نام یکتای فایل‌های توکار (``file_0``، ``file_1``، …).
    """
    if value is None or isinstance(value, (str, bool, int, float)):
        return value

    if isinstance(value, enum.Enum):
        return dump_value(value.value, uploads, counter)

    if is_uploadable(value):
        if uploads is None or counter is None:
            raise TypeError("ارسال فایل در این موقعیت ممکن نیست")
        name = f"file_{next(counter)}"
        uploads[name] = to_upload(value)
        return f"{ATTACH_PREFIX}{name}"

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        result: dict[str, Any] = {}
        for field in dataclasses.fields(value):
            raw = getattr(value, field.name)
            if raw is None:
                continue
            key = field.metadata.get("api", field.name)
            result[key] = dump_value(raw, uploads, counter)
        return result

    if isinstance(value, Mapping):
        return {str(key): dump_value(item, uploads, counter) for key, item in value.items()}

    if isinstance(value, (list, tuple, set, frozenset)):
        return [dump_value(item, uploads, counter) for item in value]

    raise TypeError(f"مقدار قابل سریال‌شدن نیست: {type(value)!r}")


def dump_params(params: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Upload]]:
    """آماده‌سازی پارامترهای متد برای ارسال.

    Returns:
        ``(data, files)`` — ``data`` داده‌های JSONی و ``files`` آپلودهای سطح بالا؛
        اگر ``files`` خالی نباشد درخواست باید multipart ارسال شود.
    """
    counter = itertools.count()
    uploads: dict[str, Upload] = {}
    data: dict[str, Any] = {}

    for key, value in params.items():
        if value is None:
            continue
        if is_uploadable(value):
            uploads[key] = to_upload(value)
            continue
        dumped = dump_value(value, uploads, counter)
        if dumped is None:
            continue
        data[key] = dumped

    return data, uploads


def json_default(value: Any) -> Any:
    """مقادیر پیش‌فرض برای سریال‌ساز JSON در ابزارهایی مانند لاگ‌گیری."""
    if isinstance(value, enum.Enum):
        return value.value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dump_value(value)
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", "replace")
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


# --------------------------------------------------------------------------- #
# دی‌سریالایز (JSON → پایتون)
# --------------------------------------------------------------------------- #
_HINTS_CACHE: dict[type, dict[str, Any]] = {}
_NONE_TYPE = type(None)


def type_hints(cls: type) -> dict[str, Any]:
    """دریافت type hints حل‌شده‌ی یک کلاس (با کش)."""
    cached = _HINTS_CACHE.get(cls)
    if cached is None:
        cached = typing.get_type_hints(cls)
        _HINTS_CACHE[cls] = cached
    return cached


def _is_union(origin: Any) -> bool:
    return origin is Union or origin is _py_types.UnionType


def load_value(annotation: Any, data: Any) -> Any:
    """تبدیل داده‌ی خام JSON به نوع پایتونی مطابق annotation داده‌شده.

    رفتار عمداً «سخاوتمندانه» است: اگر ساختار با نوع مورد انتظار نخواند، مقدار
    خام برگردانده می‌شود تا به‌روزرسانی‌های بعدی API سرور بازو کتابخانه را از کار
    نیندازد.
    """
    if data is None or annotation is None:
        return None

    origin = typing.get_origin(annotation)

    if _is_union(origin):
        for arg in typing.get_args(annotation):
            if arg is _NONE_TYPE:
                continue
            try:
                return load_value(arg, data)
            except (TypeError, ValueError, KeyError):
                continue
        return data

    if origin in (list, tuple, set, frozenset, cabc.Sequence, cabc.MutableSequence):
        args = typing.get_args(annotation)
        if not isinstance(data, (list, tuple)):
            return data
        if not args:
            return list(data)
        inner = args[0]
        builder = list if origin in (list, cabc.Sequence, cabc.MutableSequence) else origin
        return builder(load_value(inner, item) for item in data)

    if origin in (dict, cabc.Mapping, cabc.MutableMapping):
        args = typing.get_args(annotation)
        value_annotation = args[1] if len(args) > 1 else Any
        if not isinstance(data, Mapping):
            return data
        return {key: load_value(value_annotation, item) for key, item in data.items()}

    if isinstance(annotation, type):
        if dataclasses.is_dataclass(annotation):
            if not isinstance(data, Mapping):
                return data
            return annotation.from_dict(data)
        if issubclass(annotation, enum.Enum):
            try:
                return annotation(data)
            except ValueError:
                return data
        if annotation is bool:
            return data if isinstance(data, bool) else bool(data)
        if annotation is int:
            if isinstance(data, str) and data.strip().lstrip("-").isdigit():
                return int(data)
            return data
        if annotation is float:
            if isinstance(data, (int, float)) and not isinstance(data, bool):
                return float(data)
            return data

    return data
