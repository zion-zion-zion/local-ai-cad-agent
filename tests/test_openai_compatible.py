from pathlib import Path

from agent.openai_client import OpenAICompatibleClient
from agent.settings import load_settings


class JsonResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": []}


def test_openai_endpoint_uses_standard_payload_and_openai_key(monkeypatch, tmp_path: Path):
    captured = {}

    def post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return JsonResponse()

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setattr("agent.openrouter.requests.post", post)

    config_root = tmp_path / "config-root"
    config_root.mkdir()
    (config_root / "config.yaml").write_text(
        """llm:
  base_url: https://llm.example/v1
  api_key_env: OPENAI_API_KEY
  model: gpt-4.1-mini
  reasoning_effort: high
  provider: openai
  force_provider: true
  enable_anthropic_cache: true
  app_title: custom title
  app_url: https://example.test
""",
        encoding="utf-8",
    )
    settings = load_settings(project_root=config_root, home=tmp_path / "home")

    OpenAICompatibleClient(settings).chat(
        [{"role": "user", "content": "Build a bracket."}],
        tools=[{"type": "function", "function": {"name": "cad", "parameters": {}}}],
    )

    payload = captured["json"]
    assert captured["url"] == "https://llm.example/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer openai-test-key"
    assert payload["model"] == "gpt-4.1-mini"
    assert payload["reasoning_effort"] == "high"
    assert payload["tools"][0]["function"]["name"] == "cad"
    assert "provider" not in payload
    assert "session_id" not in payload
    assert "cache_control" not in payload
    assert "X-OpenRouter-Title" not in captured["headers"]
    assert "HTTP-Referer" not in captured["headers"]


def test_legacy_openrouter_config_still_enables_extensions(tmp_path: Path):
    config_root = tmp_path / "config-root"
    config_root.mkdir()
    (config_root / "config.yaml").write_text(
        """openrouter:
  base_url: https://openrouter.ai/api/v1
  model: openai/gpt-4o-mini
  provider: openai
  force_provider: true
""",
        encoding="utf-8",
    )

    settings = load_settings(project_root=config_root, home=tmp_path / "home")

    assert settings.api_key_env == "OPENROUTER_API_KEY"
    assert settings.is_openrouter
    assert settings.provider == "openai"
