"""Send geometry to the local OCP viewer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from campervan.settings import Settings

if TYPE_CHECKING:
    from build123d import Compound


def publish_model(model: Compound, settings: Settings) -> None:
    import ocp_viewer  # type: ignore[import-untyped]

    ocp_viewer.set_port(settings.viewer_port, settings.viewer_host)
    ocp_viewer.show(model, reset_camera=ocp_viewer.Camera.RESET, zoom=0.65, theme="dark")
