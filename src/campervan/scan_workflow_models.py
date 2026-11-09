"""Persistent scan workflow contracts, separate from physical observations."""

from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Pair(Model):
    tag_a: int = Field(gt=0, strict=True)
    tag_b: int = Field(gt=0, strict=True)

    @model_validator(mode="after")
    def canonical(self):
        if self.tag_a >= self.tag_b:
            raise ValueError("Pairs must have distinct tags in ascending order.")
        return self


class ProfileRef(Model):
    profile_id: str
    revision: int = Field(ge=1, strict=True)


class ReviewedRelationship(Model):
    kind: str
    region_ids: list[str] = Field(default_factory=list)
    enabled: bool = True
    sigma: float | None = Field(default=None, gt=0)
    units: str | None = None
    support: list[str] = Field(default_factory=list)
    minimum_separation_m: float = Field(default=0, ge=0)


class SourcePixel(Model):
    region_id: str = Field(min_length=1)
    frame_id: str = Field(min_length=1)
    pixel: tuple[Annotated[int, Field(ge=0, strict=True)], Annotated[int, Field(ge=0, strict=True)]]


class MatchedBodySupport(Model):
    first: SourcePixel
    second: SourcePixel


class BoundRelationship(ReviewedRelationship):
    # Source-world direction, never an assumed vehicle axis or reusable profile assertion.
    up_direction: tuple[float, float, float] | None = None
    matched_support: list[MatchedBodySupport] = Field(default_factory=list)


class ProfileRevision(Model):
    profile_id: str
    revision: int = Field(ge=1, strict=True)
    layout_id: str
    context_text: str = ""
    target_classes: list[str] = Field(default_factory=list)
    relationships: list[ReviewedRelationship] = Field(default_factory=list)
    tag_references: list[dict[str, Any]] = Field(default_factory=list)


class CleanupMask(Model):
    frame_id: str
    asset: str
    revision: int = Field(ge=0, strict=True)


class RegionSupport(Model):
    frame_id: str = Field(min_length=1)
    asset: str = Field(min_length=1)
    observed_xyz: tuple[float, float, float] | None = None


class ReviewedRegion(Model):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    support: list[RegionSupport] = Field(default_factory=list)
    correction_revision: int = Field(default=0, ge=0, strict=True)
    symmetry_scope: Literal["body", "excluded"] = "excluded"


class PlacementCandidate(Model):
    id: str = Field(min_length=1)
    tag_id: int = Field(gt=0, strict=True)
    region_id: str = Field(min_length=1)
    support_index: int = Field(ge=0, strict=True)
    mounting_confirmed: bool = False
    access_confirmed: bool = False
    interior_confirmed: bool = False
    sigma_m: float = Field(gt=0)
    connects_to: list[Annotated[int, Field(gt=0, strict=True)]] = Field(default_factory=list)


class SourceBinding(Model):
    source_run_id: str
    profile_ref: ProfileRef
    revision: int = Field(ge=0, strict=True)
    regions: list[ReviewedRegion] = Field(default_factory=list)
    masks: list[CleanupMask] = Field(default_factory=list)
    relationships: list[BoundRelationship] = Field(default_factory=list)
    placement_candidates: list[PlacementCandidate] = Field(default_factory=list)


Stage = Literal["review_capture", "measure", "check_accuracy", "update_reconstruction"]
ArtifactKind = Literal["measurement_network", "measurement_plan", "placement_review", "context_review", "scan_correction"]


class ChecklistBatch(Model):
    id: str
    kind: Literal["initial", "additional", "recheck"]
    ordered_pairs: list[Pair]
    current_pair: Pair | None = None
    producing_artifact_id: str


class Workflow(Model):
    id: str
    source_run_id: str
    layout_id: str
    group_id: str | None = None
    profile_ref: ProfileRef | None = None
    source_binding: SourceBinding | None = None
    stage: Stage = "review_capture"
    target_mm: float = Field(default=5, gt=0)
    improvement_mm: float = Field(default=5, gt=0)
    candidate_sigmas: dict[str, float] = Field(default_factory=dict)
    checklist_batches: list[ChecklistBatch] = Field(default_factory=list)
    artifact_refs: dict[ArtifactKind, str] = Field(default_factory=dict)
    corrected_run_id: str | None = None
    review_decisions: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_workflow(self):
        for key, sigma in self.candidate_sigmas.items():
            try:
                a, b = key.split(":")
                pair = Pair(tag_a=int(a), tag_b=int(b))
                if key != f"{pair.tag_a}:{pair.tag_b}" or sigma <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValueError("Candidate precision keys must be canonical pairs with positive sigma.") from None
        if self.source_binding and (self.source_binding.source_run_id != self.source_run_id or
                                    self.source_binding.profile_ref != self.profile_ref):
            raise ValueError("Source binding must belong to this source and profile revision.")
        return self


class ArtifactEnvelope(Model):
    version: Literal[1] = 1
    id: str
    kind: ArtifactKind
    algorithm_version: str
    workflow_id: str
    source_run_id: str
    layout_id: str
    measurement_revision: int = Field(ge=0, strict=True)
    profile_ref: ProfileRef | None = None
    fingerprints: dict[str, str]
    assumptions: dict[str, Any]
    job_id: str
    payload: dict[str, Any]


class ArtifactStatus(Model):
    status: Literal["current", "stale", "unavailable"]
    reasons: list[str] = Field(default_factory=list)
    available_actions: list[str] = Field(default_factory=list)


class WorkflowDocument(Model):
    version: Literal[1] = 1
    revision: int = Field(default=0, ge=0, strict=True)
    profiles: dict[str, list[ProfileRevision]] = Field(default_factory=dict)
    workflows: dict[str, Workflow] = Field(default_factory=dict)

    @model_validator(mode="after")
    def references(self):
        for key, versions in self.profiles.items():
            if any(p.profile_id != key or p.revision != i for i, p in enumerate(versions, 1)):
                raise ValueError("Profile revisions must be consecutive and match their key.")
        sources = [(w.source_run_id, w.layout_id) for w in self.workflows.values()]
        if len(sources) != len(set(sources)):
            raise ValueError("A source and layout may have only one workflow.")
        for key, workflow in self.workflows.items():
            if key != workflow.id:
                raise ValueError("Workflow identity differs from its key.")
            if workflow.profile_ref:
                versions = self.profiles.get(workflow.profile_ref.profile_id, [])
                if workflow.profile_ref.revision > len(versions) or versions[workflow.profile_ref.revision - 1].layout_id != workflow.layout_id:
                    raise ValueError("Unknown profile revision for workflow layout.")
        return self
