"""Send geometry to the local OCP viewer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from campervan.parameters import Parameters
from campervan.settings import Settings

if TYPE_CHECKING:
    from build123d import Compound


def publish_model(model: Compound, settings: Settings, parameters: Parameters) -> None:
    import ocp_viewer  # type: ignore[import-untyped]

    from campervan.cad.bed_motion import bed_keyframes
    from campervan.cad.body import sliding_door_offset
    from campervan.cad.cross_bed import cross_bed_layout
    from campervan.cad.cushions import cushion_motion_tracks
    from campervan.cad.mirror import mirror_motion_tracks
    from campervan.cad.sliding_bed import long_bed_layout

    ocp_viewer.set_port(settings.viewer_port, settings.viewer_host)
    ocp_viewer.show(model, reset_camera=ocp_viewer.Camera.KEEP, theme="dark", grid=False, tools=False, glass=False)
    drawer = "/Campervan/Long bench/Rear drawer"
    # The host applies independent translations and hinge rotations relative to the published CAD pose.
    ocp_viewer.comms.send_data(
        {
            "type": "campervan_motion",
            "motions": {
                "doors_close_percent": {
                    "position": parameters.doors_close_percent,
                    "tracks": [
                        {
                            "path": f"/Campervan/Vehicle references/Sliding doors/{side.title()} door",
                            "axis": axis,
                            "keyframes": [
                                (percent, sliding_door_offset(parameters, percent, side == "right")[index])
                                for percent in (0, 85, 100)
                            ],
                        }
                        for side in ("left", "right")
                        for index, axis in enumerate(("x", "y"))
                    ],
                },
                "cross_lid_open_percent": {
                    "position": parameters.cross_lid_open_percent,
                    "tracks": mirror_motion_tracks(
                        [
                            {
                                "path": "/Campervan/Cross bench/Storage lid",
                                "axis": "x",
                                "kind": "rotation",
                                "travel": -70,
                            }
                        ]
                    ),
                },
                "bed_extension_percent": {
                    "position": parameters.bed_extension_percent,
                    "tracks": mirror_motion_tracks(
                        [
                            {
                                "path": "/Campervan/Long bench/Sliding bed/Sliding assembly",
                                "axis": "x",
                                "keyframes": bed_keyframes(long_bed_layout(parameters).travel),
                            },
                            {
                                "path": "/Campervan/Cross bench/Sliding assembly",
                                "axis": "x",
                                "keyframes": bed_keyframes(cross_bed_layout(parameters).travel),
                            },
                            *cushion_motion_tracks(parameters),
                        ]
                    ),
                },
                "drawer_extension_percent": {
                    "position": parameters.drawer_extension_percent,
                    "tracks": mirror_motion_tracks(
                        [
                            {"path": f"{drawer}/Tray", "axis": "y", "travel": -parameters.slide_travel_mm},
                            {
                                "path": f"{drawer}/Rails/Intermediate",
                                "axis": "y",
                                "travel": -parameters.slide_travel_mm / 2,
                            },
                            {"path": f"{drawer}/Rails/Moving", "axis": "y", "travel": -parameters.slide_travel_mm},
                        ]
                    ),
                },
            },
        }
    )
