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
    elif kind == "review-placement":
        from campervan.scan_placement import review_placement
        from campervan.scan_workflow_models import ArtifactEnvelope

        payload = review_placement(source, request["run"], MeasurementDocument.model_validate(request["measurements"]),
                                   request["planning"], request["context"], directory)
        artifact = ArtifactEnvelope.model_validate(request["artifact"] | {"payload": payload})
        write_json(directory / "artifact.json", artifact.model_dump())
    elif kind in ("plan-measurements", "suggest-more"):
        from campervan.scan_network import NETWORK_SETTINGS, analyse_network
        from campervan.scan_suggestions import plan_measurements, suggest_more
        from campervan.scan_workflow_models import ArtifactEnvelope

        measurements = MeasurementDocument.model_validate(request["measurements"])
        network = request["network"]
        if network is None:
            network = analyse_network(request["run"], measurements, NETWORK_SETTINGS, directory, certify=False)
        else:
            write_json(directory / "network.json", network)
        planner = suggest_more if kind == "suggest-more" else plan_measurements
        payload = planner(source, request["run"], measurements, network, request["planning"], directory)
        artifact = ArtifactEnvelope.model_validate(request["artifact"] | {"payload": payload})
        write_json(directory / "artifact.json", artifact.model_dump())
    elif kind == "preview-correction":
        from campervan.scan_analysis import preview_correction
        from campervan.scan_workflow_models import ArtifactEnvelope, SourceBinding

        binding_data = (request["context"] or {}).get("binding")
        payload = preview_correction(source, MeasurementDocument.model_validate(request["measurements"]), directory,
                                     network=request["network"],
                                     binding=SourceBinding.model_validate(binding_data) if binding_data else None)
        artifact = ArtifactEnvelope.model_validate(request["artifact"] | {"payload": payload})
        write_json(directory / "artifact.json", artifact.model_dump())
    elif kind == "update-mesh":
        from campervan.scan_analysis import CORRECTION_ALGORITHM_VERSION, CORRECTION_SETTINGS
        from campervan.scan_layouts import ScanLayouts
        from campervan.scan_rebuild import rebuild
        from campervan.scan_workflow_models import ArtifactEnvelope
        from campervan.scan_workflows import ScanWorkflowStore, capture_inputs

        # Reuse the same content policy immediately before original RGB-D ingestion. The worker never edits the store.
        store = ScanWorkflowStore(Path(request["workflow_store_path"]))
        document = store.read()
        item = document.workflows[request["workflow_id"]]
        artifact = ArtifactEnvelope.model_validate(read_json(Path(request["correction_directory"]) / "artifact.json"))
        if (item.artifact_refs.get("scan_correction") != artifact.id or artifact.workflow_id != item.id or
            item.source_run_id != request["run_id"]):
            raise ValueError("Correction selection changed before reconstruction started.")
        current = capture_inputs(item, document, ScanLayouts(Path(request["measurement_store_path"])),
                                 "scan_correction", CORRECTION_ALGORITHM_VERSION,
                                 settings=CORRECTION_SETTINGS, context_used=True)
        rebuild(source, Path(request["correction_directory"]), SCAN_RUNS / request["output_run_id"],
                fingerprints=current["fingerprints"])
    else:
        raise ValueError("Unknown scan analysis task.")


if __name__ == "__main__":
    main()
