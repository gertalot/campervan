"""Route the OCP viewer protocol to each CAD tab that displays the model."""

from dataclasses import dataclass
from hashlib import sha256
from threading import Lock

import orjson
from ocp_viewer.server.pages import respond  # type: ignore[import-untyped]
from ocp_viewer.server.sockets import _command, _update  # type: ignore[import-untyped]
from ocp_viewer.server.viewer import Viewer  # type: ignore[import-untyped]
from ocp_viewer_core.backend import ViewerBackend  # type: ignore[import-untyped]
from ocp_viewer_core.state import add_port, del_port  # type: ignore[import-untyped]
from websockets.exceptions import ConnectionClosed
from websockets.sync.server import ServerConnection, serve


@dataclass
class Browser:
    viewer: Viewer
    subscribed: bool = False
    revision: int = -1


class ViewerServer:
    def __init__(self, host: str, port: int) -> None:
        self.host = Viewer({"host": host, "port": port})
        self.browsers: dict[ServerConnection, Browser] = {}
        self.model: str | None = None
        self.motion: str | None = None
        self.configs: list[str] = []
        self.measurement_key: bytes | None = None
        self.revision = 0
        # Each connection has its own thread. Registration and publication must reach a tab in order.
        self.lock = Lock()

    def _deliver(self, socket: ServerConnection, browser: Browser, frames: list[str]) -> None:
        try:
            for frame in frames:
                socket.send(frame)
            browser.revision = self.revision
        except ConnectionClosed:
            self.browsers.pop(socket, None)

    def _subscribe(self, socket: ServerConnection, active: bool) -> None:
        browser = self.browsers.get(socket)
        if browser is None:
            if not active:
                return
            browser = Browser(Viewer(self.host.params))
            self.browsers[socket] = browser
        browser.subscribed = active
        if active and self.model is not None and browser.revision != self.revision:
            frames = [self.model, *self.configs]
            if self.motion is not None:
                frames.append(self.motion)
            self._deliver(socket, browser, frames)

    def _publish(self, kind: str, payload: str) -> None:
        # Each CAD tab requests the saved model on first use. An identical replay must
        # leave the other tabs' selection, measurement and camera intact.
        if kind == "D" and (payload == self.model or payload == self.motion):
            return
        frame_type = orjson.loads(payload).get("type") if kind == "D" else None
        if frame_type in {"data", "clear"}:
            self.model = payload
            self.configs.clear()
            self.motion = None
            self.host.splash = False
        elif frame_type == "campervan_motion":
            self.motion = payload
        elif kind == "S":
            self.configs.append(payload)
        self.revision += 1
        for socket, browser in list(self.browsers.items()):
            if browser.subscribed:
                self._deliver(socket, browser, [payload])

    def handle(self, socket: ServerConnection) -> None:
        try:
            for message in socket:
                raw = message.decode() if isinstance(message, bytes) else message
                kind, payload = raw[:1], raw[2:]
                with self.lock:
                    if kind in {"L", "X"}:
                        self._subscribe(socket, kind == "L")
                    elif kind == "U":
                        browser = self.browsers.get(socket)
                        if browser is not None and browser.subscribed:
                            # OCP keeps the active tool on the backend instance. Only its shapes are shared.
                            browser.viewer.backend.model = self.host.backend.model
                            try:
                                _update(browser.viewer, socket, payload)
                            finally:
                                browser.viewer.backend.model = {}
                            self.host.status = browser.viewer.status
                            self.host.browser = socket
                    elif kind == "B":
                        key = sha256(payload.encode()).digest()
                        if key != self.measurement_key:
                            backend = ViewerBackend()
                            backend.load_model(orjson.loads(payload)["model"])
                            self.host.backend = backend
                            self.measurement_key = key
                        socket.send('{"ok":true}')
                    elif kind in {"D", "S"}:
                        self._publish(kind, payload)
                    elif kind == "C":
                        _command(self.host, socket, payload)
        finally:
            with self.lock:
                self.browsers.pop(socket, None)
                if self.host.browser is socket:
                    self.host.browser = None


def serve_viewer(host: str, port: int) -> None:
    room = ViewerServer(host, port)
    with serve(
        room.handle,
        host,
        port,
        process_request=lambda _, request: respond(room.host, request),
        compression=None,
        max_size=None,
    ) as server:
        add_port(port)
        try:
            print(f"OCP viewer listening at http://{host}:{port}/viewer", flush=True)
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            del_port(port)
