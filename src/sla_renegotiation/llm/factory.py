from typing import Any

import aiolimiter
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from sla_renegotiation.config import settings

llm_rate_limiter = aiolimiter.AsyncLimiter(max_rate=3, time_period=1)

_MODEL_KEY_MAP: dict[str, str] = {
    "client": settings.client_model,
    "provider": settings.provider_model,
    "profiling": settings.profiling_model,
    "judge": settings.judge_model,
    "rc": settings.rc_model,
}


def _is_nvidia_model(model_id: str) -> bool:
    model_lower = model_id.lower()
    return (
        "nvidia" in model_lower
        or model_lower.startswith("nvapi-")
        or model_lower.startswith("z-ai/")
    )


def _resolve_api_key(model_id: str) -> str | None:
    model_lower = model_id.lower()
    if settings.mistralai_api_key and "mistral" in model_lower:
        return settings.mistralai_api_key
    if settings.openai_api_key and (
        "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower
    ):
        return settings.openai_api_key
    if settings.anthropic_api_key and ("claude" in model_lower or "anthropic" in model_lower):
        return settings.anthropic_api_key
    if settings.nvidia_api_key and _is_nvidia_model(model_id):
        return settings.nvidia_api_key
    return None


def build_model(
    role: str, temperature: float = 0.0, model_kwargs: dict[str, Any] | None = None
) -> BaseChatModel:
    model_id = _MODEL_KEY_MAP.get(role, settings.client_model)
    kwargs: dict[str, Any] = {"temperature": temperature}
    api_key = _resolve_api_key(model_id)
    if api_key:
        kwargs["api_key"] = api_key
    if _is_nvidia_model(model_id):
        kwargs["model_provider"] = "nvidia"
        if model_kwargs:
            kwargs.update(model_kwargs)
    return init_chat_model(model_id, **kwargs)
