import json
import queue
import time
from pathlib import Path
from typing import ClassVar

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
            return {"choices": [{"message": {"role": "assistant", "content": json.dumps(READY_RESPONSE)}}]}
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
    assert len(fake.calls) == 2
    assert fake.calls[0]["tools"][0]["function"]["name"] == "design_spec_generate"
    assert fake.calls[0]["spec_exists"] is False
    assert fake.calls[1]["spec_exists"] is True

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
