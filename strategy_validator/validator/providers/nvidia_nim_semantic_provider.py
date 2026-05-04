"""NVIDIA NIM OpenAI-compatible semantic provider.

This module intentionally uses stdlib HTTP so the repo can keep the connector optional.
It is designed for provisional temporal semantic extraction; authoritative canonical writes
must still flow through verification + daily materialization.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from hashlib import sha256
from typing import Any

from pydantic import BaseModel


class NvidiaNimTemporalSemanticProvider:
    def __init__(
        self,
        provider_id: str,
        *,
        base_url: str = "https://integrate.api.nvidia.com/v1",
        api_key_env: str = "NVIDIA_NIM_API_KEY",
        model: str = "minimaxai/minimax-m2.7",
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
    ):
        self.provider_id = provider_id
        self._base_url = base_url.rstrip("/")
        self._api_key_env = api_key_env
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

    @property
    def model(self) -> str:
        return self._model

    def _headers(self) -> dict[str, str]:
        api_key = os.environ.get(self._api_key_env, "").strip()
        if not api_key:
            raise RuntimeError("NVIDIA_NIM_CREDENTIALS_MISSING")
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "strategy-validator-nvidia-nim/1.0",
        }

    def _post_json(self, body: dict[str, Any]) -> dict[str, Any]:
        encoded = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=encoded,
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_seconds) as resp:  # noqa: S310
                payload = resp.read().decode("utf-8")
        except TimeoutError:
            raise
        except urllib.error.HTTPError as exc:
            suffix = ""
            if exc.code == 429:
                ra = exc.headers.get("Retry-After") if exc.headers else None
                if ra:
                    suffix = f"|RETRY_AFTER={ra.strip()}"
            raise RuntimeError(f"NVIDIA_NIM_HTTP_{exc.code}{suffix}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"NVIDIA_NIM_URL_ERROR:{exc.reason}") from exc
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RuntimeError("NVIDIA_NIM_INVALID_JSON") from exc
        if not isinstance(data, dict):
            raise RuntimeError("NVIDIA_NIM_JSON_NOT_OBJECT")
        return data

    def _parse_completion_payload(
        self,
        raw: dict[str, Any],
        *,
        response_model: type[BaseModel] | None = None,
    ) -> tuple[dict[str, Any] | BaseModel, dict[str, Any]]:
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("NVIDIA_NIM_RESPONSE_MISSING_CHOICES")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if not isinstance(message, dict):
            raise RuntimeError("NVIDIA_NIM_RESPONSE_MISSING_MESSAGE")
        content = message.get("content")
        if isinstance(content, list):
            text = "".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in content)
        else:
            text = str(content or "").strip()
        if not text:
            raise RuntimeError("NVIDIA_NIM_RESPONSE_EMPTY_CONTENT")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("NVIDIA_NIM_RESPONSE_NON_JSON_CONTENT") from exc
        result = response_model.model_validate(parsed) if response_model is not None else parsed
        metadata = {
            "raw_response": raw,
            "response_text": text,
            "vendor_request_id": str(raw.get("id", "") or "") or None,
        }
        return result, metadata

    def complete_structured_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        response_model: type[BaseModel] | None = None,
    ) -> dict[str, Any] | BaseModel:
        result, _ = self.complete_structured_json_with_metadata(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            response_model=response_model,
        )
        return result

    def complete_structured_json_with_metadata(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        response_model: type[BaseModel] | None = None,
    ) -> tuple[dict[str, Any] | BaseModel, dict[str, Any]]:
        request_body = {
            "model": self._model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        raw = self._post_json(request_body)
        result, metadata = self._parse_completion_payload(raw, response_model=response_model)
        metadata["request_body"] = request_body
        return result, metadata

    def build_request_digest(self, *, system_prompt: str, user_prompt: str) -> str:
        return sha256(json.dumps({
            "model": self._model,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }, sort_keys=True).encode("utf-8")).hexdigest()
