"""Shared display data for the local API and exported project snapshots."""

from typing import Any, cast

from pydantic import BaseModel, Field

from campervan.cutting import effective_options, refresh_layout_source, source_key, stock_groups
from campervan.cutting_models import CuttingState
from campervan.materials import ROLES, CutPart, Selection, catalogue
from campervan.mannequins import MannequinSettings
from campervan.parameter_fit import parameter_constraints
from campervan.parameters import Parameters, parameter_schema


class ParameterResponse(BaseModel):
    session_id: str
    parameters: Parameters
    schema_: dict[str, object] = Field(serialization_alias="schema")
    viewer_url: str
    mannequins: MannequinSettings | None = None
    errors: dict[str, str] = Field(default_factory=dict)
    adjustments: dict[str, str] = Field(default_factory=dict)


def parameter_response(
    session_id: str, parameters: Parameters, viewer_url: str, mannequins: MannequinSettings | None = None,
) -> ParameterResponse:
    schema = cast(dict[str, Any], parameter_schema())
    for name, constraint in parameter_constraints(parameters).items():
        field = schema["properties"][name]
        field.update(constraint)
        field.pop("exclusiveMinimum", None)
        field.pop("exclusiveMaximum", None)
    for role in ROLES:
        for parameter in role.fields.values():
            schema["properties"][parameter]["material"] = role.id
    return ParameterResponse(
        session_id=session_id, parameters=parameters, schema_=schema, viewer_url=viewer_url, mannequins=mannequins,
    )


def material_data(
    parameters: Parameters, selections: dict[str, Selection], cuts: list[CutPart],
    cuts_revision: int | None, requested_revision: int,
) -> dict[str, Any]:
    return {
        "roles": [role.model_dump() for role in ROLES],
        "products": [product.model_dump() for product in catalogue()],
        "selections": {name: selection.model_dump() for name, selection in selections.items()},
        "parameters": parameters.model_dump(),
        "cuts": [cut.model_dump() for cut in cuts],
        "cuts_revision": cuts_revision,
        "requested_revision": requested_revision,
    }


def cutting_data(
    cuts: list[CutPart], materials: dict[str, Selection], cutting: CuttingState,
    jobs: dict[str, dict[str, Any]], current: bool,
) -> dict[str, Any]:
    groups = stock_groups(cuts, materials)
    sources = {}
    state = cutting.model_dump()
    for group in groups:
        options = effective_options(group, cutting.settings, cutting.options.get(group["key"]))
        sources[group["key"]] = source_key(group, options)
        for mode in ("straight", "nesting"):
            key = f"{group['key']}:{mode}"
            if key in state["results"]:
                state["results"][key] = refresh_layout_source(state["results"][key], group, options)
    return {"groups": groups, "sources": sources, "state": state, "jobs": jobs, "current": current}
