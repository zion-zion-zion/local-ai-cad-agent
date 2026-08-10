import json
import queue
import time
from pathlib import Path
from typing import ClassVar

from agent.designspec import DesignSpecStore, normalize_design_spec
from agent.settings import Settings, load_settings
from app import create_app

READY_RESPONSE = {
    "schema_version": 1,
    "status": "ready",
    "request_summary": "A mounting plate with a right-angle feature.",
    "part": {
        "name": "mounting_plate",
        "body": {"type": "plate", "description": "A rectangular mounting plate."},
        "design_features": [
            {"type": "hole", "description": "Four mounting holes."},
        ],
        "geometric_relations": [
            {"type": "symmetry", "description": "The holes are symmetric about the center."},
        ],
        "design_requirements": ["The plate must remain a single solid."],
        "assumptions": ["The mounting holes are evenly spaced."],
    },
    "design_parameters": [
        {
            "name": "width",
            "quantity_type": "length",
            "original": {"value": 2, "unit": "in"},
            "source": "user_statement",
        },
        {
            "name": "tilt",
            "quantity_type": "angle",
            "original": {"value": 1.5707963267948966, "unit": "rad"},
            "source": "user_statement",
        },
    ],
}


class OrderedFakeLLM:
    instances: ClassVar[list] = []
    api_visible: ClassVar[object] = None

    def __init__(self, settings):
        self.settings = settings
        self.calls = []
        self.stop_event = None
        self.stream_callback = None
        self.last_usage = None
        self.instances.append(self)

    def chat(self, messages, tools):
        project_dir = self.settings.workspace_root / "demo"
        self.calls.append(
            {
                "messages": list(messages),
                "tools": list(tools or []),
                "spec_exists": (project_dir / "designspec.json").is_file(),
            }
        )
        if len(self.calls) == 1:
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps({"route": "design_change"}),
                        }
                    }
                ]
            }
        if len(self.calls) == 2:
            assert self.calls[-1]["tools"][0]["function"]["name"] == "design_spec_generate"
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(READY_RESPONSE),
                        }
                    }
                ]
            }
        assert self.calls[-1]["spec_exists"]
        assert self.api_visible is not None
        assert self.api_visible()["available"] is True
        assert any(
            message.get("role") == "user"
            and "<ready_design_spec>" in str(message.get("content"))
            for message in messages
        )
        return {"choices": [{"message": {"role": "assistant", "content": "CAD loop entered."}}]}


class DirectFlowFakeLLM:
    instances: ClassVar[list] = []

    def __init__(self, settings):
        self.settings = settings
        self.calls = []
        self.stop_event = None
        self.stream_callback = None
        self.last_usage = None
        self.instances.append(self)

    def chat(self, messages, tools):
        self.calls.append({"messages": list(messages), "tools": list(tools or [])})
        assert not (self.settings.workspace_root / "demo" / "designspec.json").exists()
        return {"choices": [{"message": {"role": "assistant", "content": "Direct CAD flow."}}]}


class BrokenDesignSpecLLM:
    def __init__(self, _settings):
        self.stop_event = None
        self.stream_callback = None
        self.last_usage = None

    def chat(self, _messages, _tools):
        return {"choices": [{"message": {"role": "assistant", "content": "not json"}}]}


class ClarificationResumeFakeLLM:
    instances: ClassVar[list] = []
    route_calls = 0
    design_spec_calls = 0
    cad_calls = 0
    cad_spec_visible = False

    def __init__(self, settings):
        self.settings = settings
        self.calls = []
        self.stop_event = None
        self.stream_callback = None
        self.last_usage = None
        self.instances.append(self)

    def chat(self, messages, tools):
        self.calls.append({"messages": list(messages), "tools": list(tools or [])})
        tool_names = {
            tool["function"]["name"]
            for tool in tools or []
            if isinstance(tool, dict)
            and isinstance(tool.get("function"), dict)
            and isinstance(tool["function"].get("name"), str)
        }
        if "conversation_route" in tool_names:
            type(self).route_calls += 1
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps({"route": "design_change"}),
                        }
                    }
                ]
            }
        if "design_spec_generate" in tool_names:
            type(self).design_spec_calls += 1
            request = str(messages[-1].get("content", ""))
            if "6 mm" not in request:
                return {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "tool_calls": [
                                    {
                                        "id": "clarification-1",
                                        "function": {
                                            "name": "question",
                                            "arguments": json.dumps(
                                                {
                                                    "title": "Hole details",
                                                    "questions": [
                                                        {
                                                            "id": "hole_diameter",
                                                            "question": "What hole diameter should I use?",
                                                            "input_type": "number",
                                                        }
                                                    ],
                                                }
                                            ),
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                }
            response = {
                "schema_version": 1,
                "status": "ready",
                "request_summary": "A plate with a clarified mounting hole.",
                "part": {
                    "name": "clarified_plate",
                    "body": {"type": "plate", "description": "A rectangular plate."},
                    "design_features": [
                        {"type": "hole", "description": "One mounting hole."}
                    ],
                    "geometric_relations": [],
                    "design_requirements": ["The hole diameter must be 6 mm."],
                    "assumptions": [],
                },
                "design_parameters": [
                    {
                        "name": "hole_diameter",
                        "quantity_type": "length",
                        "original": {"value": 6, "unit": "mm"},
                        "source": "user_statement",
                    }
                ],
            }
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(response),
                        }
                    }
                ]
            }
        type(self).cad_calls += 1
        type(self).cad_spec_visible = (
            (self.settings.workspace_root / "demo" / "designspec.json").is_file()
        )
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "CAD modeling resumed.",
                    }
                }
            ]
        }


class ConversationFakeLLM:
    instances: ClassVar[list] = []

    def __init__(self, settings):
        self.settings = settings
        self.calls = []
        self.stop_event = None
        self.stream_callback = None
        self.last_usage = None
        self.instances.append(self)

    def chat(self, messages, tools):
        self.calls.append({"messages": list(messages), "tools": list(tools or [])})
        if len(self.calls) == 1:
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps({"route": "conversation"}),
                        }
                    }
                ]
            }
        assert tools == []
        assert any(
            message.get("role") == "user"
            and "<current_design_spec>" in str(message.get("content"))
            for message in messages
        )
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "The current plate is 50.8 mm wide.",
                    }
                }
            ]
        }


class ReplacementFakeLLM:
    instances: ClassVar[list] = []

    def __init__(self, settings):
        self.settings = settings
        self.calls = []
        self.designspec_calls = 0
        self.route_calls = 0
        self.stop_event = None
        self.stream_callback = None
        self.last_usage = None
        self.instances.append(self)

    def chat(self, messages, tools):
        self.calls.append({"messages": list(messages), "tools": list(tools or [])})
        tool_name = tools[0]["function"]["name"] if tools else None
        if tool_name == "conversation_route":
            self.route_calls += 1
            if (self.settings.workspace_root / "demo" / "designspec.json").is_file():
                assert any(
                    message.get("role") == "user"
                    and "width" in str(message.get("content"))
                    for message in messages
                )
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps({"route": "design_change"}),
                        }
                    }
                ]
            }
        if tool_name == "design_spec_generate":
            self.designspec_calls += 1
            if not (self.settings.workspace_root / "demo" / "designspec.json").is_file():
                return {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": json.dumps(READY_RESPONSE),
                            }
                        }
                    ]
                }
            assert any(
                message.get("role") == "user"
                and "tilt" in str(message.get("content"))
                and "geometric_relations" in str(message.get("content"))
                for message in messages
            )
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(
                                {
                                    "status": "ready",
                                    "request_summary": "A revised mounting plate.",
                                    "part": {
                                        "design_features": [
                                            {
                                                "type": "slot",
                                                "description": "One replacement slot.",
                                            }
                                        ],
                                        "design_requirements": [
                                            "The plate must have four holes."
                                        ],
                                    },
                                    "design_parameters": [
                                        {
                                            "name": "width",
                                            "quantity_type": "length",
                                            "original": {"value": 3, "unit": "cm"},
                                            "source": "user_statement",
                                        }
                                    ],
                                }
                            ),
                        }
                    }
                ]
            }
        assert tools
        assert any(
            message.get("role") == "user"
            and "<ready_design_spec>" in str(message.get("content"))
            for message in messages
        )
        return {
            "choices": [
                {"message": {"role": "assistant", "content": "CAD loop entered."}}
            ]
        }


def _new_project(app):
    client = app.test_client()
    assert client.post("/api/projects/new", json={"name": "demo"}).status_code == 201
    return client


def _wait_for_idle(client):
    for _ in range(300):
        if client.get("/api/projects/demo/state").get_json()["status"] == "idle":
            return
        time.sleep(0.01)
    raise AssertionError("The project Run did not reach a terminal state.")


def test_structured_spec_flag_defaults_off_and_loads_from_quality_config(tmp_path: Path):
    default = load_settings(project_root=tmp_path, home=tmp_path / "home")
    assert default.structured_spec is False

    (tmp_path / "config.yaml").write_text(
        "quality:\n  structured_spec: true\n", encoding="utf-8"
    )
    enabled = load_settings(project_root=tmp_path, home=tmp_path / "home")
    assert enabled.structured_spec is True


def test_designspec_api_reports_unavailable_before_first_spec(tmp_path: Path):
    settings = Settings(
        tmp_path / "projects",
        "https://example.test",
        "test-model",
        1,
        "127.0.0.1",
        5000,
        structured_spec=True,
    )
    client = _new_project(create_app(settings))

    response = client.get("/api/projects/demo/designspec")

    assert response.status_code == 200
    assert response.get_json() == {"available": False, "design_spec": None}


def test_blocking_design_clarification_resumes_same_change_before_cad(
    tmp_path: Path, monkeypatch
):
    import agent.core

    ClarificationResumeFakeLLM.instances.clear()
    ClarificationResumeFakeLLM.route_calls = 0
    ClarificationResumeFakeLLM.design_spec_calls = 0
    ClarificationResumeFakeLLM.cad_calls = 0
    ClarificationResumeFakeLLM.cad_spec_visible = False
    settings = Settings(
        tmp_path / "projects",
        "https://example.test",
        "test-model",
        1,
        "127.0.0.1",
        5000,
        structured_spec=True,
    )
    monkeypatch.setattr(agent.core, "OpenRouterClient", ClarificationResumeFakeLLM)
    app = create_app(settings)
    client = _new_project(app)
    project = settings.workspace_root / "demo"
    current = normalize_design_spec(
        {
            "status": "ready",
            "request_summary": "The existing plate.",
            "part": {"body": {"type": "plate", "description": "Existing plate."}},
        },
        "Make the existing plate.",
    )
    DesignSpecStore(project).save(current)
    spec_before = (project / "designspec.json").read_text(encoding="utf-8")

    assert client.post(
        "/api/chat",
        json={"project": "demo", "message": "Add a mounting hole to the plate."},
    ).status_code == 202
    for _ in range(300):
        state = client.get("/api/projects/demo/state").get_json()
        if state["status"] == "waiting_for_user":
            break
        time.sleep(0.01)
    else:
        raise AssertionError("The DesignSpec stage did not ask for clarification.")

    assert state["question"]["questions"][0]["input_type"] == "number"
    assert client.get("/api/projects/demo/designspec").get_json() == {
        "available": True,
        "design_spec": current,
    }
    assert (project / "designspec.json").read_text(encoding="utf-8") == spec_before
    assert not (project / "model.py").exists()
    assert ClarificationResumeFakeLLM.cad_calls == 0

    assert client.post(
        "/api/questions/answer",
        json={"project": "demo", "answers": {"hole_diameter": "6 mm"}},
    ).status_code == 202
    _wait_for_idle(client)

    spec = client.get("/api/projects/demo/designspec").get_json()["design_spec"]
    assert spec["request_summary"] == "A plate with a clarified mounting hole."
    parameter = spec["design_parameters"][0]
    assert parameter["name"] == "hole_diameter"
    assert parameter["original"] == {"value": 6, "unit": "mm"}
    assert parameter["normalized"] == {"value": 6.0, "unit": "mm"}
    assert spec["part"]["design_requirements"] == ["The hole diameter must be 6 mm."]
    assert ClarificationResumeFakeLLM.route_calls == 1
    assert ClarificationResumeFakeLLM.design_spec_calls == 2
    assert ClarificationResumeFakeLLM.cad_calls == 1
    assert ClarificationResumeFakeLLM.cad_spec_visible


def test_stop_abandons_pending_design_clarification_without_replacing_spec(
    tmp_path: Path, monkeypatch
):
    import agent.core

    ClarificationResumeFakeLLM.instances.clear()
    ClarificationResumeFakeLLM.route_calls = 0
    ClarificationResumeFakeLLM.design_spec_calls = 0
    ClarificationResumeFakeLLM.cad_calls = 0
    settings = Settings(
        tmp_path / "projects",
        "https://example.test",
        "test-model",
        1,
        "127.0.0.1",
        5000,
        structured_spec=True,
    )
    monkeypatch.setattr(agent.core, "OpenRouterClient", ClarificationResumeFakeLLM)
    app = create_app(settings)
    client = _new_project(app)
    project = settings.workspace_root / "demo"
    current = normalize_design_spec(
        {
            "status": "ready",
            "request_summary": "The existing plate.",
            "part": {"body": {"type": "plate", "description": "Existing plate."}},
        },
        "Make the existing plate.",
    )
    DesignSpecStore(project).save(current)
    spec_before = (project / "designspec.json").read_text(encoding="utf-8")

    assert client.post(
        "/api/chat",
        json={"project": "demo", "message": "Add a mounting hole to the plate."},
    ).status_code == 202
    for _ in range(300):
        if client.get("/api/projects/demo/state").get_json()["status"] == "waiting_for_user":
            break
        time.sleep(0.01)
    else:
        raise AssertionError("The DesignSpec stage did not ask for clarification.")

    response = client.post("/api/stop", json={"project": "demo"})

    assert response.status_code == 200
    _wait_for_idle(client)
    assert client.get("/api/projects/demo/designspec").get_json() == {
        "available": True,
        "design_spec": current,
    }
    assert (project / "designspec.json").read_text(encoding="utf-8") == spec_before
    assert not (project / ".agent_state.json").exists()
    assert ClarificationResumeFakeLLM.cad_calls == 0
    history = client.get("/api/projects/demo/history").get_json()["events"]
    assert any(event.get("type") == "agent_stopped" for event in history)


def test_conversation_answers_read_only_without_design_or_cad_mutation(
    tmp_path: Path, monkeypatch
):
    import agent.core

    ConversationFakeLLM.instances.clear()
    settings = Settings(
        tmp_path / "projects",
        "https://example.test",
        "test-model",
        1,
        "127.0.0.1",
        5000,
        structured_spec=True,
    )
    monkeypatch.setattr(agent.core, "OpenRouterClient", ConversationFakeLLM)
    app = create_app(settings)
    client = _new_project(app)
    project = settings.workspace_root / "demo"
    current = normalize_design_spec(
        {
            "status": "ready",
            "request_summary": "A mounting plate.",
            "part": {"body": {"type": "plate", "description": "A plate."}},
            "design_parameters": [
                {
                    "name": "width",
                    "quantity_type": "length",
                    "original": {"value": 2, "unit": "in"},
                    "source": "user_statement",
                }
            ],
        },
        "Make a plate.",
    )
    DesignSpecStore(project).save(current)
    model = project / "model.py"
    model.write_text("result = 'latest-successful-model'\n", encoding="utf-8")
    spec_before = (project / "designspec.json").read_text(encoding="utf-8")
    model_before = model.read_text(encoding="utf-8")
    assert not (project / ".cad-agent" / "history").exists()

    assert client.post(
        "/api/chat",
        json={"project": "demo", "message": "What is the current plate width?"},
    ).status_code == 202
    _wait_for_idle(client)

    fake = ConversationFakeLLM.instances[0]
    assert len(fake.calls) == 2
    assert fake.calls[0]["tools"][0]["function"]["name"] == "conversation_route"
    assert fake.calls[1]["tools"] == []
    assert client.get("/api/projects/demo/designspec").get_json() == {
        "available": True,
        "design_spec": current,
    }
    assert (project / "designspec.json").read_text(encoding="utf-8") == spec_before
    assert model.read_text(encoding="utf-8") == model_before
    assert not (project / ".cad-agent" / "history").exists()
    history = client.get("/api/projects/demo/history").get_json()["events"]
    assert history[-1]["role"] == "assistant"
    assert history[-1]["content"] == "The current plate is 50.8 mm wide."
    assert not any(
        event.get("type") == "design_spec_updated"
        or event.get("data", {}).get("status") == "designspec"
        for event in history
    )


def test_later_design_change_replaces_current_spec_and_retains_omitted_details(
    tmp_path: Path, monkeypatch
):
    import agent.core

    ReplacementFakeLLM.instances.clear()
    settings = Settings(
        tmp_path / "projects",
        "https://example.test",
        "test-model",
        1,
        "127.0.0.1",
        5000,
        structured_spec=True,
    )
    monkeypatch.setattr(agent.core, "OpenRouterClient", ReplacementFakeLLM)
    app = create_app(settings)
    client = _new_project(app)
    subscriber = app.config["EVENT_BUS"].subscribe()
    fake = None

    for index, message in enumerate(("Make the initial plate.", "Change its width to 3 cm."), 1):
        assert client.post(
            "/api/chat", json={"project": "demo", "message": message}
        ).status_code == 202
        for _ in range(300):
            if ReplacementFakeLLM.instances:
                fake = ReplacementFakeLLM.instances[-1]
            total_route_calls = sum(
                instance.route_calls for instance in ReplacementFakeLLM.instances
            )
            if (
                fake is not None
                and total_route_calls >= index
                and client.get("/api/projects/demo/state").get_json()["status"] == "idle"
            ):
                break
            time.sleep(0.01)
        else:
            state = client.get("/api/projects/demo/state").get_json()
            raise AssertionError(
                f"The project Run did not reach a terminal state: index={index}, "
                f"route_calls={fake.route_calls if fake else None}, "
                f"calls={len(fake.calls) if fake else None}, state={state}"
            )

    assert fake is not None
    assert sum(instance.route_calls for instance in ReplacementFakeLLM.instances) == 2
    assert sum(instance.designspec_calls for instance in ReplacementFakeLLM.instances) == 2
    spec = client.get("/api/projects/demo/designspec").get_json()["design_spec"]
    assert spec["request_summary"] == "A revised mounting plate."
    assert spec["part"]["body"] == READY_RESPONSE["part"]["body"]
    assert spec["part"]["design_features"] == [
        {"type": "slot", "description": "One replacement slot."}
    ]
    assert spec["part"]["geometric_relations"] == READY_RESPONSE["part"]["geometric_relations"]
    assert spec["part"]["design_requirements"] == [
        "The plate must remain a single solid.",
        "The plate must have four holes.",
    ]
    assert spec["part"]["assumptions"] == []
    parameters = {parameter["name"]: parameter for parameter in spec["design_parameters"]}
    assert parameters["width"]["original"] == {"value": 3.0, "unit": "cm"}
    assert parameters["width"]["normalized"] == {"value": 30.0, "unit": "mm"}
    assert parameters["tilt"]["original"] == READY_RESPONSE["design_parameters"][1]["original"]
    assert parameters["tilt"]["normalized"]["unit"] == "deg"

    updates = []
    try:
        while True:
            event = subscriber.get(timeout=0.2)
            if event["type"] == "design_spec_updated":
                updates.append(event)
    except queue.Empty:
        pass
    finally:
        app.config["EVENT_BUS"].unsubscribe(subscriber)
    assert len(updates) == 2
    assert list((settings.workspace_root / "demo").glob("*designspec*.json")) == [
        settings.workspace_root / "demo" / "designspec.json"
    ]


def test_disabled_structured_spec_preserves_direct_agent_flow(tmp_path: Path, monkeypatch):
    import agent.core

    DirectFlowFakeLLM.instances.clear()
    settings = Settings(
        tmp_path / "projects",
        "https://example.test",
        "test-model",
        1,
        "127.0.0.1",
        5000,
    )
    monkeypatch.setattr(agent.core, "OpenRouterClient", DirectFlowFakeLLM)
    app = create_app(settings)
    client = _new_project(app)

    assert client.post("/api/chat", json={"project": "demo", "message": "Make a plate."}).status_code == 202
    _wait_for_idle(client)

    fake = DirectFlowFakeLLM.instances[0]
    assert len(fake.calls) == 1
    assert fake.calls[0]["tools"]
    assert not (settings.workspace_root / "demo" / "designspec.json").exists()
    assert client.get("/api/projects/demo/designspec").get_json() == {
        "available": False,
        "design_spec": None,
    }


def test_enabled_design_change_persists_ready_spec_before_cad_loop(tmp_path: Path, monkeypatch):
    import agent.core

    OrderedFakeLLM.instances.clear()
    OrderedFakeLLM.api_visible = None
    settings = Settings(
        tmp_path / "projects",
        "https://example.test",
        "test-model",
        1,
        "127.0.0.1",
        5000,
        structured_spec=True,
    )
    monkeypatch.setattr(agent.core, "OpenRouterClient", OrderedFakeLLM)
    app = create_app(settings)
    client = _new_project(app)
    OrderedFakeLLM.api_visible = lambda: app.test_client().get(
        "/api/projects/demo/designspec"
    ).get_json()
    subscriber = app.config["EVENT_BUS"].subscribe()

    assert client.post(
        "/api/chat",
        json={"project": "demo", "message": "Make a 2 inch plate tilted 90 degrees."},
    ).status_code == 202
    _wait_for_idle(client)

    fake = OrderedFakeLLM.instances[0]
    assert len(fake.calls) == 3
    assert fake.calls[0]["tools"][0]["function"]["name"] == "conversation_route"
    assert fake.calls[0]["spec_exists"] is False
    assert fake.calls[1]["spec_exists"] is False
    assert fake.calls[2]["spec_exists"] is True

    response = client.get("/api/projects/demo/designspec")
    assert response.get_json()["available"] is True
    spec = response.get_json()["design_spec"]
    assert spec["status"] == "ready"
    assert spec["schema_version"] == 1
    assert spec["part"]["body"]["type"] == "plate"
    assert spec["part"]["design_features"][0]["type"] == "hole"
    assert spec["part"]["geometric_relations"][0]["type"] == "symmetry"
    assert spec["part"]["design_requirements"]
    assert spec["part"]["assumptions"]
    parameters = {parameter["name"]: parameter for parameter in spec["design_parameters"]}
    assert parameters["width"]["original"] == {"value": 2, "unit": "in"}
    assert parameters["width"]["normalized"] == {"value": 50.8, "unit": "mm"}
    assert parameters["width"]["source"] == "user_statement"
    assert parameters["tilt"]["normalized"] == {"value": 90.0, "unit": "deg"}

    event = None
    try:
        while True:
            candidate = subscriber.get(timeout=1)
            if candidate["type"] == "design_spec_updated":
                event = candidate
                break
    except queue.Empty:
        pass
    finally:
        app.config["EVENT_BUS"].unsubscribe(subscriber)
    assert event == {"type": "design_spec_updated", "data": {"project": "demo"}}

    design_spec_files = list((settings.workspace_root / "demo").glob("*designspec*.json"))
    assert [path.name for path in design_spec_files] == ["designspec.json"]


def test_designspec_failure_is_reported_without_creating_a_spec(tmp_path: Path, monkeypatch):
    import agent.core

    settings = Settings(
        tmp_path / "projects",
        "https://example.test",
        "test-model",
        1,
        "127.0.0.1",
        5000,
        structured_spec=True,
    )
    monkeypatch.setattr(agent.core, "OpenRouterClient", BrokenDesignSpecLLM)
    app = create_app(settings)
    client = _new_project(app)

    assert client.post(
        "/api/chat", json={"project": "demo", "message": "Make a plate."}
    ).status_code == 202
    _wait_for_idle(client)

    history = client.get("/api/projects/demo/history").get_json()["events"]
    assert any(
        event.get("type") == "agent_error"
        and "malformed JSON" in event.get("data", {}).get("message", "")
        for event in history
    )
    assert client.get("/api/projects/demo/designspec").get_json() == {
        "available": False,
        "design_spec": None,
    }
