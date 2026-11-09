"""Private, in-process RTAB-Map operations used by Campervan's scan worker."""

from typing import TypedDict

from ._native import _run_export, _run_reprocess, build_info


class NativeBuildInfo(TypedDict):
    rtabmap_version: str
    opencv_version: str
    pcl_version: str
    g2o_available: bool
    csparse_available: bool
    build_id: str
    version_text: str


__all__ = ["NativeBuildInfo", "build_info", "_run_export", "_run_reprocess"]
