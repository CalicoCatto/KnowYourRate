import asyncio
import json
import logging
import os
import re

import litellm

from app.llm.registry import SUPPORTED_PROVIDERS

logger = logging.getLogger(__name__)

# Suppress litellm's verbose logging
litellm.suppress_debug_info = True

# Regex to strip <think>...</think> blocks from reasoning model outputs
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class LLMClient:
    """Wrapper around litellm.acompletion for multi-provider LLM access."""

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str | None = None,
        max_retries: int = 3,
    ) -> None:
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")

        self.provider = provider
        self.api_key = api_key
        self.max_retries = max_retries

        provider_info = SUPPORTED_PROVIDERS[provider]
        self.model = model or provider_info["models"][0]

        # Custom API base URL for OpenAI-compatible providers (Moonshot, SiliconFlow)
        self.api_base: str | None = provider_info.get("api_base")

        # Models that reject explicit temperature values (e.g. Kimi K2.5 reasoning model)
        self._skip_temperature_models: list[str] = provider_info.get("skip_temperature_models", [])

        # Ensure the model has the correct litellm prefix
        prefix = provider_info["litellm_prefix"]
        if prefix and not self.model.startswith(prefix):
            self.litellm_model = f"{prefix}{self.model}"
        else:
            self.litellm_model = self.model

        # Set the API key in the environment for litellm
        env_key = provider_info["env_key"]
        os.environ[env_key] = api_key

    def _should_skip_temperature(self) -> bool:
        """Check if the current model rejects explicit temperature values."""
        return self.model in self._skip_temperature_models

    @staticmethod
    def _strip_think_tags(text: str) -> str:
        """Remove <think>...</think> blocks from reasoning model outputs."""
        return _THINK_RE.sub("", text).strip()

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        response_format: dict | None = None,
    ) -> str:
        """Send a chat completion request and return the response text."""
        kwargs: dict = {
            "model": self.litellm_model,
            "messages": messages,
            "api_key": self.api_key,
        }

        # Some reasoning models (e.g. Kimi K2.5) reject temperature != 1
        if not self._should_skip_temperature():
            kwargs["temperature"] = temperature

        if self.api_base:
            kwargs["api_base"] = self.api_base

        if response_format:
            kwargs["response_format"] = response_format

        response = await self._call_with_retry(**kwargs)
        text = response.choices[0].message.content or ""

        # Strip <think> blocks from reasoning model outputs
        text = self._strip_think_tags(text)

        return text

    async def chat_json(
        self,
        messages: list[dict],
        temperature: float = 0.3,
    ) -> dict:
        """Send a chat request and parse the response as JSON."""
        # Append instruction to return JSON
        enhanced_messages = list(messages)
        if enhanced_messages:
            last = enhanced_messages[-1]
            enhanced_messages[-1] = {
                **last,
                "content": last["content"] + "\n\nRespond with valid JSON only. No markdown, no code fences.",
            }

        raw = await self.chat(
            messages=enhanced_messages,
            temperature=temperature,
        )

        # Try to parse JSON, stripping common wrappers
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = lines[1:]  # Remove opening fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]  # Remove closing fence
            cleaned = "\n".join(lines).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON response, returning raw text wrapped")
            return {"raw_response": raw}

    async def _call_with_retry(self, **kwargs) -> object:
        """Call litellm.acompletion with exponential backoff on rate limits."""
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                return await litellm.acompletion(**kwargs)
            except litellm.RateLimitError as e:
                last_error = e
                wait = 2 ** attempt
                logger.warning(
                    "Rate limited (attempt %d/%d), retrying in %ds...",
                    attempt + 1,
                    self.max_retries,
                    wait,
                )
                await asyncio.sleep(wait)
            except litellm.APIConnectionError as e:
                last_error = e
                wait = 2 ** attempt
                logger.warning(
                    "API connection error (attempt %d/%d), retrying in %ds...",
                    attempt + 1,
                    self.max_retries,
                    wait,
                )
                await asyncio.sleep(wait)
            except Exception as e:
                raise

        raise last_error  # type: ignore[misc]
