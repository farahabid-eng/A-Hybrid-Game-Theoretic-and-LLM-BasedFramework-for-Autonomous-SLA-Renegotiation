from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from sla_renegotiation.config import settings


_MODEL_KEY_MAP: dict[str, str] = {
    "client": settings.client_model,
    "provider": settings.provider_model,
    "profiling": settings.profiling_model,
    "rc": settings.rc_model,
}


def _resolve_api_key(model_id: str) -> str | None:
    model_lower = model_id.lower()
    if settings.mistralai_api_key and "mistral" in model_lower:
        return settings.mistralai_api_key
    if settings.openai_api_key and ("gpt" in model_lower or "o1" in model_lower or "o3" in model_lower):
        return settings.openai_api_key
    if settings.anthropic_api_key and ("claude" in model_lower or "anthropic" in model_lower):
        return settings.anthropic_api_key
    return None


def build_model(role: str, temperature: float = 0.0) -> BaseChatModel:
    model_id = _MODEL_KEY_MAP.get(role, settings.client_model)
    kwargs: dict[str, Any] = {"temperature": temperature}
    api_key = _resolve_api_key(model_id)
    if api_key:
        kwargs["api_key"] = api_key
    return init_chat_model(model_id, **kwargs)
