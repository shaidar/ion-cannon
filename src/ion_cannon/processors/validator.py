# src/ion_cannon/processors/validator.py
import json
import logging
from typing import Dict, Optional

from llama_index.core import Settings

from ion_cannon.collectors.base import ContentItem
from ion_cannon.core.llm_factory import LLMFactory
from ion_cannon.processors.base import BaseProcessor
from ion_cannon.config.settings import settings

logger = logging.getLogger("ion_cannon")

class ContentValidator(BaseProcessor):
    """Validates content relevance using LLM(s)."""
    
    def __init__(self, use_multi_llm: bool = False, verbose: bool = False):
        self.use_multi_llm = use_multi_llm
        self.verbose = verbose
        # Initialize all instance variables
        self.validator1 = None
        self.validator2 = None
        self.validator = None
        self._setup_llms()

    def _setup_llms(self):
        """Initialize LLM(s) for validation."""
        try:
            if self.use_multi_llm:
                self.validator1, self.validator2 = LLMFactory.create_validation_llms(
                    require_both=False
                )
                if self.validator1 and self.validator2:
                    logger.info("Initialized multiple validation LLMs")
                elif self.validator1:
                    logger.warning("Only primary validator available, falling back to single LLM mode")
                    self.validator = self.validator1
                    self.use_multi_llm = False
                else:
                    logger.warning("No validators available, validation will be skipped")
            else:
                self.validator = LLMFactory.create_llm(require_llm=False)
                if self.validator:
                    logger.info("Initialized validation LLM")
                else:
                    logger.warning("No validator available, validation will be skipped")
        except Exception as e:
            logger.error(f"Failed to initialize validators: {str(e)}")
            self.validator = None
            self.validator1 = None
            self.validator2 = None
            self.use_multi_llm = False

    async def _safe_llm_completion(self, llm, content: str, validator_name: str = "validator") -> Optional[Dict]:
        """Safely handle LLM completion and response parsing."""
        # First ensure we have a valid LLM
        if llm is None:
            logger.error(f"{validator_name}: No LLM provided")
            return None

        # Set the LLM in Settings
        try:
            Settings.llm = llm
        except Exception as e:
            logger.error(f"{validator_name}: Failed to set LLM in Settings: {e}")
            return None

        # Prepare the content
        try:
            formatted_content = content[:200].strip()
            if self.verbose:
                logger.debug(f"{validator_name}: Using content (truncated): {formatted_content}")
        except Exception as e:
            logger.error(f"{validator_name}: Failed to format content: {e}")
            return None

        # Prepare the prompt
        prompt = f"""You are a content relevance analyzer specializing in AI and cybersecurity. Your task is to determine if the provided content specifically discusses the intersection of artificial intelligence/LLMs and cybersecurity.

Examples of RELEVANT content:
- Using AI/LLMs to detect security vulnerabilities
- AI-powered malware or attack vectors
- Protecting LLM systems from attacks/prompt injection
- AI/LLM security research findings
- Machine learning models being used in security tools
- Security implications of AI systems
- AI-based threat detection and response
- Adversarial attacks against AI systems
- Securing AI/ML pipelines
- AI/LLM security best practices

Examples of NOT RELEVANT content:
- General cybersecurity news without AI/LLM focus
- Basic AI/ML news without security aspects
- Traditional malware analysis
- Regular vulnerability reports
- Standard security tool updates
- General IT security practices
- Basic network security
- Traditional threat intelligence
- Regular data breaches without AI aspects
- General privacy issues without AI connection

Analyze the following content and return a JSON object with:
{{
    "is_relevant": boolean,
    "confidence": float (0-1),
    "primary_topic": string (main AI security topic discussed),
    "reason": string (brief explanation of decision),
    "key_aspects": [list of specific AI/LLM security elements mentioned]
}}

Only mark content as relevant if it substantively discusses the intersection of AI/LLM technology and security. If it merely mentions AI in passing while discussing general security, mark it as not relevant.

Content to analyze:
{formatted_content}"""

        try:
            # Make the LLM call
            if self.verbose:
                logger.debug(f"{validator_name}: Sending prompt to LLM")
            response = await Settings.llm.acomplete(prompt)

            # Check response
            if not response or not hasattr(response, 'text'):
                logger.error(f"{validator_name}: Invalid response from LLM")
                return None

            # Get response text
            response_text = response.text.strip()
            if self.verbose:
                logger.debug(f"{validator_name}: Raw LLM response:\n{response_text}")

            # Parse JSON
            result = json.loads(response_text)
            
            # Validate and normalize result
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")

            result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.9))))
            if "key_aspects" not in result:
                result["key_aspects"] = []

            return result

        except json.JSONDecodeError as e:
            logger.error(f"{validator_name}: JSON parsing error: {str(e)}")
            logger.error(f"{validator_name}: Problematic response:\n{response_text}")
            return None
        except Exception as e:
            logger.error(f"{validator_name}: Unexpected error during LLM completion: {str(e)}")
            return None


    async def _check_relevance(self, result: Dict) -> bool:
        """
        Check if a result meets our confidence threshold and relevance criteria.
        """
        # First check confidence threshold
        if result["confidence"] < settings.LLM_CONFIDENCE_THRESHOLD:
            if self.verbose:
                logger.debug(f"Confidence {result['confidence']} below threshold {settings.LLM_CONFIDENCE_THRESHOLD}")
            return False
            
        # If confidence is good, return the relevance decision
        return result["is_relevant"]

    async def process(self, item: ContentItem) -> Dict:
        """Process a content item through validation."""
        if (self.use_multi_llm and not (self.validator1 or self.validator2)) or \
           (not self.use_multi_llm and not self.validator):
            logger.warning("No validators available, marking content as not relevant by default")
            return {
                "is_relevant": False,
                "confidence": settings.LLM_VALIDATOR_CONFIDENCE,
                "validation_status": "skipped",
                "reason": "No validators available"
            }

        try:
            if self.use_multi_llm and self.validator1 and self.validator2:
                result1 = await self._safe_llm_completion(self.validator1, item.content, "validator1")
                if not result1:
                    logger.warning("Primary validator failed, falling back to single validator mode")
                    self.validator = self.validator1
                    self.use_multi_llm = False
                else:
                    result2 = await self._safe_llm_completion(self.validator2, item.content, "validator2")
                    if result2:
                        # Check if both results meet confidence threshold and agree on relevance
                        is_confident_and_relevant = (
                            await self._check_relevance(result1) and 
                            await self._check_relevance(result2)
                        )
                        
                        return {
                            "is_relevant": is_confident_and_relevant,
                            "confidence": min(result1["confidence"], result2["confidence"]),
                            "primary_topic": result1["primary_topic"],
                            "reason": result1["reason"] if is_confident_and_relevant else 
                                    f"Confidence threshold not met (scores: {result1['confidence']}, {result2['confidence']})",
                            "key_aspects": result1["key_aspects"] if is_confident_and_relevant else [],
                            "validation_status": "multi_llm"
                        }
            
            # Single validator mode (either by choice or fallback)
            validator = self.validator1 if self.use_multi_llm else self.validator
            if validator:
                result = await self._safe_llm_completion(validator, item.content)
                if result:
                    is_confident_and_relevant = await self._check_relevance(result)
                    return {
                        "is_relevant": is_confident_and_relevant,
                        "confidence": result["confidence"],
                        "primary_topic": result["primary_topic"],
                        "reason": result["reason"] if is_confident_and_relevant else 
                                f"Confidence threshold not met (score: {result['confidence']})",
                        "key_aspects": result["key_aspects"] if is_confident_and_relevant else [],
                        "validation_status": "single_llm"
                    }
            
            # If all validation attempts failed
            logger.warning(f"All validation attempts failed for {item.url}")
            return {
                "is_relevant": False,  # Not relevant on error
                "confidence": settings.LLM_VALIDATOR_CONFIDENCE,
                "validation_status": "error",
                "reason": "Validation failed"
            }
                
        except Exception as e:
            logger.error(f"Validation failed for {item.url}: {str(e)}")
            return {
                "is_relevant": False,  # Not relevant on error
                "confidence": settings.LLM_VALIDATOR_CONFIDENCE,
                "validation_status": "error",
                "reason": f"Error: {str(e)}"
            }