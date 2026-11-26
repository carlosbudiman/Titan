"""Minimal OpenAI-compatible chat client (stdlib only) + an offline mock.

Works with Ollama (/v1), vLLM, LM Studio, OpenRouter, DeepSeek, Anthropic-compatible
gateways that expose /chat/completions, etc.
"""
from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


class LLMError(RuntimeError):
    pass


@dataclass
class Reply:
    content: str = ""
    tool_calls: list[dict] | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    raw: dict | None = None

    def has_tools(self) -> bool:
        return bool(self.tool_calls)


def _post(url: str, payload: dict, headers: dict, timeout: int) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:2000]
        raise LLMError(f"HTTP {e.code} from {url}: {body}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise LLMError(f"cannot reach {url}: {e}") from e


class LLM:
    def __init__(self, base_url: str, model: str, api_key: str = "", timeout: int = 600,
                 max_tokens: int = 0, temperature: float = 0.2, retries: int = 3):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.retries = retries

    @property
    def name(self) -> str:
        return self.model or "(unset)"

    def chat(self, messages: list[dict], tools: list[dict] | None = None,
             temperature: float | None = None, max_tokens: int | None = None) -> Reply:
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature if temperature is None else temperature,
        }
        mt = self.max_tokens if max_tokens is None else max_tokens
        if mt:
            payload["max_tokens"] = mt
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        last: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                body = _post(f"{self.base_url}/chat/completions", payload, headers, self.timeout)
                return self._parse(body)
            except LLMError as e:
                last = e
                if attempt == self.retries:
                    break
                # back off on 429/5xx, fail fast on 4xx auth/schema errors
                msg = str(e)
                if any(code in msg for code in ("HTTP 401", "HTTP 403", "HTTP 404", "HTTP 400")):
                    break
                time.sleep(min(30, (2 ** attempt) + random.random()))
        raise LLMError(f"LLM call failed after retries: {last}")

    def _parse(self, body: dict) -> Reply:
        try:
            choice = body["choices"][0]
            msg = choice.get("message") or choice.get("delta") or {}
        except (KeyError, IndexError, TypeError) as e:
            raise LLMError(f"malformed completion: {json.dumps(body)[:400]}") from e

        content = msg.get("content") or ""
        if isinstance(content, list):  # some gateways return content parts
            content = "".join(p.get("text", "") for p in content if isinstance(p, dict))

        calls = []
        for i, tc in enumerate(msg.get("tool_calls") or []):
            fn = tc.get("function") or {}
            args = fn.get("arguments")
            if isinstance(args, dict):
                args = json.dumps(args)
            calls.append({"id": tc.get("id") or f"call_{i}", "name": fn.get("name") or "",
                          "arguments": args or "{}"})
        usage = body.get("usage") or {}
        return Reply(content=content, tool_calls=calls or None,
                     tokens_in=int(usage.get("prompt_tokens") or 0),
                     tokens_out=int(usage.get("completion_tokens") or 0), raw=body)


class MockLLM:
    """Deterministic provider for tests: a queue of scripted replies."""

    def __init__(self, script):
        self.script = list(script)
        self.name = "mock"
        self.calls: list[list[dict]] = []

    def chat(self, messages, tools=None, temperature=None, max_tokens=None) -> Reply:
        self.calls.append(messages)
        r = self.script.pop(0) if self.script else Reply(content="(mock exhausted)")
        if isinstance(r, dict):
            return Reply(content=r.get("content", ""), tool_calls=r.get("tool_calls"))
        return r
