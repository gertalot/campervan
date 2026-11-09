"""RTAB-Map 0.24 observations, kept distinct from saved global initial estimates."""

import json
import sqlite3
import struct
import zlib
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict

from campervan.scans import database_info, file_hash, read_json, write_json


class GraphLink(BaseModel):
    from_id: int
    to_id: int
    kind: int
    transform: list[list[float]]
    information: list[list[float]]


class GraphDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1] = 1
    units: Literal["m"] = "m"
    source_sha256: str
    gravity_sigma_rad: float
    poses: dict[str, list[list[float]]]
    links: list[GraphLink]
    optical_transforms: dict[str, list[list[float]]]
    excluded_links: int = 0
    note: str = "Information uses RTAB-Map translation/rotation order; duplicate inverse links counted once."


def rigid(value: Any) -> Any:
    matrix = np.asarray(value, dtype=float)
    if matrix.shape != (4, 4) or not np.isfinite(matrix).all() or not np.allclose(matrix[3], [0, 0, 0, 1]):
        raise ValueError("Invalid rigid graph transform.")
    if not np.allclose(matrix[:3, :3].T @ matrix[:3, :3], np.eye(3), atol=1e-4):
        raise ValueError("Graph transform is not a rotation.")
    if not np.isclose(np.linalg.det(matrix[:3, :3]), 1, atol=1e-4):
        raise ValueError("Graph rotation is reflected.")
    return matrix


def _saved(blob: bytes, dtype: str, kind: int) -> Any:
    rows, columns, mat_type = struct.unpack("<3i", blob[-12:])
    values = np.frombuffer(zlib.decompress(blob[:-12]), dtype=dtype)
    if rows != 1 or mat_type != kind or len(values) != columns:
        raise ValueError("Unsupported RTAB-Map saved graph encoding.")
    return values


def extract_graph(database: Path, optical_poses: dict[str, list[list[float]]]) -> GraphDocument:
    database_info(database)
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as db:
        ids_blob, poses_blob = db.execute("SELECT opt_ids,opt_poses FROM Admin").fetchone()
        ids = _saved(ids_blob, "<i4", 4)
        matrices = _saved(poses_blob, "<f4", 5).reshape(-1, 3, 4)
        if len(ids) != len(matrices):
            raise ValueError("Saved graph IDs and initial poses differ.")
        poses = {
            str(int(key)): rigid(np.vstack([matrix, [0, 0, 0, 1]])).tolist()
            for key, matrix in zip(ids, matrices, strict=True)
        }
        parameters = db.execute("SELECT parameters FROM Info ORDER BY time_enter DESC LIMIT 1").fetchone()
        settings = dict(item.split(":", 1) for item in parameters[0].split(";") if ":" in item) if parameters else {}
        gravity = float(settings.get("Optimizer/GravitySigma", "nan"))
        links: list[GraphLink] = []
        seen: dict[tuple[int, int, int], Any] = {}
        excluded = 0
        for a, b, kind, transform, information in db.execute(
            "SELECT from_id,to_id,type,transform,information_matrix FROM Link ORDER BY from_id,to_id,type"
        ):
            if str(a) not in poses or str(b) not in poses:
                excluded += 1
                continue
            if kind not in {0, 1, 2, 3, 4, 6, 7, 8, 9}:
                raise ValueError(f"Unsupported original graph link type {kind}; analysis cannot discard it.")
            if not transform or len(transform) != 48 or len(information) != 288:
                raise ValueError("Unsupported graph transform or information encoding.")
            matrix = rigid(np.vstack([np.frombuffer(transform, dtype="<f4").reshape(3, 4), [0, 0, 0, 1]]))
            info = np.frombuffer(information, dtype="<f8").reshape(6, 6)
            if not np.isfinite(info).all() or not np.allclose(info, info.T) or np.min(np.linalg.eigvalsh(info)) <= 0:
                raise ValueError("Original graph has a nonpositive information matrix.")
            edge_key = (min(a, b), max(a, b), kind)
            canonical = matrix if a <= b else np.linalg.inv(matrix)
            if edge_key in seen:
                prior_transform, prior_information = seen[edge_key]
                if not np.allclose(prior_transform, canonical, atol=1e-4) or not np.allclose(prior_information, info):
                    raise ValueError("Inverse graph links disagree.")
                continue
            seen[edge_key] = (canonical, info)
            # RTAB-Map Link::inverse() retains its stored information. Keep one original direction unchanged.
            links.append(GraphLink(from_id=a, to_id=b, kind=kind, transform=matrix.tolist(), information=info.tolist()))
    if any(link.kind == 9 for link in links) and (not np.isfinite(gravity) or gravity < 0):
        raise ValueError("Gravity links require the database's recorded Optimizer/GravitySigma.")
    offsets = {}
    for key, matrix in optical_poses.items():
        if key not in poses:
            raise ValueError(f"Exported camera {key} is absent from the saved graph.")
        offsets[key] = (np.linalg.inv(rigid(poses[key])) @ rigid(matrix)).tolist()
    return GraphDocument(
        source_sha256=file_hash(database),
        gravity_sigma_rad=gravity if np.isfinite(gravity) else 0,
        poses=poses,
        links=links,
        optical_transforms=offsets,
        excluded_links=excluded,
    )


def ensure_graph(run: Path) -> GraphDocument:
    path = run / "graph.json"
    if path.is_file():
        return GraphDocument.model_validate_json(path.read_text())
    frames = read_json(run / "frames.json")
    if frames.get("poses_corrected"):
        raise ValueError(
            "The corrected result's original-observation graph is missing; do not infer it from fitted poses."
        )
    graph = extract_graph((run / frames["database"]).resolve(), read_json(run / "poses.json")["poses"])
    temporary = path.with_suffix(".tmp")
    write_json(temporary, json.loads(graph.model_dump_json()))
    temporary.replace(path)
    return graph
