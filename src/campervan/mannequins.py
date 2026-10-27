"""Saved browser mannequin poses, independent of the CAD geometry."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

MannequinMode = Literal["seated", "lying", "lying-second"]


class MannequinPose(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    mode: MannequinMode
    visible: bool
    x: float
    y: float
    z: float
    facing: float
    compression: float
    lean: float
    curvature: float
    headTilt: float
    hip: float
    knee: float
    shoulder: float
    elbow: float
    autoLegs: bool
    fitSeat: bool
    poseVersion: Literal[2]


class MannequinSettings(BaseModel):
    version: Literal[1]
    visible: bool
    poses: dict[MannequinMode, MannequinPose]

    @model_validator(mode="after")
    def complete_poses(self) -> Self:
        if set(self.poses) != {"seated", "lying", "lying-second"}:
            raise ValueError("Mannequin settings must include all three poses")
        if any(mode != pose.mode for mode, pose in self.poses.items()):
            raise ValueError("Each mannequin pose must match its mode")
        return self
