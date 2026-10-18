"""ورودی‌های رسانه: آپلود فایل، رسانه‌های گروهی و استیکر.

مستندات: InputFile، InputMediaPhoto/Video/Animation/Audio/Document و
(برای متدهای استیکر) InputSticker.

نمونه ارسال فایل محلی:

.. code-block:: python

    from pathlib import Path
    from baleRobot import InputFile

    await client.send_document(chat_id, Path("report.pdf"))
    await client.send_document(chat_id, InputFile("report.pdf", content_type="application/pdf"))
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, BinaryIO, Union

from .._serializers import Upload, _guess_type
from .base import BaleObject

__all__ = [
    "InputFile",
    "InputMediaAnimation",
    "InputMediaAudio",
    "InputMediaDocument",
    "InputMediaPhoto",
    "InputMediaVideo",
    "InputSticker",
]

FileSource = Union[str, bytes, bytearray, os.PathLike[str], BinaryIO, "InputFile"]


class InputFile:
    """نماینده‌ی یک فایل که باید با ``multipart/form-data`` آپلود شود.

    سه روش ساخت:

    .. code-block:: python

        InputFile("photo.jpg")                  # فایل محلی (رشته مسیر)
        InputFile(Path("photo.jpg"))            # pathlib.Path
        InputFile(b"...", filename="a.png")     # داده‌ی باینری در حافظه
        InputFile(open("a.mp3", "rb"))          # شیء فایل باز

    Args:
        file: منبع فایل (مسیر، bytes یا شیء دارای ``read``).
        filename: نام فایل ارسالی؛ در صورت عدم ارسال از مسیر یا نام شیء استفاده
            می‌شود.
        content_type: نوع MIME فایل؛ در صورت عدم ارسال حدس زده می‌شود.
    """

    #: نشانه‌ای برای سریالایزر کتابخانه (بدون وابستگی ماژولی)
    _bale_upload = True

    __slots__ = ("content", "content_type", "filename")

    def __init__(
        self,
        file: FileSource,
        *,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> None:
        content: bytes
        name: str | None = None

        if isinstance(file, InputFile):
            content = file.content
            name = file.filename
        elif isinstance(file, (bytes, bytearray, memoryview)):
            content = bytes(file)
        elif isinstance(file, str):
            name = os.path.basename(file)
            with open(file, "rb") as handle:
                content = handle.read()
        elif os.PathLike and isinstance(file, os.PathLike):
            path = os.fspath(file)
            name = os.path.basename(path)
            with open(path, "rb") as handle:
                content = handle.read()
        elif hasattr(file, "read"):
            raw = file.read()
            content = raw.encode("utf-8") if isinstance(raw, str) else bytes(raw)
            raw_name = getattr(file, "name", "") or ""
            name = os.path.basename(str(raw_name)) or None
        else:
            raise TypeError(f"منبع فایل پشتیبانی نمی‌شود: {type(file)!r}")

        self.content = content
        self.filename = filename or name or "file.bin"
        self.content_type = content_type or _guess_type(self.filename)

    # ------------------------------------------------------------------ #
    @classmethod
    def from_path(cls, path: str | os.PathLike[str], **kwargs: Any) -> InputFile:
        """ساخت از روی مسیر فایل."""
        return cls(path, **kwargs)

    @classmethod
    def from_bytes(cls, data: bytes, filename: str = "file.bin", **kwargs: Any) -> InputFile:
        """ساخت از روی داده‌ی باینری."""
        return cls(data, filename=filename, **kwargs)

    def to_upload(self) -> Upload:
        """تبدیل به شیء داخلی :class:`~baleRobot._serializers.Upload`."""
        return Upload(filename=self.filename, content=self.content, content_type=self.content_type)

    def __repr__(self) -> str:  # pragma: no cover - ابزاری
        return (
            f"InputFile(filename={self.filename!r}, size={len(self.content)}, "
            f"content_type={self.content_type!r})"
        )

    def __len__(self) -> int:
        return len(self.content)


@dataclass
class InputMediaPhoto(BaleObject):
    """تصویری که باید ارسال شود (برای ``sendMediaGroup``).

    ``media`` می‌تواند ``file_id``، URL یا :class:`InputFile` باشد.
    """

    media: Any
    type: str = "photo"
    caption: str | None = None


@dataclass
class InputMediaVideo(BaleObject):
    """ویدیویی که باید ارسال شود (برای ``sendMediaGroup``)."""

    media: Any
    type: str = "video"
    thumbnail: Any | None = None
    caption: str | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None


@dataclass
class InputMediaAnimation(BaleObject):
    """انیمیشنی که باید ارسال شود (برای ``sendMediaGroup``)."""

    media: Any
    type: str = "animation"
    thumbnail: Any | None = None
    caption: str | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None


@dataclass
class InputMediaAudio(BaleObject):
    """فایل صوتی که باید ارسال شود (برای ``sendMediaGroup``)."""

    media: Any
    type: str = "audio"
    thumbnail: Any | None = None
    caption: str | None = None
    duration: int | None = None
    title: str | None = None


@dataclass
class InputMediaDocument(BaleObject):
    """سندی که باید ارسال شود (برای ``sendMediaGroup``)."""

    media: Any
    type: str = "document"
    thumbnail: Any | None = None
    caption: str | None = None


@dataclass
class InputSticker(BaleObject):
    """اطلاعات استیکری که به بسته‌ی استیکر اضافه می‌شود.

    Args:
        sticker: ``file_id`` یا :class:`InputFile` با فرمت‌های ‎.WEBP‎، ‎.PNG‎،
            ‎.TGS‎ یا ‎.WEBM‎.
        format: قالب استیکر (در صورت پشتیبانی سرور).
        emoji_list: فهرست ایموجی‌های مرتبط با استیکر.
    """

    sticker: Any
    format: str | None = None
    emoji_list: list[str] | None = None
