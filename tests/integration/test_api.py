"""A small in-process smoke test; the viewer stays a manual visual check."""

import asyncio

import httpx

from campervan.api import build_app
from campervan.settings import Settings


def test_api_smoke():
    async def regenerate(parameters, settings):
        generated.append(parameters)
        return ["/Campervan/Vehicle references/Floor outline"]

    generated = []

    async def scenario():
        app = build_app(Settings(), regenerate)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
                initial = (await client.get("/api/v1/parameters")).json()
                assert initial["parameters"]["cargo_width_mm"] == 1500
                assert initial["schema"]["properties"]["cargo_width_mm"]["group"] == [
                    "Vehicle references",
                    "Floor outline",
                ]
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

                moved = await client.patch("/api/v1/model/position", json={"bed_extension_percent": 75})
                assert moved.status_code == 200
                assert (await client.get("/api/v1/parameters")).json()["parameters"]["bed_extension_percent"] == 75
                assert (await client.get("/api/v1/model/status")).json()["requested_revision"] == 1
                assert len(generated) == 1
                assert (
                    await client.patch("/api/v1/model/position", json={"bed_extension_percent": 101})
                ).status_code == 422

                regenerated = await client.post("/api/v1/model/regenerate")
                assert regenerated.status_code == 202
                await asyncio.sleep(0)
                final = (await client.get("/api/v1/model/status")).json()
                assert final["state"] == "ready" and final["published_revision"] == 2
                assert final["model_paths"] == ["/Campervan/Vehicle references/Floor outline"]
                assert generated[-1].bed_extension_percent == 75

    asyncio.run(scenario())
