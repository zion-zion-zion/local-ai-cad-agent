"""The small current DesignSpec used by the structured-spec Demo."""
from __future__ import annotations

import json
import math
import os
import re
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent.tools.question_tool import QuestionTool, normalize_questions

SCHEMA_VERSION = 1
DESIGN_SPEC_FILENAME = "designspec.json"


class DesignSpecError(ValueError):
    """Raised when a DesignSpec cannot be generated or stored."""


CONVERSATION_ROUTE = "conversation"
DESIGN_CHANGE_ROUTE = "design_change"


MESSAGE_ROUTE_TOOL = {
    "type": "function",
    "function": {
        "name": "conversation_route",
        "description": "Classify the user's text as an informational Conversation or a Design Change.",
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "required": ["route"],
            "properties": {
                "route": {
                    "type": "string",
                    "enum": [CONVERSATION_ROUTE, DESIGN_CHANGE_ROUTE],
                },
            },
        },
    },
}


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

# The DesignSpec stage uses the same typed question contract as the CAD loop.
# Keeping the function name and payload shape identical lets the existing UI
# render a blocking omission without a second clarification protocol.
DESIGN_SPEC_CLARIFICATION_TOOL = deepcopy(QuestionTool.__tool_schema__)

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


@dataclass(frozen=True)
class MessageClassification:
    """The structured route selected for one user text message."""

    route: str


@dataclass(frozen=True)
class ClarificationRequest:
    """Typed user input required before a Design Change can become ready."""

    title: str
    questions: list[dict[str, Any]]


class DesignSpecStage:
    """Prepare one Ready DesignSpec or a typed Clarification before CAD tools."""

    def __init__(self, client: Any, stop_event: Any = None) -> None:
        self.client = client
        self.stop_event = stop_event

    def classify(
        self,
        request_message: str,
        current: dict[str, Any] | None = None,
        project_state: dict[str, Any] | None = None,
    ) -> MessageClassification:
        """Classify a text request before exposing any CAD capability."""
        if self.stop_event is not None and self.stop_event.is_set():
            raise DesignSpecError("Message routing was stopped.")
        response = self.client.chat(
            [
                {"role": "system", "content": _ROUTING_PROMPT},
                {
                    "role": "user",
                    "content": _stage_context(
                        request_message, current=current, project_state=project_state
                    ),
                },
            ],
            [MESSAGE_ROUTE_TOOL],
        )
        if self.stop_event is not None and self.stop_event.is_set():
            raise DesignSpecError("Message routing was stopped.")
        raw = _response_object(response)
        return MessageClassification(route=_normalize_route(raw))

    def generate(
        self, request_message: str, current: dict[str, Any] | None = None
    ) -> dict[str, Any] | ClarificationRequest:
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
            [DESIGN_SPEC_TOOL, DESIGN_SPEC_CLARIFICATION_TOOL],
        )
        if self.stop_event is not None and self.stop_event.is_set():
            raise DesignSpecError("DesignSpec generation was stopped.")
        clarification = _clarification_from_response(response)
        if clarification is not None:
            return clarification
        raw = _response_object(response)
        if current is not None:
            raw = merge_design_specs(current, raw)
        return normalize_design_spec(raw, request_message)


_ROUTING_PROMPT = """You are the lightweight message-routing stage for a local CAD agent.
Classify the user's supported text message as exactly one route using the
conversation_route function. Use conversation when the user asks for
information, an explanation, a status update, or a discussion that does not
change the intended Part. Use design_change when the user asks to create,
modify, resize, remove, or otherwise change the Part. A question about the
current DesignSpec is a conversation. Return no explanation and do not write
CAD code."""


_DESIGN_SPEC_PROMPT = """You are the lightweight structured DesignSpec stage for a local CAD agent.
The user message is a text-only Design Change for one Part. Normally return
exactly one complete JSON object through the design_spec_generate function and
set status to ready. Include schema_version 1, request_summary, one part with
name, body, design_features, geometric_relations, design_requirements, and
assumptions, plus design_parameters. Keep explicit user statements distinct
from assumptions. For every design parameter retain the original numeric value
and unit, quantity_type, and source (user_statement or assumption). A length
must have a normalized value in millimetres (mm); an angle must have a
normalized value in degrees (deg).

Use assumptions for non-critical omitted details. If a missing dimension or
other fact genuinely blocks modeling, call the question function with a typed
Clarification instead of returning an incomplete specification. Ask only for
the blocking fact; do not ask the user to approve the DesignSpec. A valid
answer will be supplied to this same Design Change later. Do not call question
for a non-critical detail that can be recorded as an assumption.

When a current DesignSpec is provided, return a complete replacement: carry
forward design details omitted by the new request, and replace values or
requirements explicitly changed by the user. Do not return an independent
fragment. A new explicit Design Requirement supersedes an Assumption about the
same design detail. Do not return Markdown, an assembly, or CAD source code.
Once no blocking omission remains, the specification is ready for the CAD
Agent to use immediately."""


def _stage_context(
    request_message: str,
    *,
    current: dict[str, Any] | None,
    project_state: dict[str, Any] | None,
) -> str:
    current_content = (
        json.dumps(current, ensure_ascii=False, sort_keys=True)
        if current is not None
        else "No current Ready DesignSpec is available."
    )
    state_content = json.dumps(
        project_state or {}, ensure_ascii=False, sort_keys=True
    )
    return (
        "<current_design_spec>\n"
        + current_content
        + "\n</current_design_spec>\n"
        "<project_state>\n"
        + state_content
        + "\n</project_state>\n"
        "<user_message>\n"
        + request_message
        + "\n</user_message>"
    )


def _normalize_route(raw: dict[str, Any]) -> str:
    value = raw.get(
        "route",
        raw.get("classification", raw.get("message_type", raw.get("intent"))),
    )
    if isinstance(value, bool):
        return DESIGN_CHANGE_ROUTE if value else CONVERSATION_ROUTE
    if not isinstance(value, str):
        raise DesignSpecError("Message routing did not return a Conversation or Design Change.")
    route = value.strip().lower().replace("-", "_").replace(" ", "_")
    if route in {CONVERSATION_ROUTE, "chat", "question", "informational"}:
        return CONVERSATION_ROUTE
    if route in {DESIGN_CHANGE_ROUTE, "design", "model_change", "modeling"}:
        return DESIGN_CHANGE_ROUTE
    raise DesignSpecError("Message routing did not return a Conversation or Design Change.")


def merge_design_specs(
    current: dict[str, Any], incoming: dict[str, Any]
) -> dict[str, Any]:
    """Merge a later partial model response over the current complete intent.

    The stage prompt asks the model for a complete replacement, but retaining
    omitted fields here makes that contract observable even when a compatible
    model returns only the details it changed.
    """
    if not isinstance(current, dict) or not isinstance(incoming, dict):
        raise DesignSpecError("DesignSpec replacement must be a JSON object.")
    merged = deepcopy(current)
    incoming_part = incoming.get("part")
    incoming_part = incoming_part if isinstance(incoming_part, dict) else {}
    current_part = merged.get("part")
    current_part = current_part if isinstance(current_part, dict) else {}
    merged["part"] = current_part

    for key in ("schema_version", "status", "request_summary"):
        if key in incoming and incoming[key] not in (None, ""):
            merged[key] = deepcopy(incoming[key])
    if "name" in incoming_part and incoming_part["name"] not in (None, ""):
        current_part["name"] = deepcopy(incoming_part["name"])

    if "body" in incoming_part:
        current_part["body"] = _merge_object(
            current_part.get("body"), incoming_part["body"]
        )
    for key in ("design_features", "geometric_relations"):
        if key in incoming_part:
            # The model is asked for a complete replacement. A present list
            # is therefore authoritative; an omitted field is retained above.
            current_part[key] = deepcopy(incoming_part[key])

    for key in ("design_requirements", "assumptions"):
        if key in incoming_part:
            current_part[key] = _merge_statements(
                current_part.get(key), incoming_part[key]
            )

    incoming_parameters = None
    if "design_parameters" in incoming:
        incoming_parameters = incoming["design_parameters"]
    elif "design_parameters" in incoming_part:
        incoming_parameters = incoming_part["design_parameters"]
    elif "parameters" in incoming:
        incoming_parameters = incoming["parameters"]
    if incoming_parameters is not None:
        parameters = _merge_parameters(
            current_part.get("design_parameters", merged.get("design_parameters")),
            incoming_parameters,
        )
        current_part["design_parameters"] = parameters
        merged["design_parameters"] = parameters
    elif "design_parameters" in current_part:
        merged["design_parameters"] = deepcopy(current_part["design_parameters"])

    requirements = _statement_values(current_part.get("design_requirements"))
    assumptions = _statement_values(current_part.get("assumptions"))
    current_part["design_requirements"] = requirements
    current_part["assumptions"] = [
        assumption
        for assumption in assumptions
        if not any(
            _statements_overlap(assumption, requirement)
            for requirement in requirements
        )
    ]
    return merged


def _merge_object(current: Any, incoming: Any) -> Any:
    if isinstance(current, dict) and isinstance(incoming, dict):
        merged = deepcopy(current)
        merged.update(deepcopy(incoming))
        return merged
    return deepcopy(incoming)


def _merge_parameters(current: Any, incoming: Any) -> list[Any]:
    current_items = (
        current
        if isinstance(current, list)
        else ([] if current is None else [current])
    )
    incoming_items = incoming if isinstance(incoming, list) else [incoming]
    if not incoming_items:
        return deepcopy(current_items)
    merged = deepcopy(current_items)
    for item in incoming_items:
        if not isinstance(item, dict):
            merged.append(deepcopy(item))
            continue
        name = str(item.get("name", "")).strip().casefold()
        match_index = next(
            (
                index
                for index, existing in enumerate(merged)
                if isinstance(existing, dict)
                and name
                and str(existing.get("name", "")).strip().casefold() == name
            ),
            None,
        )
        if match_index is None:
            merged.append(deepcopy(item))
        else:
            merged[match_index] = _merge_parameter(merged[match_index], item)
    return merged


def _merge_parameter(current: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(current)
    for key, value in incoming.items():
        if key in {"original", "normalized"} and isinstance(value, dict):
            merged[key] = _merge_object(merged.get(key), value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _merge_statements(current: Any, incoming: Any) -> list[str]:
    current_items = _statement_values(current)
    incoming_items = _statement_values(incoming)
    if not incoming_items:
        return []
    merged = current_items
    for statement in incoming_items:
        match_index = next(
            (
                index
                for index, existing in enumerate(merged)
                if _statements_overlap(existing, statement)
            ),
            None,
        )
        if match_index is None:
            merged.append(statement)
        else:
            merged[match_index] = statement
    return list(dict.fromkeys(merged))


def _statement_values(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return [item.strip() for item in values if isinstance(item, str) and item.strip()]


_STATEMENT_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "be",
        "by",
        "for",
        "in",
        "is",
        "it",
        "must",
        "of",
        "on",
        "or",
        "part",
        "remain",
        "should",
        "the",
        "to",
        "use",
        "with",
    }
)


def _statement_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.casefold())
        if token not in _STATEMENT_STOPWORDS
    }


_DESIGN_DETAIL_TOKENS = frozenset(
    {
        "angle",
        "angles",
        "aperture",
        "bevel",
        "chamfer",
        "chamfers",
        "coaxial",
        "diameter",
        "depth",
        "fillet",
        "fillets",
        "height",
        "heights",
        "hole",
        "holes",
        "mounting",
        "parallel",
        "radius",
        "radii",
        "rectangular",
        "single",
        "slot",
        "slots",
        "solid",
        "spacing",
        "spaced",
        "symmetry",
        "thickness",
        "tilt",
        "width",
    }
)


def _statements_overlap(left: str, right: str) -> bool:
    if left.casefold().strip() == right.casefold().strip():
        return True
    overlap = _statement_tokens(left) & _statement_tokens(right)
    if len(overlap) >= 2:
        return True
    return any(token in _DESIGN_DETAIL_TOKENS for token in overlap)


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


def _clarification_from_response(response: Any) -> ClarificationRequest | None:
    message = _response_message(response)
    calls = message.get("tool_calls")
    if isinstance(calls, list):
        for call in calls:
            function = call.get("function") if isinstance(call, dict) else None
            if not isinstance(function, dict):
                continue
            name = function.get("name")
            if name not in {
                "question",
                "ask_question",
                "clarification",
                "design_spec_clarification",
            }:
                continue
            return _clarification_from_arguments(_tool_arguments(function))

    raw = _response_object(response)
    status = (
        str(raw.get("status", raw.get("readiness", "")))
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )
    is_question_payload = any(
        key in raw
        for key in ("questions", "question", "clarification", "pending_clarification")
    )
    if status not in {
        "clarification",
        "needs_clarification",
        "clarification_required",
        "pending_clarification",
        "blocked",
    } and not (is_question_payload and status not in {"ready", "complete", "completed"}):
        return None
    clarification = raw.get(
        "clarification", raw.get("pending_clarification", raw)
    )
    return _clarification_from_arguments(clarification)


def _clarification_from_arguments(arguments: Any) -> ClarificationRequest:
    if not isinstance(arguments, dict):
        raise DesignSpecError("DesignSpec clarification did not return an object.")
    try:
        questions = normalize_questions(arguments)
        QuestionTool.validate_questions(questions)
    except (KeyError, TypeError, ValueError) as error:
        raise DesignSpecError("DesignSpec clarification returned invalid questions.") from error
    title = arguments.get("title", "")
    return ClarificationRequest(
        title=title.strip() if isinstance(title, str) else "",
        questions=deepcopy(questions),
    )


def _response_message(response: Any) -> dict[str, Any]:
    try:
        message = response["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as error:
        raise DesignSpecError("DesignSpec generation returned an invalid model response.") from error
    if not isinstance(message, dict):
        raise DesignSpecError("DesignSpec generation returned an invalid model message.")
    return message


def _tool_arguments(function: dict[str, Any]) -> dict[str, Any]:
    arguments = function.get("arguments")
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        return _parse_json(arguments)
    raise DesignSpecError("DesignSpec clarification returned no question content.")


def _response_object(response: Any) -> dict[str, Any]:
    message = _response_message(response)
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
