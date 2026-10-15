"""Send geometry to the local OCP viewer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from campervan.settings import Settings

if TYPE_CHECKING:
    from build123d import Part


def publish_cube(cube: Part, settings: Settings) -> None:
    import ocp_viewer  # type: ignore[import-untyped]

    ocp_viewer.set_port(settings.viewer_port, settings.viewer_host)
    ocp_viewer.show(cube, names=["Cube"], reset_camera=ocp_viewer.Camera.KEEP)
