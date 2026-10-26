"""Capture and replay the installed OCP viewer protocol."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Literal

from campervan.model_cache import ModelBundle
from campervan.parameters import Parameters
from campervan.settings import Settings

if TYPE_CHECKING:
    from build123d import Compound


def build_viewer_frames(model: Compound, parameters: Parameters) -> list[tuple[Literal["B", "D", "S"], str]]:
    """Use OCP's transport interface to capture a complete show, without a viewer connection."""
    import orjson
    from ocp_viewer_core.codec import default  # type: ignore[import-untyped]
    from ocp_viewer_core.comms import Comms, Session  # type: ignore[import-untyped]
    from ocp_viewer_core.config import Camera, Config  # type: ignore[import-untyped]
    from ocp_viewer_core.show import Viewer  # type: ignore[import-untyped]

    class BundleComms(Comms[None]):  # type: ignore[misc]
        def __init__(self) -> None:
            super().__init__()
            self.frames: list[tuple[Literal["B", "D", "S"], str]] = []

        def capture(self, kind: Literal["B", "D", "S"], data: Any) -> None:
            self.frames.append((kind, orjson.dumps(data, default=default, option=orjson.OPT_SERIALIZE_NUMPY).decode()))

        def send_data(self, data: Any, timeit: bool = False) -> None:
            self.capture("D", data)

        def send_backend(self, data: Any, timeit: bool = False) -> None:
            self.capture("B", data)

        def send_config(self, config: Any, timeit: bool = False) -> None:
            self.capture("S", config)

        def status(self) -> dict[str, Any]:
            return {}

        def workspace_config(self) -> dict[str, Any]:
            return {"_splash": False}

        def send_command(self, data: Any, timeit: bool = False) -> Any:
            raise ValueError(f"Unexpected viewer command while saving a model: {data}")

    transport = BundleComms()
    viewer = Viewer(Config(Session(transport), exclude_keys=()))
    viewer.show(model, reset_camera=Camera.KEEP, theme="dark", grid=False, tools=False, glass=False)
    transport.send_data(motion_data(parameters))
    return transport.frames


def replay_model(bundle: ModelBundle, settings: Settings) -> None:
    """Deliver the saved messages in order, using the existing OCP socket and measurement backend."""
    from websockets.sync.client import connect

    with connect(f"ws://{settings.viewer_host}:{settings.viewer_port}") as socket:
        # Load exact measurement shapes before displaying their matching mesh.
        for kind, payload in sorted(bundle.frames, key=lambda frame: frame[0] != "B"):
            socket.send(f"{kind}:{payload}")
            if kind == "B" and not json.loads(socket.recv()).get("ok"):
                raise RuntimeError("CAD viewer did not accept the saved measurement geometry")


def motion_data(parameters: Parameters) -> dict[str, Any]:
    from campervan.cad.bed_motion import bed_keyframes
    from campervan.cad.body import sliding_door_offset
    from campervan.cad.cabinet_doors import cabinet_door_motions
    from campervan.cad.cushions import cushion_motion_tracks
    from campervan.cad.gear import gear_motions
    from campervan.cad.mirror import mirror_motion_tracks
    from campervan.cad.sliding_bed import long_bed_layout

    drawer = "/Campervan/Long bench/Rear drawer"
    # The host applies independent translations and hinge rotations relative to the published CAD pose.
    return {
        "type": "campervan_motion",
        "motions": {
            **gear_motions(parameters),
            **cabinet_door_motions(parameters),
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
            "bed_extension_percent": {
                "position": parameters.bed_extension_percent,
                "tracks": mirror_motion_tracks(
                    [
                        {
                            "path": "/Campervan/Long bench/Sliding bed/Sliding assembly",
                            "axis": "x",
                            "keyframes": bed_keyframes(long_bed_layout(parameters).travel),
                        },
                        *cushion_motion_tracks(parameters, "bed_extension_percent"),
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
