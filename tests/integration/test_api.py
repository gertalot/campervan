"""A small in-process smoke test; the viewer stays a manual visual check."""

import asyncio

import httpx

from campervan.api import build_app
from campervan.settings import Settings


def test_api_smoke():
    async def regenerate(parameters, settings):
        pass

    async def scenario():
        app = build_app(Settings(), regenerate)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
                initial = (await client.get("/api/v1/parameters")).json()
                assert initial["parameters"]["cargo_width_mm"] == 1500
                changed = initial["parameters"] | {"cargo_width_mm": 1600}
                assert initial["session_id"]
                assert (await client.get("/api/v1/model/status")).json()["state"] == "idle"

                applied = await client.put("/api/v1/parameters", json=changed)
                assert applied.status_code == 202
                await asyncio.sleep(0)
                assert (await client.get("/api/v1/model/status")).json()["published_revision"] == 1
                assert (await client.get("/api/v1/parameters")).json()["parameters"] == changed

                invalid = await client.put("/api/v1/parameters", json=changed | {"arch_radius_mm": 300})
                assert invalid.status_code == 422
                assert (await client.get("/api/v1/parameters")).json()["parameters"] == changed
                assert (await client.get("/api/v1/model/status")).json()["requested_revision"] == 1

                regenerated = await client.post("/api/v1/model/regenerate")
                assert regenerated.status_code == 202
                await asyncio.sleep(0)
                final = (await client.get("/api/v1/model/status")).json()
                assert final["state"] == "ready" and final["published_revision"] == 2

    asyncio.run(scenario())
