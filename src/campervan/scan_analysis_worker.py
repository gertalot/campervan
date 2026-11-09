"""CLI subprocess entry for analysis, suggestions and corrected reconstruction."""

import sys
from pathlib import Path

from campervan.scan_measurements import MeasurementDocument
from campervan.scans import SCAN_RUNS, read_json, write_json


def main() -> None:
    kind, location = sys.argv[1:3]
    directory = Path(location).resolve()
    request = read_json(directory / "request.json")
    source = SCAN_RUNS / request["run_id"]
    if kind == "check-measurements":
        from campervan.scan_network import analyse_network
        from campervan.scan_workflow_models import ArtifactEnvelope

        payload = analyse_network(request["run"], MeasurementDocument.model_validate(request["measurements"]),
                                  request["settings"], directory)
        artifact = ArtifactEnvelope.model_validate(request["artifact"] | {"payload": payload})
        write_json(directory / "artifact.json", artifact.model_dump())
    elif kind == "analyse":
        from campervan.scan_analysis import analyse

        analyse(source, MeasurementDocument.model_validate(request["measurements"]), directory)
    elif kind == "rebuild":
        from campervan.scan_rebuild import rebuild

        rebuild(source, directory, SCAN_RUNS / sys.argv[3])
    elif kind == "suggest":
        from campervan.scan_suggestions import suggest

        suggest(source, directory, float(sys.argv[3]))
    else:
        raise ValueError("Unknown scan analysis task.")


if __name__ == "__main__":
    main()
