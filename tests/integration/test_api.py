"""Exercise the ASGI application and lifespan entirely in process."""

import asyncio

import httpx
import pytest

from campervan.api import build_app
from campervan.settings import Settings
from tests.unit.test_coordinator import Factory


def test_api_contract_and_lifespan_session():
    async def scenario():
        factory = Factory()
        app = build_app(Settings(viewer_port=4040), factory)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
                parameters = (await client.get("/api/v1/parameters")).json()
                session = parameters["session_id"]
                assert parameters["parameters"] == {"size_mm": 100}
                assert parameters["viewer_url"] == "http://127.0.0.1:4040/viewer"
                assert parameters["schema"]["properties"]["size_mm"]["unit"] == "mm"
                status = (await client.get("/api/v1/model/status")).json()
                assert status == dict(
                    session_id=session, requested_revision=0, published_revision=None, state="idle", error=None
                )
                assert (await client.get("/api/unknown")).status_code == 404
                mutation = await client.put("/api/v1/parameters", json={"size_mm": 150})
                assert mutation.status_code == 202
                assert mutation.json() == {"session_id": session, "requested_revision": 1}
                worker = await factory.next()
                assert worker.parameters.size_mm == 150
                rejected = await client.put("/api/v1/parameters", json={"size_mm": 0})
                assert rejected.status_code == 422
                assert app.state.coordinator.status().requested_revision == 1
                assert app.state.coordinator.parameters.size_mm == 150
                assert factory.workers.empty()
                regeneration = await client.post("/api/v1/model/regenerate")
                assert regeneration.status_code == 202
                assert regeneration.json()["requested_revision"] == 2
                assert (await client.get("/api/v1/parameters")).json()["parameters"] == {"size_mm": 150}
        assert worker.closed.is_set()
        async with app.router.lifespan_context(app):
            assert app.state.coordinator.session_id != session
            assert app.state.coordinator.status().requested_revision == 0

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "payload",
    [
        "{}",
        '{"size_mm":0}',
        '{"size_mm":-1}',
        '{"size_mm":1001}',
        '{"size_mm":true}',
        '{"size_mm":"150"}',
        '{"size_mm":150,"unknown":1}',
        '{"size_mm":null}',
        '{"size_mm":NaN}',
        '{"size_mm":Infinity}',
        '{"size_mm":-Infinity}',
        "",
    ],
)
def test_invalid_input_returns_422_without_mutation(payload):
    async def scenario():
        factory = Factory()
        app = build_app(Settings(), factory)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
                response = await client.put(
                    "/api/v1/parameters", content=payload, headers={"content-type": "application/json"}
                )
                assert response.status_code == 422
                assert response.json()["detail"]
                assert app.state.coordinator.status().state == "idle"
                assert app.state.coordinator.parameters.size_mm == 100
                assert factory.workers.empty()

    asyncio.run(scenario())


def test_lifespan_shutdown_reaps_active_real_child(monkeypatch):
    from campervan import worker as worker_module
    from tests.fixtures.worker_targets import generation_hang

    async def scenario():
        workers = asyncio.Queue()

        async def factory(parameters, settings):
            worker = await worker_module.start_worker(parameters, settings)
            await workers.put(worker)
            return worker

        monkeypatch.setattr(worker_module, "worker_main", generation_hang)
        app = build_app(Settings(), factory)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
                assert (await client.post("/api/v1/model/regenerate")).status_code == 202
                worker = await asyncio.wait_for(workers.get(), 2)
                assert worker._process.is_alive()
                assert (await client.get("/api/v1/model/status")).json()["state"] == "regenerating"
        assert not worker._process.is_alive()
        assert worker._process.exitcode is not None
        assert worker._connection.closed
        assert all(receive.done() for receive in worker._receives)

    asyncio.run(scenario())


def test_real_worker_publication_timeout_becomes_api_failure(monkeypatch):
    from campervan import worker as worker_module
    from tests.fixtures.worker_targets import publication_hang
    from tests.unit.test_coordinator import completed

    async def scenario():
        workers = []

        async def factory(parameters, settings):
            worker = await worker_module.start_worker(parameters, settings)
            workers.append(worker)
            return worker

        monkeypatch.setattr(worker_module, "worker_main", publication_hang)
        app = build_app(Settings(publication_timeout_s=0.05), factory)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
                await client.post("/api/v1/model/regenerate")
                await asyncio.wait_for(completed(app.state.coordinator), 5)
                status = (await client.get("/api/v1/model/status")).json()
                assert status["state"] == "failed" and status["published_revision"] is None
                assert status["error"] == {"stage": "publication", "message": "Viewer publication timed out"}
                assert not workers[0]._process.is_alive()
                assert workers[0]._connection.closed

    asyncio.run(scenario())
