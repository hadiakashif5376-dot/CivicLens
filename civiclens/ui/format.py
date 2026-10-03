"""Text helpers for the pages. No Streamlit import, so these can be tested on their own."""
import re
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

# Characters that Markdown would act on. Citizens type free text that officers then read,
# so it is escaped before display to stop links, images and formatting from sneaking in.
_MARKDOWN_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+!|<>~$])")


def md_escape(text: Optional[str]) -> str:
    return _MARKDOWN_SPECIAL.sub(r"\\\1", text or "")


def fmt_time(value: Optional[datetime], tz_name: str = "UTC") -> str:
    if value is None:
        return ""
    if value.tzinfo is None:  # SQLite returns naive datetimes; everything is stored as UTC
        value = value.replace(tzinfo=timezone.utc)
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = timezone.utc
    return value.astimezone(tz).strftime("%d %b %Y, %H:%M")
