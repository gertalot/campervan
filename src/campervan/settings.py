"""Single boundary for process environment and CLI-supplied setting values."""

import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    viewer_host: str = "127.0.0.1"
    viewer_port: int = 3939
    ui_host: str = "127.0.0.1"
    ui_port: int = 5173
    development: bool = False
    publication_timeout_s: float = 30.0

    @property
    def viewer_url(self) -> str:
        return f"http://{self.viewer_host}:{self.viewer_port}/viewer"


def _port(environ: Mapping[str, str], name: str, default: int) -> int:
    try:
        value = int(environ.get(name, str(default)))
    except ValueError as error:
        raise ValueError(f"{name} must be an integer from 1 to 65535") from error
    if not 1 <= value <= 65535:
        raise ValueError(f"{name} must be an integer from 1 to 65535")
    return value


def _development(environ: Mapping[str, str]) -> bool:
    value = environ.get("CAMPERVAN_DEV", "false").strip().lower()
    if value in {"true", "1", "yes", "on"}:
        return True
    if value in {"false", "0", "no", "off"}:
        return False
    raise ValueError("CAMPERVAN_DEV must be true or false")


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    values = os.environ if environ is None else environ
    defaults = Settings()
    return Settings(
        api_host=values.get("CAMPERVAN_API_HOST", defaults.api_host),
        api_port=_port(values, "CAMPERVAN_API_PORT", defaults.api_port),
        viewer_host=values.get("CAMPERVAN_VIEWER_HOST", defaults.viewer_host),
        viewer_port=_port(values, "CAMPERVAN_VIEWER_PORT", defaults.viewer_port),
        ui_host=values.get("CAMPERVAN_UI_HOST", defaults.ui_host),
        ui_port=_port(values, "CAMPERVAN_UI_PORT", defaults.ui_port),
        development=_development(values),
    )
