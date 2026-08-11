"""Trusted SimpleCADAPI model runner used inside the CAD sandbox."""

import hashlib
import json
import math
from pathlib import Path

from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepCheck import BRepCheck_Analyzer
from simplecadapi import ModelResult, Part, Solid, export_stl

namespace = {"__name__": "__main__", "__file__": "model.py"}
model_code = Path("model.py").read_text(encoding="utf-8")
exec(compile(model_code, "model.py", "exec"), namespace)  # noqa: S102

model_result = namespace.get("model_result")
if model_result is None:
    # Accept the short name during the bootstrap migration, while the
    # canonical issue-03 source validator will require ``model_result``.
    model_result = namespace.get("result")
if not isinstance(model_result, ModelResult):
    raise TypeError("model.py must expose a SimpleCADAPI ModelResult as `model_result`.")
if not model_result.session.has_explicit_results:
    raise ValueError("model.py must call capture_result() explicitly inside @model.")
if len(model_result.result_node_ids) != 1:
    raise ValueError("SimpleCADAPI model must expose exactly one captured Model Result.")

value = model_result.value
if not isinstance(value, Part):
    raise TypeError("SimpleCADAPI ModelResult must contain one semantic Part.")
shape = value.body
if not isinstance(shape, Solid):
    raise TypeError("SimpleCADAPI Part must contain exactly one Solid body.")
if not BRepCheck_Analyzer(shape.wrapped).IsValid():
    raise ValueError("The SimpleCADAPI Part body is invalid.")

volume = float(shape.get_volume())
if not math.isfinite(volume) or volume <= 0:
    raise ValueError("The SimpleCADAPI Part body has non-positive or non-finite volume.")

box = Bnd_Box()
BRepBndLib.AddOptimal_s(shape.wrapped, box, False, False)
x_min, y_min, z_min, x_max, y_max, z_max = box.Get()
dimensions = {
    "x": float(x_max - x_min),
    "y": float(y_max - y_min),
    "z": float(z_max - z_min),
}
if not all(math.isfinite(dimension) and dimension > 0 for dimension in dimensions.values()):
    raise ValueError("The SimpleCADAPI Part body has degenerate or non-finite bounds.")

metrics = {
    "solid_count": 1,
    "is_valid": True,
    "volume_mm3": round(volume, 3),
    "dimensions_mm": {key: round(value, 3) for key, value in dimensions.items()},
    "cad_backend": "SimpleCADAPI",
    "model_result_count": 1,
    "model_graph_id": model_result.session.graph.graph_id,
}
export_stl(shape, "preview.stl")
if not Path("preview.stl").is_file() or Path("preview.stl").stat().st_size == 0:
    raise RuntimeError("SimpleCADAPI execution did not save a usable preview.")
Path(".cad_metrics.json").write_text(
    json.dumps(
        {
            "model_sha256": hashlib.sha256(model_code.encode("utf-8")).hexdigest(),
            "metrics": metrics,
        },
        sort_keys=True,
    ),
    encoding="utf-8",
)
