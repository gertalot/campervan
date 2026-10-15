from dataclasses import FrozenInstanceError

import pytest

from campervan.settings import Settings, load_settings


def test_defaults_use_loopback_and_disable_development() -> None:
    settings = load_settings({})
    assert settings == Settings()
    assert (settings.api_host, settings.api_port) == ("127.0.0.1", 8000)
    assert (settings.viewer_host, settings.viewer_port) == ("127.0.0.1", 3939)
    assert (settings.ui_host, settings.ui_port) == ("127.0.0.1", 5173)
    assert settings.development is False
    assert settings.publication_timeout_s == 30.0
    assert settings.viewer_url == "http://127.0.0.1:3939/viewer"


def test_environment_overrides_share_one_settings_boundary() -> None:
    settings = load_settings(
        {
            "CAMPERVAN_API_HOST": "localhost",
            "CAMPERVAN_API_PORT": "8001",
            "CAMPERVAN_VIEWER_HOST": "localhost",
            "CAMPERVAN_VIEWER_PORT": "3940",
            "CAMPERVAN_UI_HOST": "localhost",
            "CAMPERVAN_UI_PORT": "5174",
            "CAMPERVAN_DEV": "true",
        }
    )
    assert (settings.api_host, settings.api_port) == ("localhost", 8001)
    assert (settings.viewer_host, settings.viewer_port) == ("localhost", 3940)
    assert (settings.ui_host, settings.ui_port) == ("localhost", 5174)
    assert settings.development is True
    assert settings.viewer_url == "http://localhost:3940/viewer"


@pytest.mark.parametrize("variable", ["CAMPERVAN_API_PORT", "CAMPERVAN_VIEWER_PORT", "CAMPERVAN_UI_PORT"])
@pytest.mark.parametrize("port", ["0", "-1", "65536", "1.5", "invalid", ""])
def test_rejects_invalid_configured_ports(variable: str, port: str) -> None:
    with pytest.raises(ValueError, match=variable):
        load_settings({variable: port})


@pytest.mark.parametrize("port", ["1", "65535"])
def test_accepts_port_boundaries(port: str) -> None:
    assert load_settings({"CAMPERVAN_API_PORT": port}).api_port == int(port)


@pytest.mark.parametrize("flag", ["false", "0", "off", "no"])
def test_false_development_flags(flag: str) -> None:
    assert load_settings({"CAMPERVAN_DEV": flag}).development is False


def test_invalid_development_flag_fails_visibly() -> None:
    with pytest.raises(ValueError, match="CAMPERVAN_DEV"):
        load_settings({"CAMPERVAN_DEV": "maybe"})


def test_uses_process_environment_when_not_supplied(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAMPERVAN_VIEWER_PORT", "4000")
    assert load_settings().viewer_port == 4000


def test_settings_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        Settings().api_port = 9000
