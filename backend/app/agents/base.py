import json
from abc import ABC, abstractmethod

from app.llm.provider import LLMClient


class BaseAgent(ABC):
    """Abstract base class for all agents in the analysis pipeline."""

    name: str = "base"
    description: str = "Base agent"

    def __init__(self, llm_client: LLMClient, language: str = "en") -> None:
        self.llm_client = llm_client
        self.language = language

    @abstractmethod
    async def run(self, context: dict) -> dict:
        """Execute the agent's analysis and return structured results."""
        ...

    def build_prompt(self, template: str, **kwargs) -> str:
        """Fill in a prompt template with the provided keyword arguments."""
        # Convert dict/list values to JSON strings for template insertion
        formatted_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, (dict, list)):
                formatted_kwargs[key] = json.dumps(value, indent=2, default=str)
            else:
                formatted_kwargs[key] = value
        return template.format(**formatted_kwargs)
