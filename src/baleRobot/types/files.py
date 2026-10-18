"""انواع مرتبط با فایل‌ها و استیکرها.

مستندات: PhotoSize، Animation، Audio، Document، Video، Voice، File، Sticker، StickerSet.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import BaleObject

__all__ = [
    "Animation",
    "Audio",
    "Document",
    "File",
    "PhotoSize",
    "Sticker",
    "StickerSet",
    "Video",
    "Voice",
]


@dataclass
class PhotoSize(BaleObject):
    """یک اندازه از تصویر یا thumbnail یک فایل."""

    file_id: str = ""
    file_unique_id: str = ""
    width: int = 0
    height: int = 0
    file_size: int | None = None


@dataclass
class Animation(BaleObject):
    """فایل انیمیشن (GIF یا ویدیوی H.264/MPEG-4 AVC بدون صدا)."""

    file_id: str = ""
    file_unique_id: str = ""
    width: int = 0
    height: int = 0
    duration: int = 0
    thumbnail: PhotoSize | None = None
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None


@dataclass
class Audio(BaleObject):
    """فایل صوتی (موسیقی) قابل نمایش در پخش‌کننده‌ی بله."""

    file_id: str = ""
    file_unique_id: str = ""
    duration: int = 0
    title: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None


@dataclass
class Document(BaleObject):
    """سند/فایل عمومی."""

    file_id: str = ""
    file_unique_id: str = ""
    thumbnail: PhotoSize | None = None
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None


@dataclass
class Video(BaleObject):
    """فایل ویدیویی."""

    file_id: str = ""
    file_unique_id: str = ""
    width: int = 0
    height: int = 0
    duration: int = 0
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None


@dataclass
class Voice(BaleObject):
    """پیام صوتی."""

    file_id: str = ""
    file_unique_id: str = ""
    duration: int | None = None
    file_size: int | None = None


@dataclass
class File(BaleObject):
    """فایل آماده دانلود؛ لینک دانلود: ``{base}/file/bot<token>/<file_path>``.

    .. note::
        لینک دانلود یک ساعت اعتبار دارد. برای دریافت لینک از
        :meth:`baleRobot.AsyncBaleClient.file_url` استفاده کنید.
    """

    file_id: str = ""
    file_unique_id: str = ""
    file_size: int | None = None
    file_path: str | None = None


@dataclass
class Sticker(BaleObject):
    """یک استیکر."""

    file_id: str = ""
    file_unique_id: str = ""
    type: str = ""
    width: int = 0
    height: int = 0
    file_size: int | None = None


@dataclass
class StickerSet(BaleObject):
    """یک بسته‌ی استیکر."""

    name: str = ""
    title: str = ""
    stickers: list[Sticker] = field(default_factory=list)
    thumbnail: PhotoSize | None = None
