from __init__ import logger

from guardrails import Guard
from guardrails.hub import (
    GibberishText,
    ProfanityFree,
    ToxicLanguage,
)

class UserInteractionGR():
    def __init__(self):
        self.setup_guard()
        
    def setup_guard(self):
        self.guard = Guard().use_many(
            GibberishText(
                threshold=0.8,
                validation_method="sentence",
                on_fail="reask"
            ),
            ProfanityFree(
                on_fail="reask"
            ),
            ToxicLanguage(
                validation_method="sentence",
                threshold=0.8,
                on_fail="reask"
            )
        )

    def validate(self, agent_response):
        try:
            outcome = self.guard.validate(agent_response)
            return outcome
        except Exception as e:
            logger.error(f"Error in validating LLM response: {e}")
            return None