"""انواع عضویت در گفتگو (چندوجهی بر اساس فیلد ``status``).

مستندات: ChatMember، ChatMemberOwner، ChatMemberAdministrator،
ChatMemberMember و ChatMemberRestricted.

نمونه:

.. code-block:: python

    member = await client.get_chat_member(chat_id, user_id)
    if member.status == "administrator":
        print(member.can_restrict_members)
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypeVar

from .base import BaleObject
from .users import User

__all__ = [
    "ChatMember",
    "ChatMemberAdministrator",
    "ChatMemberMember",
    "ChatMemberOwner",
    "ChatMemberRestricted",
]

_T = TypeVar("_T", bound="ChatMember")


@dataclass
class ChatMember(BaleObject):
    """اطلاعات یک عضو گفتگو.

    وضعیت‌های پشتیبانی‌شده: ``creator``، ``administrator``، ``member`` و
    ``restricted``. برای وضعیت‌های ناشناخته (مانند ``left`` یا ``banned``) همین
    کلاس پایه برگردانده می‌شود تا پاسخ سرور از بین نرود.
    """

    status: str = ""
    user: User | None = None

    @classmethod
    def from_dict(cls: type[_T], data: Mapping[str, Any] | None) -> _T:
        """ساخت شیء مناسب بر اساس مقدار فیلد ``status``."""
        if cls is ChatMember and isinstance(data, Mapping):
            target = _MEMBER_TYPES.get(str(data.get("status", "")).lower())
            if target is not None and target is not ChatMember:
                return target.from_dict(data)  # type: ignore[return-value]
        return super().from_dict(data)


@dataclass
class ChatMemberOwner(ChatMember):
    """مالک گفتگو؛ همه‌ی دسترسی‌های مدیریتی را دارد."""

    status: str = "creator"


@dataclass
class ChatMemberAdministrator(ChatMember):
    """عضوی با دسترسی‌های مدیریتی."""

    status: str = "administrator"
    can_delete_messages: bool | None = None
    can_manage_video_chats: bool | None = None
    can_restrict_members: bool | None = None
    can_promote_members: bool | None = None
    can_change_info: bool | None = None
    can_invite_users: bool | None = None
    can_post_stories: bool | None = None
    can_post_messages: bool | None = None
    can_edit_messages: bool | None = None
    can_pin_messages: bool | None = None


@dataclass
class ChatMemberMember(ChatMember):
    """عضو عادی بدون دسترسی یا محدودیت خاص."""

    status: str = "member"


@dataclass
class ChatMemberRestricted(ChatMember):
    """عضوی با محدودیت‌های ارسال پیام (فقط در سوپرگروه‌ها)."""

    status: str = "restricted"
    is_member: bool | None = None
    can_send_messages: bool | None = None
    can_send_audios: bool | None = None
    can_send_documents: bool | None = None
    can_send_photos: bool | None = None
    can_send_videos: bool | None = None
    can_change_info: bool | None = None
    can_invite_users: bool | None = None
    can_pin_messages: bool | None = None


#: نگاشت وضعیت عضو به کلاس متناظر
_MEMBER_TYPES: dict[str, type[ChatMember]] = {
    "creator": ChatMemberOwner,
    "administrator": ChatMemberAdministrator,
    "member": ChatMemberMember,
    "restricted": ChatMemberRestricted,
}
