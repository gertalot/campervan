"""A small in-process smoke test; the viewer stays a manual visual check."""

import asyncio

import httpx

from campervan.api import build_app
from campervan.settings import Settings


def test_height_preview_adjusts_dependents_and_rejects_invalid_height_before_saving(tmp_path):
    generated = []

    async def regenerate(parameters, settings):
        generated.append(parameters)

    async def scenario():
        path = tmp_path / "project.json"
        app = build_app(Settings(), regenerate, path)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
                initial = (await client.get("/api/v1/parameters")).json()
                assert initial["schema"]["properties"]["platform_height_mm"]["minimum"] == 358
                invalid = initial["parameters"] | {"platform_height_mm": 200}
                preview = (await client.post("/api/v1/parameters/preview", json=invalid)).json()
                assert "wheel arch" in preview["errors"]["platform_height_mm"]
                assert (await client.put("/api/v1/parameters", json=invalid)).status_code == 422
                assert not path.exists() and not generated
                assert (await client.get("/api/v1/parameters")).json()["parameters"] == initial["parameters"]
                lower = initial["parameters"] | {
                    "platform_height_mm": 366,
                    "inside_radius_mm": 5,
                }
                preview = (await client.post("/api/v1/parameters/preview", json=lower)).json()
                assert not preview["errors"] and preview["parameters"]["drawer_height_mm"] == 277
                assert "drawer_height_mm" in preview["adjustments"]
                assert not path.exists() and not generated
                assert (await client.put("/api/v1/parameters", json=lower)).status_code == 202
                await asyncio.sleep(0)
                assert generated[-1].drawer_height_mm == 277

    asyncio.run(scenario())


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
                cross = await client.patch("/api/v1/model/position", json={"cross_bed_extension_percent": 25})
                assert cross.status_code == 200
                assert cross.json()["cross_bed_extension_percent"] == 25
                assert cross.json()["bed_extension_percent"] == 75
                await client.patch("/api/v1/model/position", json={"drawer_extension_percent": 40})
                positions = (await client.get("/api/v1/parameters")).json()["parameters"]
                assert positions["bed_extension_percent"] == 75 and positions["drawer_extension_percent"] == 40
                lid = await client.patch("/api/v1/model/position", json={"cross_lid_open_percent": 80})
                assert lid.status_code == 200
                assert {
                    name: lid.json()[name]
                    for name in (
                        "bed_extension_percent",
                        "drawer_extension_percent",
                        "cross_lid_open_percent",
                        "doors_close_percent",
                    )
                } == {
                    "bed_extension_percent": 75,
                    "drawer_extension_percent": 40,
                    "cross_lid_open_percent": 80,
                    "doors_close_percent": 0,
                }
                doors = await client.patch("/api/v1/model/position", json={"doors_close_percent": 100})
                assert doors.json()["doors_close_percent"] == 100
                assert len(generated) == 1
                cabinet_doors = await client.patch(
                    "/api/v1/model/position",
                    json={
                        "cabinet_upper_doors_open_percent": 100,
                        "cabinet_lower_doors_open_percent": 50,
                        "cabinet_storage_doors_open_percent": 100,
                        "cabinet_front_upper_door_open_percent": 75,
                        "cabinet_storage_upper_doors_open_percent": 80,
                    },
                )
                assert cabinet_doors.status_code == 200
                assert cabinet_doors.json()["cabinet_upper_doors_open_percent"] == 100
                assert cabinet_doors.json()["cabinet_lower_doors_open_percent"] == 50
                assert cabinet_doors.json()["cabinet_storage_doors_open_percent"] == 100
                assert cabinet_doors.json()["cabinet_front_upper_door_open_percent"] == 75
                assert cabinet_doors.json()["cabinet_storage_upper_doors_open_percent"] == 80
                assert len(generated) == 1  # Door sliders do not regenerate CAD.
                gear_positions = {
                    "chair_1_x_mm": 280,
                    "chair_1_y_mm": 450,
                    "chair_1_z_mm": 50,
                    "chair_1_yaw_deg": -90,
                    "solar_bag_y_mm": 35,
                    "chair_2_yaw_deg": 180,
                }
                moved_gear = await client.patch("/api/v1/model/position", json=gear_positions)
                assert moved_gear.status_code == 200
                assert all(moved_gear.json()[key] == value for key, value in gear_positions.items())
                assert (await client.get("/api/v1/model/status")).json()["requested_revision"] == 1
                assert len(generated) == 1
                assert (await client.patch("/api/v1/model/position", json={"chair_1_z_mm": -1})).status_code == 422
                assert (
                    await client.patch("/api/v1/model/position", json={"bed_extension_percent": 101})
                ).status_code == 422
                assert (
                    await client.patch("/api/v1/model/position", json={"cross_bed_extension_percent": 101})
                ).status_code == 422

                regenerated = await client.post("/api/v1/model/regenerate")
                assert regenerated.status_code == 202
                await asyncio.sleep(0)
                final = (await client.get("/api/v1/model/status")).json()
                assert final["state"] == "ready" and final["published_revision"] == 2
                assert generated[-1].bed_extension_percent == 75
                assert generated[-1].cross_bed_extension_percent == 25
                assert generated[-1].drawer_extension_percent == 40
                assert generated[-1].cross_lid_open_percent == 80
                assert generated[-1].doors_close_percent == 100
                assert generated[-1].cabinet_upper_doors_open_percent == 100
                assert generated[-1].cabinet_lower_doors_open_percent == 50
                assert generated[-1].cabinet_storage_doors_open_percent == 100
                assert generated[-1].cabinet_front_upper_door_open_percent == 75
                assert generated[-1].cabinet_storage_upper_doors_open_percent == 80
                assert all(getattr(generated[-1], key) == value for key, value in gear_positions.items())

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
