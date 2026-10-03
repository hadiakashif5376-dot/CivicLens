from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./civiclens.db"
    officer_email: str = ""
    officer_password: str = ""
    display_tz: str = "Asia/Karachi"

    @property
    def is_demo_storage(self) -> bool:
        """SQLite on Streamlit Community Cloud is wiped whenever the app restarts."""
        return self.database_url.startswith("sqlite")


def _text(values: Mapping, key: str, default: str) -> str:
    value = values.get(key)
    return str(value).strip() if value not in (None, "") else default


def from_mapping(values: Mapping) -> Settings:
    """Build settings from any mapping, such as environment variables or Streamlit secrets."""
    defaults = Settings()
    return Settings(
        database_url=_text(values, "DATABASE_URL", defaults.database_url),
        officer_email=_text(values, "OFFICER_EMAIL", "").lower(),
        officer_password=_text(values, "OFFICER_PASSWORD", ""),
        display_tz=_text(values, "DISPLAY_TZ", defaults.display_tz),
    )
