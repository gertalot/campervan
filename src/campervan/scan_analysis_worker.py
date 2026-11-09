"""CLI subprocess entry for analysis, suggestions and corrected reconstruction."""

import sys
from pathlib import Path

from campervan.scan_measurements import MeasurementDocument
from campervan.scans import SCAN_RUNS, read_json


def main() -> None:
    kind, location = sys.argv[1:3]
    directory = Path(location).resolve()
    request = read_json(directory / "request.json")
    source = SCAN_RUNS / request["run_id"]
    if kind == "analyse":
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
