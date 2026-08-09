from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks.cadprompt import adapt_prompt, load_cadprompt_samples
from benchmarks.metrics import evaluate_stl_pair
from benchmarks.run import _tool_stats, _valid_solid


def test_cadquery_prompt_adapter_keeps_geometry_and_forces_noninteractive() -> None:
    adapted = adapt_prompt(
        "Write Python code using CADQuery to create a cylinder with a radius of 2 units."
    )
    assert "CADQuery" not in adapted
    assert "radius of 2 units" in adapted
    assert "build123d" in adapted
    assert "Do not ask a clarifying question" in adapted


def test_cadprompt_slice_is_grouped_when_data_is_available() -> None:
    root = Path(__file__).parents[1] / "benchmarks/.data/CADPrompt"
    if not (root / "Data_Stratification.xlsx").is_file():
        pytest.skip("CADPrompt is an optional benchmark download.")
    samples = load_cadprompt_samples(root)
    assert len(samples) == 20
    assert [sample.semantic_complexity for sample in samples[:10]] == ["Simple"] * 10
    assert [sample.semantic_complexity for sample in samples[10:]] == ["Complex"] * 10
    assert all("CADQuery" in sample.prompt for sample in samples)


def test_stl_metrics_are_zero_for_identical_mesh(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    mesh = trimesh.creation.box(extents=[1.0, 2.0, 3.0])
    source = tmp_path / "source.stl"
    prediction = tmp_path / "prediction.stl"
    mesh.export(source)
    mesh.export(prediction)
    metrics = evaluate_stl_pair(source, prediction, sample_count=256, seed=4)
    assert metrics["normalized_chamfer_distance"] == 0.0
    assert metrics["bbox_relative_error"] == 0.0
    assert metrics["volume_relative_error"] == 0.0
    assert metrics["prediction_mesh_valid"] is True


def test_runner_metric_helpers_classify_tool_failures() -> None:
    events = [
        {"kind": "tool_status", "data": {"tool": "file_read", "status": "completed"}},
        {
            "kind": "tool_status",
            "data": {
                "tool": "cad_build_and_verify",
                "arguments": {},
                "status": "error",
                "result": json.dumps({"error": {"code": "CAD_BUILD_FAILED"}}),
            },
        },
    ]
    assert _tool_stats(events) == {
        "tool_calls": 2,
        "cad_build_calls": 1,
        "cad_repair_count": 1,
    }
    assert _valid_solid({"is_valid": True, "solid_count": 1, "volume_mm3": 1})
    assert not _valid_solid({"is_valid": False, "solid_count": 1, "volume_mm3": 1})
