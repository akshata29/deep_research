"""
Prompt templates for orchestration agents.
"""

from .agent_prompts import *
from .manager_prompts import *

__all__ = [
    "LEAD_RESEARCHER_PROMPT",
    "RESEARCHER_PROMPT", 
    "CREDIBILITY_CRITIC_PROMPT",
    "REFLECTION_CRITIC_PROMPT",
    "SUMMARIZER_PROMPT",
    "REPORT_WRITER_PROMPT",
    "CITATION_AGENT_PROMPT",
    "TRANSLATOR_PROMPT",
    "MANAGER_PROMPT",
    "FINAL_ANSWER_PROMPT"
]
