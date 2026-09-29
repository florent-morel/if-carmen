"""Shared helpers for daemon E2E tests."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from backend.src.schemas.resource import ResourceType

common_fields_str = [
    "ResourceType",
    "Provider",
    "Region",
]

common_fields_float = [
    "EnergyKWH",
    "OperationalCarbonGramsCO2eq",
    "EmbodiedCarbonGramsCO2eq",
    "TotalCarbonGramsCO2eq",
    "CarbonIntensity",
]

VM_fields = [
    "VMSize",
]

storage_fields = [
    "StorageType",
    "ReplicationType",
    "SizeGB",
]


@dataclass(frozen=True)
class DaemonRun:
    rows: list[dict[str, str]]
    artifact_dir: Path

    def validate_if_inputs(
        self,
        stage: str,
        expected_inputs_by_id: dict[str, dict[str, float]],
        expected_common_inputs: dict[str, float] | None = None,
    ) -> None:
        validate_if_inputs(self.artifact_dir, stage, expected_inputs_by_id, expected_common_inputs)


def validate_if_inputs(
    artifact_dir: Path,
    stage: str,
    expected_inputs_by_id: dict[str, dict[str, float]],
    expected_common_inputs: dict[str, float] | None = None,
) -> None:
    output_paths = sorted((artifact_dir / stage).glob("if_output*.yaml"))
    assert output_paths, f"Missing IF output for {stage} in {artifact_dir}"

    actual_by_id = {}
    for if_output_path in output_paths:
        with if_output_path.open(encoding="utf-8") as if_output_file:
            children = yaml.safe_load(if_output_file)["tree"]["children"]
        for resource_id, resource in children.items():
            assert resource_id not in actual_by_id, f"Duplicate IF result for {resource_id}"
            actual_by_id[resource_id] = resource

    assert expected_inputs_by_id, "Provide at least one expected IF resource"
    first_resource_id = next(iter(expected_inputs_by_id))
    first_resource = actual_by_id.get(first_resource_id)
    assert first_resource is not None, f"Missing IF result for {first_resource_id}"
    assert first_resource["inputs"], f"Missing IF inputs for {first_resource_id}"

    for field, expected_value in (expected_common_inputs or {}).items():
        assert first_resource["inputs"][0][field] == pytest.approx(
            expected_value, abs=0.0001, rel=0
        ), (
            f"{first_resource_id}: IF common input {field} "
            f"actual={first_resource['inputs'][0][field]} expected={expected_value}"
        )

    for resource_id, expected_inputs in expected_inputs_by_id.items():
        actual = actual_by_id.get(resource_id)
        assert actual is not None, f"Missing IF result for {resource_id}"
        assert actual["inputs"], f"Missing IF inputs for {resource_id}"
        for field, expected_value in expected_inputs.items():
            assert actual["inputs"][0][field] == pytest.approx(
                expected_value, abs=0.0001, rel=0
            ), (
                f"{resource_id}: IF input {field} "
                f"actual={actual['inputs'][0][field]} expected={expected_value}"
            )


def validate_output(row_by_id, expected_result_by_id):
    for resource_id, expected_result in expected_result_by_id.items():
        actual_result = row_by_id.get(resource_id)
        assert actual_result is not None, f"Missing output row for resource {resource_id}"

        # Validate fields only if they are present in the expected result
        # This allows for partial validation of the output rows

        # Validate string fields
        for field in common_fields_str:
            if field in expected_result:
                assert actual_result[field] == expected_result[field], f"{resource_id}: {field} actual_result={actual_result[field]} expected_result={expected_result[field]}"

        # Validate float fields
        for field in common_fields_float:
            if field in expected_result:
                assert float(actual_result[field]) == pytest.approx(expected_result[field], rel=1e-3), (
                    f"{resource_id}: {field} actual_result={actual_result[field]} expected_result={expected_result[field]}"
                )

        if expected_result["ResourceType"] == ResourceType.VIRTUAL_MACHINE.value:
            for field in VM_fields:
                # By default, VMSize is a string, so we can compare directly
                if field in expected_result:
                    assert actual_result[field] == expected_result[field], f"{resource_id}: {field} actual_result={actual_result[field]} expected_result={expected_result[field]}"

        if expected_result["ResourceType"] == ResourceType.STORAGE.value:
            for field in storage_fields:
                # Float comparison
                if field == "SizeGB":
                    assert float(actual_result[field]) == pytest.approx(expected_result[field], rel=1e-6), (
                        f"{resource_id}: {field} actual_result={actual_result[field]} expected_result={expected_result[field]}"
                    )
                # String comparison
                else:
                    assert actual_result[field] == expected_result[field], f"{resource_id}: {field} actual_result={actual_result[field]} expected_result={expected_result[field]}"


def run_daemon(test_path: Path, tmp_path: Path) -> DaemonRun:
    import csv
    import subprocess
    import sys
    if_artifact_dir = tmp_path / "if-artifacts"
    test_data_folder = test_path.parent / "test_data"
    output_dir = test_path.parent / "test_data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure deterministic assertion by removing previous report artifacts.
    for old_report in output_dir.glob("CO2_*.csv"):
        old_report.unlink()

    main_config_path = test_data_folder / "config" / "config.yaml"

    project_root = next(
        parent
        for parent in test_path.resolve().parents
        if (parent / "pyproject.toml").is_file()
    )
    command = [
        sys.executable,
        "-m",
        "backend.src.daemon.carbon_daemon_orchestrator",
        "--carmen-config-filepath",
        str(main_config_path),
        "--carmen-provider-config-filepath",
        str(test_data_folder / "config" / "modelling_constants" / "cloud_providers"),
        "--carmen-carbon-values-filepath",
        str(test_data_folder / "config" / "modelling_constants" / "carbon_values.yaml"),
    ]
    daemon = subprocess.run(
        command,
        cwd=project_root,
        env={**os.environ, "CARMEN_IF_ARTIFACT_DIR": str(if_artifact_dir.resolve())},
        capture_output=True,
        text=True,
        check=False,
    )
    assert daemon.returncode == 0, (
        f"Daemon main failed with exit code {daemon.returncode}\n"
        f"STDOUT:\n{daemon.stdout}\nSTDERR:\n{daemon.stderr}"
    )

    reports = sorted(output_dir.glob("CO2_*.csv"))
    assert reports, "No output CSV report generated by daemon main"

    with open(reports[-1], "r", encoding="utf-8") as report_f:
        return DaemonRun(list(csv.DictReader(report_f)), if_artifact_dir)
