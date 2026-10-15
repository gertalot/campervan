import math

import pytest
from pydantic import ValidationError

from campervan.parameters import DEFAULT_SIZE_MM, Parameters, default_parameters, parameter_schema


@pytest.mark.parametrize("size", [1, 100, 150.5, 1000])
def test_accepts_finite_json_numbers(size: float) -> None:
    assert Parameters.model_validate({"size_mm": size}).size_mm == size


@pytest.mark.parametrize("size", [0, -1, 1001, math.inf, -math.inf, math.nan, True, "150"])
def test_rejects_invalid_sizes(size: object) -> None:
    with pytest.raises(ValidationError):
        Parameters.model_validate({"size_mm": size})


@pytest.mark.parametrize("data", [{}, {"size_mm": 100, "unknown": 1}])
def test_requires_exact_parameter_fields(data: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Parameters.model_validate(data)


def test_parameter_snapshot_is_immutable() -> None:
    parameters = default_parameters()
    with pytest.raises(ValidationError, match="frozen"):
        parameters.size_mm = 150


def test_default_and_schema_describe_the_same_contract() -> None:
    assert DEFAULT_SIZE_MM == 100.0
    assert default_parameters().size_mm == DEFAULT_SIZE_MM
    schema = parameter_schema()
    assert schema["required"] == ["size_mm"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["size_mm"] == {
        "title": "Cube size",
        "type": "number",
        "default": 100.0,
        "unit": "mm",
        "exclusiveMinimum": 0,
        "maximum": 1000,
    }
