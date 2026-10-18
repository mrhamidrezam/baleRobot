"""کمک‌تابع‌های قالب‌بندی متن پیام مطابق قواعد بله.

طبق مستندات بازو، متن پیام‌ها به صورت Markdown قالب‌بندی می‌شوند:

* **برجسته**: متن بین دو ستاره، با یک فاصله قبل از ستاره‌ی اول و بعد از ستاره‌ی دوم.
* **ایتالیک/کج**: متن بین دو زیرخط، با یک فاصله قبل از زیرخط اول و بعد از زیرخط دوم.
* **لینک**: ``[متن](آدرس)`` — بدون فاصله بین متن و پرانتز.
* **نمایش آنی**: `` ```[متن]توضیحات``` `` — توضیح تکمیلی زیر متن اصلی.

نمونه:

.. code-block:: python

    from baleRobot import bold, italic, link

    await client.send_message(
        chat_id, f"{bold('سلام')}، شما {link('اینجا', 'https://ble.ir')} هستید"
    )
"""

from __future__ import annotations

import re

__all__ = ["bold", "escape_markdown", "inline_note", "italic", "link"]

_MARKDOWN_SPECIALS = re.compile(r"([_*`\[\]])")


def bold(text: str) -> str:
    """برجسته‌نویسی متن (به فاصله‌های داخل ستاره‌ها دقت کنید)."""
    return f" * {text} * "


def italic(text: str) -> str:
    """کج/ایتالیک کردن متن (تأکید بر بخشی از متن)."""
    return f" _ {text} _ "


def link(text: str, url: str) -> str:
    """ساخت لینک قابل کلیک.

    Args:
        text: متنی که نمایش داده می‌شود.
        url: آدرس لینک (در بله یا هر سایت دیگر).
    """
    return f"[{text}]({url})"


def inline_note(text: str, description: str) -> str:
    """نمایش آنی: متن اصلی همراه با توضیح تکمیلی زیر آن.

    خروجی: `` ```[متن]توضیحات``` ``
    """
    return f"```[{text}]{description}```"


def escape_markdown(text: str) -> str:
    """گریز کاراکترهای ویژه‌ی قالب‌بندی متن.

    .. note::
        مستندات بازو قواعد گریز را به صورت رسمی توضیح نداده است؛ این تابع
        کاراکترهای ``*``، ``_``، `` ` ``، ``[`` و ``]`` را با باک‌اسلش می‌پوشاند
        تا به صورت متن ساده نمایش داده شوند.
    """
    return _MARKDOWN_SPECIALS.sub(r"\\\1", text)
