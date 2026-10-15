"""Publish through OCP's public API, without promising browser delivery."""

from __future__ import annotations

import time
import warnings
from typing import TYPE_CHECKING

from campervan.settings import Settings

if TYPE_CHECKING:
    from build123d import Part


class PublicationError(RuntimeError):
    """The publisher failed or could not establish viewer readiness."""

    stage = "publication"


def publish_cube(cube: Part, settings: Settings) -> None:
    """Replace the scene after readiness; completion is not a rendering acknowledgement."""
    try:
        import ocp_viewer  # type: ignore[import-untyped]

        with warnings.catch_warnings():
            # The selected OCP release reports connection failures as UserWarning
            # subclasses. Match its transport diagnostic without private imports.
            warnings.filterwarnings("error", message=r"Cannot reach a viewer on port .*", category=UserWarning)
            ocp_viewer.set_port(settings.viewer_port, settings.viewer_host)
            deadline = time.monotonic() + 10.0
            while not ocp_viewer.status():
                if time.monotonic() >= deadline:
                    raise PublicationError("Viewer did not become ready within 10 seconds")
                time.sleep(0.1)
            ocp_viewer.show(cube, names=["Cube"], reset_camera=ocp_viewer.Camera.KEEP)
    except PublicationError:
        raise
    except Exception as error:
        raise PublicationError(str(error)) from error
