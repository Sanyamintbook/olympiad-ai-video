import json
import time
from typing import Any

import httpx
from loguru import logger

from app.config.settings import get_settings
from app.core.exceptions import (
    AIProviderException,
    ProviderAuthenticationException,
    ProviderResponseException,
    ProviderTimeoutException,
)
from app.infrastructure.ai.providers.base import LLMProvider
from app.infrastructure.ai.schemas.llm_response import LLMResponse


class OllamaProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.default_model

    async def _resolve_local_model(self) -> None:
        import os
        env_model = os.environ.get("LOCAL_MODEL")
        if env_model:
            self.model = env_model
            logger.info(f"Ollama using environment-configured local model: {self.model}")
            return

        if "gemini" in self.model.lower():
            try:
                async with httpx.AsyncClient(timeout=get_settings().ollama_connect_timeout_seconds) as client:
                    response = await client.get(f"{self.base_url}/api/tags")
                    if response.status_code == 200:
                        data = response.json()
                        models = [m["name"] for m in data.get("models", [])]
                        gen_models = [m for m in models if "embed" not in m.lower()]
                        if gen_models:
                            # Prioritize larger/better models if present
                            for p_model in ["qwen3:8b", "qwen2.5:7b", "qwen2.5:3b"]:
                                for gm in gen_models:
                                    if p_model in gm:
                                        self.model = gm
                                        logger.info(f"Ollama dynamically mapped Gemini model to local model: {self.model}")
                                        return
                            self.model = gen_models[0]
                            logger.info(f"Ollama dynamically mapped Gemini model to first available local model: {self.model}")
            except Exception as e:
                logger.warning(f"Failed to dynamically resolve Ollama model: {str(e)}")

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        await self._resolve_local_model()
        start_time = time.perf_counter()
        logger.info("ollama_request_started provider=ollama model={model}", model=self.model)
        settings = get_settings()
        timeout = float(kwargs.pop("timeout", settings.ollama_request_timeout_seconds))
        num_predict = int(kwargs.pop("num_predict", settings.ollama_num_predict))
        response_format = kwargs.pop("format", None)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": num_predict,
                "num_ctx": settings.ollama_context_window
            },
        }
        if response_format:
            payload["format"] = response_format
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                if hasattr(response, "raise_for_status"):
                    response.raise_for_status()
                if hasattr(response, "json"):
                    json_payload = response.json()
                    data = await json_payload if hasattr(json_payload, "__await__") else json_payload
                else:
                    data = {}
        except (TimeoutError, httpx.TimeoutException) as exc:
            logger.exception("ollama_request_failed provider=ollama model={model} error=timeout", model=self.model)
            raise ProviderTimeoutException("Ollama request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code in {401, 403}:
                logger.warning("ollama_request_failed provider=ollama model={model} reason=auth", model=self.model)
                raise ProviderAuthenticationException("Ollama authentication failed.") from exc
            logger.exception("ollama_request_failed provider=ollama model={model} error={error}", model=self.model, error=exc.response.status_code if exc.response else "http")
            raise AIProviderException(f"Ollama generation failed: {exc}") from exc
        except httpx.HTTPError as exc:
            logger.exception("ollama_request_failed provider=ollama model={model} error={error}", model=self.model, error=type(exc).__name__)
            raise AIProviderException(f"Ollama generation failed: {exc}") from exc

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        content = data.get("response", "")
        logger.info(
            "ollama_request_completed provider=ollama model={model} latency_ms={latency_ms}",
            model=self.model,
            latency_ms=latency_ms,
        )
        return LLMResponse(
            provider="ollama",
            model=self.model,
            content=content,
            latency_ms=float(latency_ms),
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: dict,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> dict:
        # ADVANCED FIX: Passing a complex JSON schema dict directly to Ollama's format parameter 
        # causes small local models (like 8B) to suffer from grammar-constraint corruption, 
        # resulting in them outputting raw strings or arrays instead of the object. 
        # We also DO NOT use standard "json" mode because it can cause the model to freeze 
        # and return an empty string when overwhelmed. Our regex handles extraction perfectly.
        # kwargs["format"] = "json"
        for attempt in range(2):
            raw_response = await self.generate(prompt, system_prompt=system_prompt, **kwargs)
            try:
                text = raw_response.content.strip()
                import re
                json_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
                if json_match:
                    text = json_match.group(1)
                else:
                    if text.startswith("```json"):
                        text = text[7:]
                    elif text.startswith("```"):
                        text = text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                parsed = json.loads(text)
            except json.JSONDecodeError as jde:
                logger.warning(f"Ollama JSON parsing failed on attempt {attempt + 1}. Error: {str(jde)}. Raw content preview: {raw_response.content[:500]}")
                if attempt == 1:
                    raise ProviderResponseException(f"Ollama returned invalid JSON for structured generation. Raw: {raw_response.content[:200]}")
                
                prompt = prompt + f"\n\n[SYSTEM NOTICE]: Your previous attempt failed to parse as valid JSON. Error: {str(jde)}.\nHere is the malformed output you generated:\n```json\n{raw_response.content}\n```\nPlease carefully fix the syntax errors (such as missing commas, unclosed strings, or mismatched brackets) and output ONLY valid JSON."
                continue

            if not isinstance(parsed, (dict, list)):
                raise ProviderResponseException("Ollama structured response was not a JSON object or array.")

            return parsed

        raise ProviderResponseException("Ollama returned invalid JSON for structured generation.")

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=get_settings().ollama_connect_timeout_seconds) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                return True
        except (httpx.HTTPError, TimeoutError):
            return False
