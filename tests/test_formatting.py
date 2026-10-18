"""تست قواعد قالب‌بندی متن بله."""

from __future__ import annotations

from baleRobot import bold, escape_markdown, inline_note, italic, link


def test_bold_adds_spaces_inside_stars() -> None:
    # طبق مستندات: باید قبل از ستاره‌ی اول و بعد از ستاره‌ی دوم فاصله باشد
    assert bold("متن") == " * متن * "


def test_italic_adds_spaces_inside_underscores() -> None:
    assert italic("متن") == " _ متن _ "


def test_link_has_no_space_between_text_and_url() -> None:
    assert link("متن", "https://ble.ir") == "[متن](https://ble.ir)"


def test_inline_note_format() -> None:
    assert inline_note("متن", "توضیح") == "```[متن]توضیح```"


def test_escape_markdown_escapes_specials() -> None:
    escaped = escape_markdown("تست * _ [ ]")
    assert "\\*" in escaped
    assert "\\_" in escaped
    assert "\\[" in escaped


def test_combined_formatting() -> None:
    text = f"{bold('سلام')} {link('لینک', 'https://ble.ir')}"
    assert text == " * سلام *  [لینک](https://ble.ir)"
