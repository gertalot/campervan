"""Send geometry to the local OCP viewer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from campervan.parameters import Parameters
from campervan.settings import Settings

if TYPE_CHECKING:
    from build123d import Compound


def publish_model(model: Compound, settings: Settings, parameters: Parameters) -> list[str]:
    import ocp_viewer  # type: ignore[import-untyped]

    from campervan.cad.sliding_bed import long_bed_layout

    ocp_viewer.set_port(settings.viewer_port, settings.viewer_host)
    ocp_viewer.show(model, reset_camera=ocp_viewer.Camera.RESET, zoom=0.65, theme="dark")
    travel = long_bed_layout(parameters).travel
    position = travel * parameters.bed_extension_percent / 100
    animation = ocp_viewer.Animation()
    animation.add_track(
        "/Campervan/Long bench/Sliding bed/Sliding assembly", "tx", [0, 1], [-position, travel - position]
    )
    # OCP initializes the timeline paused; the sidebar scrubs it directly in the browser.
    animation.animate(1)
    animation.set_relative_time(parameters.bed_extension_percent / 100)
    return list(ocp_viewer.get_last_paths())
