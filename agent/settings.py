"""Configuration loading for the local CAD agent."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

REASONING_EFFORTS = {"minimal", "low", "medium", "high"}


@dataclass(frozen=True)
class Settings:
    workspace_root: Path
    # These field names are retained for constructor compatibility with older
    # integrations. The public properties below expose provider-neutral names.
    openrouter_base_url: str
    openrouter_model: str
    openrouter_timeout_seconds: int
    host: str
    port: int
    openrouter_app_title: str = "Local AI CAD Agent"
    openrouter_app_url: str = ""
    openrouter_session_prefix: str = "local-ai-cad-agent"
    openrouter_enable_anthropic_cache: bool = True
    openrouter_reasoning_effort: str | None = None
    openrouter_provider: str | None = None
    openrouter_force_provider: bool = False
    show_info_messages: bool = True
    agent_tool_call_limit: int = 12
    revision_retention_count: int = 0  # 0 = unlimited, >0 = keep at most N revisions
    quality_enabled: bool = True  # passive run/attempt observability (plan Phase 1)
    quality_require_acceptance_before_finalize: bool = False  # plan Phase 2 gate (rollout stage 7)
    api_key_env: str = "OPENAI_API_KEY"
    # ``None`` preserves inference for direct legacy Settings construction;
    # load_settings() sets this explicitly from the selected config section.
    openrouter_extensions: bool | None = None

    @property
    def base_url(self) -> str:
        return self.openrouter_base_url

    @property
    def model(self) -> str:
        return self.openrouter_model

    @property
    def timeout_seconds(self) -> int:
        return self.openrouter_timeout_seconds

    @property
    def app_title(self) -> str:
        return self.openrouter_app_title

    @property
    def app_url(self) -> str:
        return self.openrouter_app_url

    @property
    def session_prefix(self) -> str:
        return self.openrouter_session_prefix

    @property
    def enable_anthropic_cache(self) -> bool:
        return self.openrouter_enable_anthropic_cache

    @property
    def reasoning_effort(self) -> str | None:
        return self.openrouter_reasoning_effort

    @property
    def provider(self) -> str | None:
        return self.openrouter_provider

    @property
    def force_provider(self) -> bool:
        return self.openrouter_force_provider

    @property
    def is_openrouter(self) -> bool:
        """Whether OpenRouter-only request extensions are explicitly enabled."""
        hostname = (urlparse(self.base_url).hostname or "").lower()
        if self.openrouter_extensions is not None:
            return self.openrouter_extensions
        return (
            hostname == "openrouter.ai"
            or hostname.endswith(".openrouter.ai")
            or bool(self.provider)
            or self.force_provider
            or bool(self.app_url)
            or self.app_title != "Local AI CAD Agent"
        )

def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as config_file:
        data = yaml.safe_load(config_file) or {}
    if not isinstance(data, dict):
        raise TypeError(f"Configuration must be a mapping: {path}")
    return data


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _strict_bool(value: Any, name: str) -> bool:
    """Reject stringly-typed boolean values so YAML quoted booleans fail fast."""
    if value is True or value is False:
        return value
    raise TypeError(f"{name} must be true or false, got {value!r} (quoted booleans like \"false\" are not supported).")


def _validate_port(value: Any, name: str) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be an integer between 1 and 65535.") from error
    if port < 1 or port > 65535:
        raise ValueError(f"{name} must be between 1 and 65535, got {port}.")
    return port


def _validate_timeout_seconds(value: Any, name: str) -> int:
    return _positive_int(value, name)


def load_settings(project_root: Path | None = None, home: Path | None = None) -> Settings:
    project_root = project_root or Path(__file__).resolve().parents[1]
    home = home or Path.home()
    config = _merge(_read_yaml(project_root / "config.yaml"), _read_yaml(home / ".cad-agent" / "config.yaml"))
    llm = config.get("llm")
    legacy_openrouter = config.get("openrouter")
    using_legacy_openrouter = not isinstance(llm, dict) and isinstance(legacy_openrouter, dict)
    if not isinstance(llm, dict):
        llm = legacy_openrouter if isinstance(legacy_openrouter, dict) else {}
    server = config.get("server", {})
    ui = config.get("ui", {})
    agent = config.get("agent", {})
    quality = config.get("quality", {})

    quality_enabled = _strict_bool(quality.get("enabled", True), "quality.enabled")
    quality_require_acceptance = _strict_bool(
        quality.get("require_acceptance_before_finalize", False),
        "quality.require_acceptance_before_finalize",
    )
    if not quality_enabled and quality_require_acceptance:
        raise ValueError(
            "quality.require_acceptance_before_finalize=true requires quality.enabled=true. "
            "Enable quality or disable the acceptance gate."
        )

    return Settings(
        workspace_root=Path(config.get("workspace_root", "~/CAD-Agent-Projects")).expanduser(),
        openrouter_base_url=_required_string(
            llm.get("base_url", "https://api.openai.com/v1"),
            "llm.base_url" if not using_legacy_openrouter else "openrouter.base_url",
        ).rstrip("/"),
        openrouter_model=_required_string(
            llm.get("model", "gpt-4o-mini"),
            "llm.model" if not using_legacy_openrouter else "openrouter.model",
        ),
        openrouter_timeout_seconds=_validate_timeout_seconds(
            llm.get("timeout_seconds", 60),
            "llm.timeout_seconds" if not using_legacy_openrouter else "openrouter.timeout_seconds",
        ),
        host=str(server.get("host", "127.0.0.1")),
        port=_validate_port(server.get("port", 5000), "server.port"),
        api_key_env=_validate_env_name(
            llm.get("api_key_env", "OPENROUTER_API_KEY" if using_legacy_openrouter else "OPENAI_API_KEY"),
            "llm.api_key_env" if not using_legacy_openrouter else "openrouter.api_key_env",
        ),
        openrouter_app_title=str(llm.get("app_title", "Local AI CAD Agent")),
        openrouter_app_url=str(llm.get("app_url", "")).rstrip("/"),
        openrouter_session_prefix=str(llm.get("session_prefix", "local-ai-cad-agent")),
        openrouter_enable_anthropic_cache=_strict_bool(
            llm.get("enable_anthropic_cache", using_legacy_openrouter),
            "llm.enable_anthropic_cache" if not using_legacy_openrouter else "openrouter.enable_anthropic_cache",
        ),
        openrouter_reasoning_effort=_optional_effort(
            llm.get("reasoning_effort"),
            "llm.reasoning_effort" if not using_legacy_openrouter else "openrouter.reasoning_effort",
        ),
        openrouter_provider=_optional_string(llm.get("provider")),
        openrouter_force_provider=_strict_bool(
            llm.get("force_provider", False),
            "llm.force_provider" if not using_legacy_openrouter else "openrouter.force_provider",
        ),
        openrouter_extensions=using_legacy_openrouter or _is_openrouter_url(str(llm.get("base_url", ""))),
        show_info_messages=_strict_bool(ui.get("show_info_messages", True), "ui.show_info_messages"),
        agent_tool_call_limit=_positive_int(agent.get("tool_call_limit", 12), "agent.tool_call_limit"),
        revision_retention_count=_non_negative_int(agent.get("revision_retention_count", 0), "agent.revision_retention_count"),
        quality_enabled=quality_enabled,
        quality_require_acceptance_before_finalize=quality_require_acceptance,
    )


def _optional_string(value: Any) -> str | None:
    value = str(value).strip() if value is not None else ""
    return value or None


def _optional_effort(value: Any, name: str = "llm.reasoning_effort") -> str | None:
    effort = _optional_string(value)
    if effort is not None and effort not in REASONING_EFFORTS:
        raise ValueError(f"{name} must be minimal, low, medium, or high.")
    return effort


def _required_string(value: Any, name: str) -> str:
    result = str(value).strip() if value is not None else ""
    if not result:
        raise ValueError(f"{name} must not be empty.")
    return result


def _validate_env_name(value: Any, name: str) -> str:
    result = _required_string(value, name)
    if not result.replace("_", "").isalnum() or result[0].isdigit():
        raise ValueError(f"{name} must be a valid environment variable name.")
    return result


def _is_openrouter_url(value: str) -> bool:
    hostname = (urlparse(value).hostname or "").lower()
    return hostname == "openrouter.ai" or hostname.endswith(".openrouter.ai")


def _positive_int(value: Any, name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a positive integer.") from error
    if number < 1:
        raise ValueError(f"{name} must be a positive integer.")
    return number


def _non_negative_int(value: Any, name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a non-negative integer.") from error
    if number < 0:
        raise ValueError(f"{name} must be a non-negative integer.")
    return number


def resolve_api_key(settings: Settings) -> tuple[str | None, str]:
    """Resolve the configured API key, with legacy environment fallbacks."""
    names = [settings.api_key_env, "OPENAI_API_KEY", "OPENROUTER_API_KEY"]
    seen: set[str] = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        value = os.getenv(name, "").strip()
        if value:
            return value, name
    return None, settings.api_key_env
