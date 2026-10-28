"""
Pick the LLM provider from LLM_PROVIDER (gemini | openai).

    from app.providers import get_chat_model, get_embedder
    get_chat_model().generate("Hello")

use_providers() swaps in your own implementations (tests, custom setups).
"""
from app.config import settings
from app.providers.base import ChatModel, Embedder, ProviderError

__all__ = ["ChatModel", "Embedder", "ProviderError", "get_chat_model", "get_embedder", "use_providers"]

_chat: ChatModel | None = None
_embedder: Embedder | None = None


def get_chat_model() -> ChatModel:
    global _chat
    if _chat is None:
        if settings.llm_provider == "openai":
            from app.providers.openai import OpenAIChat
            _chat = OpenAIChat(settings.openai_api_key, settings.chat_model)
        else:
            from app.providers.gemini import GeminiChat
            _chat = GeminiChat(settings.gemini_api_key, settings.chat_model)
    return _chat


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        if settings.llm_provider == "openai":
            from app.providers.openai import OpenAIEmbedder
            _embedder = OpenAIEmbedder(settings.openai_api_key, settings.embed_model, settings.embed_dim)
        else:
            from app.providers.gemini import GeminiEmbedder
            _embedder = GeminiEmbedder(settings.gemini_api_key, settings.embed_model, settings.embed_dim)
    return _embedder


_KEEP = object()


def use_providers(chat: ChatModel | None = _KEEP, embedder: Embedder | None = _KEEP) -> None:
    """Replace the active chat model and/or embedder. Pass None to go back to the configured one."""
    global _chat, _embedder
    if chat is not _KEEP:
        _chat = chat
    if embedder is not _KEEP:
        _embedder = embedder
