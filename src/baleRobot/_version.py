"""نسخه کتابخانه baleRobot.

این فایل تنها منبع نسخه است؛ در ``pyproject.ttoml`` با ``[tool.hatch.version]``
خوانده می‌شود و در گردش‌کار انتشار (``publish.yml``) با نشان گیت تطبیق داده می‌شود.
"""

from __future__ import annotations

__version__ = "0.1.0"

#: اطلاعات نسخه به شکل ساخت‌یافته: (major, minor, patch)
VERSION_INFO: tuple[int, int, int] = (0, 1, 0)

__all__ = ["VERSION_INFO", "__version__"]
