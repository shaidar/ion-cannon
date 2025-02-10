# src/ion_cannon/core/llm_factory.py
import logging
from typing import Optional, Tuple

from llama_index.core import Settings
from llama_index.core.llms import LLM
from llama_index.llms.openai import OpenAI
from llama_index.llms.ollama import Ollama

from ion_cannon.config.settings import settings

logger = logging.getLogger("ion_cannon")

class LLMFactory:
    """Factory class for creating LLM instances."""

    @staticmethod
    def create_llm(
        provider: Optional[str] = None,
        model: Optional[str] = None,
        require_llm: bool = True,
    ) -> Optional[LLM]:
        """Create and return an LLM instance based on provided settings or config."""
        provider = provider or settings.LLM_PROVIDER
        model = model or settings.LLM_MODEL

        try:
            if provider.lower() == "openai":
                if not settings.OPENAI_API_KEY:
                    msg = "OpenAI API key not found in environment"
                    if require_llm:
                        raise ValueError(msg)
                    logger.warning(msg)
                    return None
                
                llm = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    model=model,
                    max_tokens=settings.LLM_MAX_TOKENS_RESPONSE,
                    temperature=settings.LLM_TEMPERATURE,
                    json_mode=True,
                )
                Settings.llm = llm
                return llm
                
            elif provider.lower() == "ollama":
                llm = Ollama(
                    model=model,
                    temperature=settings.LLM_TEMPERATURE,
                    json_mode=True,
                )
                Settings.llm = llm
                return llm
                
            else:
                msg = f"Unsupported LLM provider: {provider}"
                if require_llm:
                    raise ValueError(msg)
                logger.warning(msg)
                return None
                
        except Exception as e:
            msg = f"Failed to create LLM instance: {str(e)}"
            if require_llm:
                raise ValueError(msg) from e
            logger.warning(msg)
            return None

    @staticmethod
    def create_validation_llms(require_both: bool = True) -> Tuple[Optional[LLM], Optional[LLM]]:
        """Create LLM instances for content validation."""
        validator1 = LLMFactory.create_llm(
            provider=settings.VALIDATOR1_PROVIDER,
            model=settings.VALIDATOR1_MODEL,
            require_llm=require_both
        )
        
        validator2 = LLMFactory.create_llm(
            provider=settings.VALIDATOR2_PROVIDER,
            model=settings.VALIDATOR2_MODEL,
            require_llm=require_both
        )
        
        return validator1, validator2

    @staticmethod
    def create_summarization_llm(required: bool = True) -> Optional[LLM]:
        """Create LLM instance for content summarization."""
        return LLMFactory.create_llm(
            provider=settings.SUMMARIZER_PROVIDER,
            model=settings.SUMMARIZER_MODEL,
            require_llm=required
        )