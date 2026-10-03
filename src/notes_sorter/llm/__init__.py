from notes_sorter.config import Settings
from notes_sorter.llm.base import LLMProvider


def build_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "anthropic":
        from notes_sorter.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(settings)
    if settings.llm_provider == "openai":
        from notes_sorter.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(settings)
    if settings.llm_provider == "ollama":
        from notes_sorter.llm.ollama_provider import OllamaProvider

        return OllamaProvider(settings)
    raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")


__all__ = ["LLMProvider", "build_provider"]
