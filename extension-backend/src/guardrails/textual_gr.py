from __init__ import logger

import os
from guardrails import Guard
from guardrails.hub import (
    SaliencyCheck,
    ExtractedSummarySentencesMatch,
    LLMCritic
)

class TextualGR():
    def __init__(self, local_transcript_path):
        self.local_transcript_path = local_transcript_path
        self.docs_dir = os.path.sep.join(self.local_transcript_path.split(os.path.sep)[:-1])

    def setup_guard(self):
        self.guard = Guard().use_many(
            SaliencyCheck(
                docs_dir= self.docs_dir,
                threshold=0.4,
                on_fail="reask"
            ),
            ExtractedSummarySentencesMatch(
                filepaths=[self.local_transcript_path],
                threshold=0.4,
                on_fail="reask"
            ),
            LLMCritic(
            metrics={
                "informative": {
                    "description": "An informative summary captures the main points of the input and is free of irrelevant details.",
                    "threshold": 50,
                },
                "coherent": {
                    "description": "A coherent summary is logically organized and easy to follow.",
                    "threshold": 50,
                },
                "coverage": {
                    "description": "Summary contains all these sections - short summary, key items discussed, action items",
                    "threshold": 30
                }
            },
            max_score=100,
            llm_callable="gpt-3.5-turbo-0125",
            on_fail="reask",
            )
        )

        self.metadata = {
            "filepaths":[self.local_transcript_path]
            }
        

    def validate(self, summary):
        try:
            outcome = self.guard.validate(
                summary,
                metadata=self.metadata
                )
            return outcome
        except Exception as e:
            logger.error(f"Error in validating text: {e}")
            return None