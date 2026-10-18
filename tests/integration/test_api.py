"""A small in-process smoke test; the viewer stays a manual visual check."""

import asyncio

import httpx

from campervan.api import build_app
from campervan.settings import Settings


def test_api_smoke(tmp_path):
    async def regenerate(parameters, settings):
        generated.append(parameters)

    generated = []

    async def scenario():
        app = build_app(Settings(), regenerate, tmp_path / "project.json")
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
                await client.patch("/api/v1/model/position", json={"drawer_extension_percent": 40})
                positions = (await client.get("/api/v1/parameters")).json()["parameters"]
                assert positions["bed_extension_percent"] == 75 and positions["drawer_extension_percent"] == 40
                lid = await client.patch("/api/v1/model/position", json={"cross_lid_open_percent": 80})
                assert lid.status_code == 200
                assert lid.json() == {
                    "bed_extension_percent": 75,
                    "drawer_extension_percent": 40,
                    "cross_lid_open_percent": 80,
                    "doors_close_percent": 0,
                }
                doors = await client.patch("/api/v1/model/position", json={"doors_close_percent": 100})
                assert doors.json()["doors_close_percent"] == 100
                assert len(generated) == 1
                assert (
                    await client.patch("/api/v1/model/position", json={"bed_extension_percent": 101})
                ).status_code == 422

                regenerated = await client.post("/api/v1/model/regenerate")
                assert regenerated.status_code == 202
                await asyncio.sleep(0)
                final = (await client.get("/api/v1/model/status")).json()
                assert final["state"] == "ready" and final["published_revision"] == 2
                assert generated[-1].bed_extension_percent == 75
                assert generated[-1].drawer_extension_percent == 40
                assert generated[-1].cross_lid_open_percent == 80
                assert generated[-1].doors_close_percent == 100

                material = await client.put(
                    "/api/v1/materials",
                    json={
                        "role": "skins",
                        "selection": {"product_id": "tigerply-okoume-4", "measured": {"thickness": 3.8}},
                    },
                )
                assert material.status_code == 202
                await asyncio.sleep(0)
                assert generated[-1].wall_thickness_mm == 3.8
                bom = (await client.get("/api/v1/materials")).json()
                assert bom["selections"]["skins"]["product_id"] == "tigerply-okoume-4"
                # A stale sidebar value cannot override the chosen product.
                stale = (await client.get("/api/v1/parameters")).json()["parameters"] | {"wall_thickness_mm": 7}
                assert (await client.put("/api/v1/parameters", json=stale)).status_code == 202
                assert (await client.get("/api/v1/parameters")).json()["parameters"]["wall_thickness_mm"] == 3.8
                assert (
                    await client.put(
                        "/api/v1/materials",
                        json={
                            "role": "skins",
                            "selection": {"product_id": "missing-product"},
                        },
                    )
                ).status_code == 422

    asyncio.run(scenario())
