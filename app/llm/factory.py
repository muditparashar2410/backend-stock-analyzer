from app.llm.base import LLMProvider
from app.llm.gemini import GeminiProvider
from app.config.settings import settings
from app.utils.logging import logger


def get_llm_provider() -> LLMProvider:
    """Factory function returning the configured LLMProvider implementation."""
    provider_type = settings.LLM_PROVIDER.lower()

    if provider_type == "gemini":
        return GeminiProvider()

    # Extension point for future providers (e.g. OpenAI, Anthropic)
    # elif provider_type == "openai":
    #     return OpenAIProvider()

    else:
        logger.warning(f"Unknown LLM_PROVIDER '{provider_type}'. Defaulting to GeminiProvider.")
        return GeminiProvider()
