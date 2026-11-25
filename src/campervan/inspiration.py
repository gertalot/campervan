"""Manage the local gallery of reference photographs."""

import json
from pathlib import Path
from typing import Annotated, NotRequired, TypedDict

from fastapi import Body, FastAPI, HTTPException
from fastapi import Path as RoutePath
from fastapi.staticfiles import StaticFiles

PhotoId = Annotated[str, RoutePath(pattern=r"^[0-9a-f]{16}$")]


class Photo(TypedDict):
    id: str
    title: str
    source: str
    tags: list[str]
    description: NotRequired[str]
    credit: NotRequired[str]
    favourite: NotRequired[bool]


def register_inspiration(app: FastAPI, directory: Path) -> None:
    images = directory / "images"
    catalogue_path = directory / "catalogue.json"
    route = "/api/v1/inspiration"

    def read_catalogue() -> list[Photo]:
        return json.loads(catalogue_path.read_text(encoding="utf-8"))

    @app.get(route)
    async def gallery() -> list[Photo]:
        return [photo for photo in read_catalogue() if (images / f"{photo['id']}.webp").is_file()]

    @app.put(f"{route}/{{photo_id}}/favourite")
    async def set_favourite(photo_id: PhotoId, favourite: Annotated[bool, Body(embed=True)]) -> bool:
        catalogue = read_catalogue()
        photo = next((entry for entry in catalogue if entry["id"] == photo_id), None)
        if photo is None or not (images / f"{photo_id}.webp").is_file():
            raise HTTPException(status_code=404, detail="Photo no longer in the gallery.")
        if photo.get("favourite", False) != favourite:
            photo["favourite"] = favourite
            temporary = catalogue_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temporary.replace(catalogue_path)
        return favourite

    @app.delete(f"{route}/{{photo_id}}")
    async def remove_photo(photo_id: PhotoId) -> None:
        (images / f"{photo_id}.webp").unlink(missing_ok=True)

    app.mount(f"{route}/images", StaticFiles(directory=images, check_dir=False), name="inspiration-images")
