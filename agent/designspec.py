"""The small current DesignSpec used by the structured-spec Demo."""
from __future__ import annotations

import json
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DESIGN_SPEC_FILENAME = "designspec.json"


class DesignSpecError(ValueError):
    """Raised when a DesignSpec cannot be generated or stored."""


DESIGN_SPEC_TOOL = {
    "type": "function",
    "function": {
        "name": "design_spec_generate",
        "description": "Return one complete Ready DesignSpec for one Part as JSON.",
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "status",
                "request_summary",
                "part",
                "design_parameters",
            ],
            "properties": {
                "schema_version": {"type": "integer", "const": SCHEMA_VERSION},
                "status": {"type": "string", "enum": ["ready"]},
                "request_summary": {"type": "string"},
                "part": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "name",
                        "body",
                        "design_features",
                        "geometric_relations",
                        "design_requirements",
                        "assumptions",
                    ],
                    "properties": {
                        "name": {"type": "string"},
                        "body": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["type", "description"],
                            "properties": {
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                            },
                        },
                        "design_features": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["type", "description"],
                                "properties": {
                                    "type": {"type": "string"},
                                    "description": {"type": "string"},
                                },
                            },
                        },
                        "geometric_relations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["type", "description"],
                                "properties": {
                                    "type": {"type": "string"},
                                    "description": {"type": "string"},
                                },
                            },
                        },
                        "design_requirements": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "assumptions": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
                "design_parameters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "name",
                            "quantity_type",
                            "original",
                            "source",
                        ],
                        "properties": {
                            "name": {"type": "string"},
                            "quantity_type": {"type": "string"},
                            "original": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["value", "unit"],
                                "properties": {
                                    "value": {},
                                    "unit": {"type": "string"},
                                },
                            },
                            "source": {
                                "type": "string",
                                "enum": ["user_statement", "assumption"],
                            },
                        },
                    },
                },
            },
        },
    },
}

_QUANTITY_RE = re.compile(
    r"^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*([A-Za-z]+)?\s*$"
)
_LENGTH_FACTORS = {
    "mm": 1.0,
    "millimeter": 1.0,
    "millimeters": 1.0,
    "millimetre": 1.0,
    "millimetres": 1.0,
    "cm": 10.0,
    "centimeter": 10.0,
    "centimeters": 10.0,
    "centimetre": 10.0,
    "centimetres": 10.0,
    "m": 1000.0,
    "meter": 1000.0,
    "meters": 1000.0,
    "metre": 1000.0,
    "metres": 1000.0,
    "in": 25.4,
    "inch": 25.4,
    "inches": 25.4,
    "ft": 304.8,
    "foot": 304.8,
    "feet": 304.8,
    "um": 0.001,
    "micrometer": 0.001,
    "micrometers": 0.001,
    "micrometre": 0.001,
    "micrometres": 0.001,
}
_ANGLE_FACTORS = {
    "deg": 1.0,
    "degree": 1.0,
    "degrees": 1.0,
    "rad": 180.0 / math.pi,
    "radian": 180.0 / math.pi,
    "radians": 180.0 / math.pi,
    "grad": 0.9,
    "grads": 0.9,
}


class DesignSpecStore:
    """Persist exactly one current Ready DesignSpec for a project."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.path = project_dir / DESIGN_SPEC_FILENAME

    def read(self) -> dict[str, Any] | None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError) as error:
            raise DesignSpecError("The current DesignSpec is unreadable.") from error
        _validate_ready_spec(data)
        return data

    def save(self, spec: dict[str, Any]) -> dict[str, Any]:
        _validate_ready_spec(spec)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.", suffix=".tmp", dir=self.project_dir
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as temporary:
                json.dump(spec, temporary, ensure_ascii=False, indent=2)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_name, self.path)
        except BaseException:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass
            raise
        return spec


class DesignSpecStage:
    """Generate and normalize one Ready DesignSpec before CAD tools exist."""

    def __init__(self, client: Any, stop_event: Any = None) -> None:
        self.client = client
        self.stop_event = stop_event

    def generate(
        self, request_message: str, current: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if self.stop_event is not None and self.stop_event.is_set():
            raise DesignSpecError("DesignSpec generation was stopped.")
        user_content = request_message
        if current is not None:
            user_content = (
                "Current DesignSpec context:\n"
                + json.dumps(current, ensure_ascii=False, sort_keys=True)
                + "\n\nDesign Change:\n"
                + request_message
            )
        response = self.client.chat(
            [
                {"role": "system", "content": _DESIGN_SPEC_PROMPT},
                {"role": "user", "content": user_content},
            ],
            [DESIGN_SPEC_TOOL],
        )
        if self.stop_event is not None and self.stop_event.is_set():
            raise DesignSpecError("DesignSpec generation was stopped.")
        raw = _response_object(response)
        return normalize_design_spec(raw, request_message)


_DESIGN_SPEC_PROMPT = """You are the lightweight structured DesignSpec stage for a local CAD agent.
The user message is a text-only Design Change for one Part. Return exactly one
complete JSON object through the design_spec_generate function. Set status to
ready. Include schema_version 1, request_summary, one part with name, body,
design_features, geometric_relations, design_requirements, and assumptions,
plus design_parameters. Keep explicit user statements distinct from
assumptions. For every design parameter retain the original numeric value and
unit, quantity_type, and source (user_statement or assumption). A length must
have a normalized value in millimetres (mm); an angle must have a normalized
value in degrees (deg). Use assumptions for non-critical omitted details.
Do not return Markdown, explanations, a clarification, an assembly, or CAD
source code. The specification is ready for the CAD Agent to use immediately."""


def normalize_design_spec(raw: Any, request_message: str = "") -> dict[str, Any]:
    """Convert a model response into the small canonical Ready DesignSpec."""
    if not isinstance(raw, dict):
        raise DesignSpecError("DesignSpec generation did not return a JSON object.")
    status = str(raw.get("status", raw.get("readiness", "ready"))).strip().lower()
    if status not in {"ready", "complete", "completed"}:
        raise DesignSpecError("DesignSpec generation returned a specification that is not ready.")

    part_raw = raw.get("part")
    part = part_raw if isinstance(part_raw, dict) else {}
    summary = _text(
        raw.get("request_summary", raw.get("summary", request_message)),
        request_message,
    )
    body = _normalize_geometry_item(
        part.get("body", raw.get("body")), "part", summary
    )
    features = _normalize_geometry_items(
        part.get("design_features", raw.get("design_features", raw.get("features")))
    )
    relations = _normalize_geometry_items(
        part.get(
            "geometric_relations",
            raw.get("geometric_relations", raw.get("relations")),
        )
    )
    requirements = _normalize_text_list(
        part.get(
            "design_requirements",
            raw.get("design_requirements", raw.get("requirements")),
        )
    )
    assumptions = _normalize_text_list(
        part.get("assumptions", raw.get("assumptions"))
    )
    parameters_raw = raw.get("design_parameters")
    if parameters_raw is None:
        parameters_raw = part.get("design_parameters", raw.get("parameters"))
    parameters = _normalize_parameters(parameters_raw)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "request_summary": summary,
        "part": {
            "name": _text(part.get("name"), "Part"),
            "body": body,
            "design_parameters": parameters,
            "design_features": features,
            "geometric_relations": relations,
            "design_requirements": requirements,
            "assumptions": assumptions,
        },
        "design_parameters": parameters,
    }


def _response_object(response: Any) -> dict[str, Any]:
    try:
        message = response["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as error:
        raise DesignSpecError("DesignSpec generation returned an invalid model response.") from error
    if not isinstance(message, dict):
        raise DesignSpecError("DesignSpec generation returned an invalid model message.")
    calls = message.get("tool_calls")
    if isinstance(calls, list):
        for call in calls:
            function = call.get("function") if isinstance(call, dict) else None
            if not isinstance(function, dict):
                continue
            arguments = function.get("arguments")
            if isinstance(arguments, dict):
                return arguments
            if isinstance(arguments, str):
                return _parse_json(arguments)
    content = message.get("content")
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        return _parse_json(content)
    raise DesignSpecError("DesignSpec generation returned no JSON content.")


def _parse_json(content: str) -> dict[str, Any]:
    candidate = content.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.IGNORECASE)
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as error:
        raise DesignSpecError("DesignSpec generation returned malformed JSON.") from error
    if not isinstance(value, dict):
        raise DesignSpecError("DesignSpec generation did not return a JSON object.")
    return value


def _validate_ready_spec(spec: Any) -> None:
    if not isinstance(spec, dict):
        raise DesignSpecError("DesignSpec must be a JSON object.")
    if spec.get("schema_version") != SCHEMA_VERSION:
        raise DesignSpecError("DesignSpec has an unsupported schema version.")
    if spec.get("status") != "ready":
        raise DesignSpecError("Only a Ready DesignSpec can be stored.")
    if not isinstance(spec.get("request_summary"), str):
        raise DesignSpecError("Ready DesignSpec is missing its request summary.")
    part = spec.get("part")
    if not isinstance(part, dict):
        raise DesignSpecError("Ready DesignSpec is missing its Part.")
    for key in (
        "body",
        "design_parameters",
        "design_features",
        "geometric_relations",
        "design_requirements",
        "assumptions",
    ):
        if key not in part:
            raise DesignSpecError(f"Ready DesignSpec is missing Part field: {key}.")
    if spec.get("design_parameters") != part.get("design_parameters"):
        raise DesignSpecError("Ready DesignSpec has inconsistent Design Parameters.")


def _text(value: Any, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback.strip() or "Design Change"


def _normalize_geometry_item(value: Any, default_type: str, default_description: str) -> dict[str, str]:
    if isinstance(value, dict):
        return {
            "type": _text(value.get("type", value.get("kind")), default_type),
            "description": _text(value.get("description"), default_description),
        }
    if isinstance(value, str) and value.strip():
        return {"type": default_type, "description": value.strip()}
    return {"type": default_type, "description": default_description}


def _normalize_geometry_items(value: Any) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    return [_normalize_geometry_item(item, "feature", str(item)) for item in value]


def _normalize_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _normalize_parameters(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, dict):
        value = [dict(item, name=name) if isinstance(item, dict) else {"name": name, "value": item} for name, item in value.items()]
    if not isinstance(value, list):
        raise DesignSpecError("Design Parameters must be a JSON array.")
    return [_normalize_parameter(item, index) for index, item in enumerate(value)]


def _normalize_parameter(value: Any, index: int) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DesignSpecError(f"Design Parameter {index + 1} is not an object.")
    name = _text(value.get("name"), f"parameter_{index + 1}")
    quantity_type = _text(
        value.get("quantity_type", value.get("quantityType", value.get("type"))),
        "quantity",
    ).lower()
    original_value, original_unit = _quantity_parts(
        value.get("original", value.get("original_value", value.get("value"))),
        value.get("original_unit", value.get("unit")),
    )
    if original_value is None:
        raise DesignSpecError(f"Design Parameter {name} is missing its original value.")
    normalized_value, normalized_unit = _normalized_quantity(
        quantity_type,
        original_value,
        original_unit,
        value.get("normalized"),
        value.get("normalized_value"),
        value.get("normalized_unit"),
    )
    source = str(value.get("source", value.get("origin", "user_statement"))).strip().lower()
    source = "assumption" if source in {"assumption", "assumed", "inferred"} else "user_statement"
    return {
        "name": name,
        "quantity_type": quantity_type,
        "original": {"value": original_value, "unit": original_unit},
        "normalized": {"value": normalized_value, "unit": normalized_unit},
        "source": source,
    }


def _quantity_parts(value: Any, unit: Any) -> tuple[Any, str]:
    unit_text = str(unit).strip() if unit is not None else ""
    if isinstance(value, dict):
        unit_text = str(value.get("unit", unit_text)).strip()
        value = value.get("value")
    if isinstance(value, str):
        match = _QUANTITY_RE.match(value)
        if match:
            value = float(match.group(1))
            unit_text = unit_text or (match.group(2) or "")
    if isinstance(value, bool):
        return None, unit_text
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            return None, unit_text
        return value, unit_text
    return value, unit_text


def _normalized_quantity(
    quantity_type: str,
    original_value: Any,
    original_unit: str,
    normalized: Any,
    normalized_value: Any,
    normalized_unit: Any,
) -> tuple[Any, str]:
    dimension = "angle" if quantity_type in {"angle", "angular"} else "length" if quantity_type in {"length", "distance"} else ""
    if dimension:
        factors = _ANGLE_FACTORS if dimension == "angle" else _LENGTH_FACTORS
        source_unit = original_unit.lower()
        factor = factors.get(source_unit)
        if factor is None or not isinstance(original_value, (int, float)):
            raise DesignSpecError(
                f"{quantity_type.title()} Design Parameter requires a numeric value and supported unit."
            )
        result = round(float(original_value) * factor, 10)
        return result, "deg" if dimension == "angle" else "mm"
    if isinstance(normalized, dict):
        value = normalized.get("value")
        unit = normalized.get("unit", "")
    else:
        value = normalized_value if normalized_value is not None else original_value
        unit = normalized_unit if normalized_unit is not None else original_unit
    return value, str(unit).strip()
