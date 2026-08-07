"""Provider-neutral OpenAI Chat Completions client exports."""

from agent.openrouter import (
    OpenAICompatibleClient,
    OpenRouterClient,
    sanitize_assistant_message,
)

__all__ = [
    "OpenAICompatibleClient",
    "OpenRouterClient",
    "sanitize_assistant_message",
]
