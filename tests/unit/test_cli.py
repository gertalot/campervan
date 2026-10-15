"""Inspect foreground commands and the installed reload filter without starting services."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from uvicorn import Config
from uvicorn.supervisors.watchfilesreload import FileFilter

from campervan import cli


def invoke(monkeypatch, arguments):
    monkeypatch.setattr(sys, "argv", ["campervan", *arguments])
    cli.main()


def test_dev_api_excludes_cad_from_actual_uvicorn_reload_filter(monkeypatch):
    monkeypatch.setenv("CAMPERVAN_DEV", "0")
    run = Mock()
    monkeypatch.setattr("uvicorn.run", run)
    invoke(monkeypatch, ["dev-api"])
    args, kwargs = run.call_args
    assert args == ("campervan.api:create_app",)
    assert kwargs["factory"] is True and kwargs["reload"] is True
    assert os.environ["CAMPERVAN_DEV"] == "1"
    directory = Path(cli.__file__).resolve().parent
    assert kwargs["reload_dirs"] == [str(directory)]
    assert kwargs["reload_excludes"] == [str(directory / "cad")]
    filter_ = FileFilter(Config(*args, **kwargs))
    assert filter_(directory / "api.py")
    assert not filter_(directory / "cad" / "cube.py")
    assert not filter_(directory / "cad" / "nested" / "model.py")


def test_serve_disables_development_and_supports_overrides(monkeypatch):
    monkeypatch.setenv("CAMPERVAN_DEV", "1")
    run = Mock()
    monkeypatch.setattr("uvicorn.run", run)
    invoke(monkeypatch, ["serve", "--host", "127.0.0.2", "--port", "8123"])
    assert os.environ["CAMPERVAN_DEV"] == "0"
    assert run.call_args.kwargs == dict(factory=True, host="127.0.0.2", port=8123, workers=1, reload=False)


@pytest.mark.parametrize("command,code", [("viewer", 7), ("dev-ui", 0)])
def test_foreground_commands_use_resolved_settings_and_propagate_exit(monkeypatch, command, code):
    monkeypatch.setenv("CAMPERVAN_API_PORT", "8123")
    monkeypatch.setenv("CAMPERVAN_VIEWER_PORT", "4040")
    monkeypatch.setenv("CAMPERVAN_UI_PORT", "5180")
    run = Mock(return_value=subprocess.CompletedProcess([], code))
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(SystemExit) as exit_:
        invoke(monkeypatch, [command])
    assert exit_.value.code == code
    args, kwargs = run.call_args
    assert kwargs["check"] is False
    if command == "viewer":
        assert args[0] == [sys.executable, "-m", "ocp_viewer", "--host", "127.0.0.1", "--port", "4040"]
    else:
        assert args[0] == ["npm", "--prefix", "frontend", "run", "dev"]
        assert kwargs["env"]["CAMPERVAN_API_TARGET"] == "http://127.0.0.1:8123"
        assert kwargs["env"]["CAMPERVAN_UI_HOST"] == "127.0.0.1"
        assert kwargs["env"]["CAMPERVAN_UI_PORT"] == "5180"


def test_foreground_ctrl_c_returns_interrupt_status(monkeypatch):
    monkeypatch.setattr(subprocess, "run", Mock(side_effect=KeyboardInterrupt))
    with pytest.raises(SystemExit) as exit_:
        invoke(monkeypatch, ["viewer"])
    assert exit_.value.code == 130


def test_serve_rejects_invalid_override_port(monkeypatch):
    monkeypatch.setattr("uvicorn.run", Mock(side_effect=AssertionError("must not start")))
    with pytest.raises(SystemExit) as exit_:
        invoke(monkeypatch, ["serve", "--port", "70000"])
    assert exit_.value.code == 2
