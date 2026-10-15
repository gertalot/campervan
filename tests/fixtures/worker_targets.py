"""Picklable targets exercising the parent without CAD or viewer services."""

import os
import time
from multiprocessing.connection import Connection


def authorized(connection: Connection) -> None:
    try:
        request = connection.recv()
        assert request["type"] == "generate"
        assert request["parameters"] == {"size_mm": 150.0}
        assert request["settings"]["viewer_port"] == 4567
        connection.send({"type": "generated"})
        # Any premature publication is observable by the parent's readiness check.
        assert connection.recv() == {"type": "publish"}
        connection.send({"type": "published"})
    finally:
        connection.close()


def generation_error(connection: Connection) -> None:
    connection.recv()
    connection.send({"type": "error", "stage": "generation", "message": "broken CAD"})
    connection.close()


def eof(connection: Connection) -> None:
    connection.recv()
    connection.close()


def child_exit(connection: Connection) -> None:
    connection.recv()
    os._exit(9)


def unexpected(connection: Connection) -> None:
    connection.recv()
    connection.send({"type": "published"})
    connection.close()


def publication_error(connection: Connection) -> None:
    connection.recv()
    connection.send({"type": "generated"})
    connection.recv()
    connection.send({"type": "error", "stage": "publication", "message": "viewer absent"})
    connection.close()


def publication_hang(connection: Connection) -> None:
    connection.recv()
    connection.send({"type": "generated"})
    connection.recv()
    time.sleep(60)


def generation_hang(connection: Connection) -> None:
    connection.recv()
    time.sleep(60)


def published_then_crash(connection: Connection) -> None:
    connection.recv()
    connection.send({"type": "generated"})
    connection.recv()
    connection.send({"type": "published"})
    os._exit(9)


def publication_exit(connection: Connection) -> None:
    connection.recv()
    connection.send({"type": "generated"})
    connection.recv()
    connection.close()


def production_import_error(connection: Connection) -> None:
    import builtins

    from campervan.worker import worker_main

    original = builtins.__import__

    def broken_import(name, *args, **kwargs):
        if name == "campervan.cad.cube":
            raise SyntaxError("controlled CAD import syntax failure")
        return original(name, *args, **kwargs)

    builtins.__import__ = broken_import
    worker_main(connection)


def production_with_observed_publication(connection: Connection) -> None:
    import sys
    from types import ModuleType

    import campervan.viewer
    from campervan.worker import worker_main

    cube_module = ModuleType("campervan.cad.cube")
    cube_module.make_cube = lambda parameters: object()
    sys.modules["campervan.cad.cube"] = cube_module
    campervan.viewer.publish_cube = lambda cube, settings: connection.send({"type": "viewer-called"})
    worker_main(connection)
