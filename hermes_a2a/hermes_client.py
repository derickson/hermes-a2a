import json
from collections.abc import AsyncIterator

import httpx


class HermesClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "hermes-agent",
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._client = httpx.AsyncClient(timeout=timeout)

    def _headers(self, session_id: str | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if session_id:
            headers["X-Hermes-Session-Id"] = session_id
        return headers

    async def complete(
        self,
        messages: list[dict],
        session_id: str | None = None,
    ) -> str:
        payload = {"model": self._model, "messages": messages, "stream": False}
        response = await self._client.post(
            f"{self._base_url}/v1/chat/completions",
            headers=self._headers(session_id),
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def stream(
        self,
        messages: list[dict],
        session_id: str | None = None,
    ) -> AsyncIterator[str]:
        payload = {"model": self._model, "messages": messages, "stream": True}
        async with self._client.stream(
            "POST",
            f"{self._base_url}/v1/chat/completions",
            headers=self._headers(session_id),
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                raw = line[len("data:"):].strip()
                if raw == "[DONE]":
                    break
                try:
                    chunk = json.loads(raw)
                    delta = chunk["choices"][0]["delta"].get("content")
                    if delta:
                        yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    async def close(self) -> None:
        await self._client.aclose()
