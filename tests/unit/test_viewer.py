"""Public viewer boundary behavior with no viewer service."""

import importlib
import warnings
from unittest.mock import Mock

import ocp_viewer as ocp
import pytest

from campervan.settings import Settings


def adapter():
    return importlib.import_module("campervan.viewer")


def test_publishes_only_after_ready_with_explicit_destination_and_kept_camera(monkeypatch):
    viewer = adapter()
    cube = object()
    calls = []
    monkeypatch.setattr(ocp, "set_port", lambda *args: calls.append(("port", args)))
    statuses = iter([{}, None, {"_splash": True}])
    monkeypatch.setattr(ocp, "status", lambda: next(statuses))
    monkeypatch.setattr(viewer.time, "sleep", lambda seconds: calls.append(("sleep", seconds)))
    show = Mock()
    monkeypatch.setattr(ocp, "show", show)
    viewer.publish_cube(cube, Settings(viewer_host="localhost", viewer_port=4567))
    assert calls == [("port", (4567, "localhost")), ("sleep", 0.1), ("sleep", 0.1)]
    show.assert_called_once_with(cube, names=["Cube"], reset_camera=ocp.Camera.KEEP)


def test_missing_browser_status_times_out_without_show(monkeypatch):
    viewer = adapter()
    monkeypatch.setattr(ocp, "set_port", Mock())
    monkeypatch.setattr(ocp, "status", lambda: {})
    elapsed = [0.0]
    monkeypatch.setattr(viewer.time, "monotonic", lambda: elapsed[0])
    monkeypatch.setattr(viewer.time, "sleep", lambda seconds: elapsed.__setitem__(0, elapsed[0] + seconds))
    show = Mock()
    monkeypatch.setattr(ocp, "show", show)
    with pytest.raises(viewer.PublicationError, match="ready") as error:
        viewer.publish_cube(object(), Settings())
    assert error.value.stage == "publication"
    assert 10 <= elapsed[0] < 10.2
    show.assert_not_called()


@pytest.mark.parametrize("operation", ["status", "show"])
def test_transport_warnings_fail_publication_and_filter_is_scoped(monkeypatch, operation):
    viewer = adapter()
    monkeypatch.setattr(ocp, "set_port", Mock())
    monkeypatch.setattr(ocp, "status", lambda: {"_splash": False})
    monkeypatch.setattr(ocp, "show", Mock())

    def warn(*args, **kwargs):
        warnings.warn("Cannot reach a viewer on port 3939: refused", UserWarning, stacklevel=2)

    monkeypatch.setattr(ocp, operation, warn)
    with pytest.raises(viewer.PublicationError, match="Cannot reach"):
        viewer.publish_cube(object(), Settings())
    with pytest.warns(UserWarning, match="Cannot reach"):
        warnings.warn("Cannot reach a viewer on port 3939: refused", UserWarning, stacklevel=2)


@pytest.mark.parametrize("operation", ["set_port", "status", "show"])
def test_public_api_errors_propagate_as_publication_failures(monkeypatch, operation):
    viewer = adapter()
    monkeypatch.setattr(ocp, "set_port", Mock())
    monkeypatch.setattr(ocp, "status", lambda: {"_splash": False})
    monkeypatch.setattr(ocp, "show", Mock())
    failure = ValueError("controlled failure")

    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(ocp, operation, fail)
    with pytest.raises(viewer.PublicationError, match="controlled failure") as error:
        viewer.publish_cube(object(), Settings())
    assert error.value.__cause__ is failure


def test_selected_ocp_release_connection_warning_is_converted_without_a_service():
    import socket

    viewer = adapter()
    # Reserve an unused port without listening: no server is started.
    with socket.socket() as unavailable:
        unavailable.bind(("127.0.0.1", 0))
        port = unavailable.getsockname()[1]
        with pytest.raises(viewer.PublicationError, match="Cannot reach a viewer on port") as error:
            viewer.publish_cube(object(), Settings(viewer_port=port))
    assert isinstance(error.value.__cause__, UserWarning)
