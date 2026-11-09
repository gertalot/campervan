"""Photo-texture an Open3D mesh without reconstructing or moving its geometry."""

import shutil
from pathlib import Path

from campervan.scans import ScanSettings, native_command, read_json

OPENMVS_DIRECTORY = Path(".local/tools/openmvs-2.4.0")


def _tool(name: str) -> str:
    installed = shutil.which(name)
    if installed:
        return installed
    local = OPENMVS_DIRECTORY / name
    if local.is_file():
        return str(local.resolve())
    raise ValueError(f"{name} is missing. Install the documented OpenMVS ARM64 release in {OPENMVS_DIRECTORY}.")


def texture_photos(output: Path, settings: ScanSettings, log: Path) -> list[Path]:
    import numpy as np
    from scipy.spatial.transform import Rotation  # type: ignore[import-untyped]

    frames = read_json(output / "frames.json")["frames"]
    poses = read_json(output / "poses.json")["poses"]
    interface, texturer = _tool("InterfaceCOLMAP"), _tool("TextureMesh")
    colmap = output / "working" / "colmap"
    sparse = colmap / "sparse"
    sparse.mkdir(parents=True, exist_ok=True)
    cameras, images = [], []
    for frame in frames:
        node_id = frame["id"]
        k = frame["intrinsics"]
        # InterfaceCOLMAP subtracts 0.5 from COLMAP's principal point to obtain OpenCV coordinates.
        cameras.append(
            f"{node_id} PINHOLE {frame['width']} {frame['height']} "
            f"{k[0]:.12g} {k[4]:.12g} {k[2] + 0.5:.12g} {k[5] + 0.5:.12g}\n"
        )
        world_to_camera = np.linalg.inv(np.asarray(poses[str(node_id)]))
        qx, qy, qz, qw = Rotation.from_matrix(world_to_camera[:3, :3]).as_quat()
        tx, ty, tz = world_to_camera[:3, 3]
        images.append(
            f"{node_id} {qw:.12g} {qx:.12g} {qy:.12g} {qz:.12g} "
            f"{tx:.12g} {ty:.12g} {tz:.12g} {node_id} {node_id}.jpg\n\n"
        )
    (sparse / "cameras.txt").write_text("".join(cameras))
    (sparse / "images.txt").write_text("".join(images))
    (sparse / "points3D.txt").write_text("# No SfM points: texture the supplied Open3D mesh.\n")
    scene = output / "working" / "cameras.mvs"
    rgb_directory = (output / frames[0]["rgb"]).parent
    native_command(
        [interface, "-i", str(colmap), "-o", str(scene), "--image-folder", str(rgb_directory)], log, cwd=scene.parent
    )
    photo = output / "photo"
    photo.mkdir(exist_ok=True)
    native_command(
        [
            texturer,
            "-i",
            str(scene),
            "-m",
            str(output / "mesh.ply"),
            "-o",
            str(photo / "mesh.mvs"),
            "--export-type",
            "obj",
            "--decimate",
            "1",
            "--close-holes",
            "0",
            # OpenMVS 2.4.0's seam samplers corrupt colours (upstream issue #1251).
            # Keep original photographic colours; exposure seams remain visible.
            "--global-seam-leveling",
            "0",
            "--local-seam-leveling",
            "0",
            "--max-texture-size",
            str(settings.texture_size),
        ],
        log,
        cwd=scene.parent,
    )
    assets = sorted(path for path in photo.iterdir() if path.suffix in {".obj", ".mtl", ".png", ".jpg", ".jpeg"})
    if not (photo / "mesh.obj").is_file() or not any(p.suffix == ".mtl" for p in assets):
        raise RuntimeError("OpenMVS did not write the expected photo mesh/material.")
    if not any(p.suffix in {".png", ".jpg", ".jpeg"} for p in assets):
        raise RuntimeError("OpenMVS did not write a photographic texture.")
    return assets
