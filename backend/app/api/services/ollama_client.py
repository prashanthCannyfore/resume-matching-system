"""
Async Ollama client — production-grade with CPU-aware timeouts.

Key design decisions:
- EMBED_TIMEOUT: 30s  (nomic-embed-text is fast even on CPU)
- GEN_TIMEOUT:   90s  (per single generate call — enough for llama3.2:3b on CPU)
- No retries on generate — on CPU a retry doubles the wait time with no benefit.
  Fail fast and use the Python fallback instead.
- Retries only on connect/network errors, not on timeout.
- URLs built at call-time so .env changes are picked up without restart.
- Inline comments stripped from env values (Windows .env quirk).
"""
import asyncio
import json
import logging
from typing import Any, AsyncGenerator

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Timeouts ──────────────────────────────────────────────────────────────────
# Embed: fast even on CPU (~1-3s for nomic-embed-text)
_EMBED_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0)

# Generate: on CPU llama3.2:3b takes 30-120s per call.
# We use a single-attempt timeout — if it times out we fall back immediately
# rather than retrying (retry = double the wait = worse UX).
_GEN_READ_TIMEOUT = 90.0   # seconds — tuned for CPU inference
_GEN_TIMEOUT = httpx.Timeout(connect=5.0, read=_GEN_READ_TIMEOUT, write=10.0, pool=5.0)

_EMBED_MAX_RETRIES = 3
_EMBED_RETRY_BASE  = 1.5


def _base_url() -> str:
    """Strip inline comments from env value (Windows .env quirk)."""
    return settings.OLLAMA_BASE_URL.split("#")[0].strip().rstrip("/")


def _embed_url()    -> str: return f"{_base_url()}/api/embeddings"
def _generate_url() -> str: return f"{_base_url()}/api/generate"
def _tags_url()     -> str: return f"{_base_url()}/api/tags"


# ── Health check ──────────────────────────────────────────────────────────────
async def check_ollama_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            r = await client.get(_tags_url())
            ok = r.status_code == 200
            logger.info(f"Ollama health {_tags_url()} -> {'OK' if ok else r.status_code}")
            return ok
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        return False


async def list_models() -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            r = await client.get(_tags_url())
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
    except Exception as e:
        logger.warning(f"Could not list Ollama models: {e}")
        return []


# ── Embeddings (retry on network error, not on timeout) ───────────────────────
async def embed(text: str, model: str | None = None) -> list[float]:
    model   = model or settings.OLLAMA_EMBED_MODEL
    url     = _embed_url()
    payload = {"model": model, "prompt": text}

    last_exc: Exception | None = None
    for attempt in range(_EMBED_MAX_RETRIES):
        try:
            logger.debug(f"[embed] attempt={attempt+1} model={model} text_len={len(text)}")
            async with httpx.AsyncClient(timeout=_EMBED_TIMEOUT) as client:
                r = await client.post(url, json=payload)
                r.raise_for_status()
                embedding = r.json()["embedding"]
                logger.debug(f"[embed] OK dim={len(embedding)}")
                return embedding

        except httpx.HTTPStatusError as e:
            logger.error(f"[embed] HTTP {e.response.status_code}: {e.response.text[:200]}")
            raise

        except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError) as e:
            last_exc = e
            wait = _EMBED_RETRY_BASE ** attempt
            logger.warning(
                f"[embed] attempt {attempt+1}/{_EMBED_MAX_RETRIES} failed: "
                f"{type(e).__name__}. Retry in {wait:.1f}s"
            )
            await asyncio.sleep(wait)

        except KeyError:
            body = r.text[:300] if "r" in dir() else "no response"
            raise RuntimeError(f"Ollama embed missing 'embedding' key. Body: {body}")

    raise RuntimeError(
        f"Ollama embed failed after {_EMBED_MAX_RETRIES} attempts. "
        f"URL={url} model={model}. Last: {last_exc}"
    )


async def embed_batch(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Embed multiple texts with bounded concurrency."""
    sem = asyncio.Semaphore(settings.OLLAMA_EMBED_CONCURRENCY)

    async def _one(t: str) -> list[float]:
        async with sem:
            return await embed(t, model)

    return list(await asyncio.gather(*[_one(t) for t in texts]))


# ── Text generation ───────────────────────────────────────────────────────────
async def generate(
    prompt: str,
    model: str | None = None,
    system: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 150,          # kept small — CPU is slow
    format: str | None = None,
) -> str:
    """
    Single-attempt generate with a hard timeout.
    Does NOT retry on timeout — on CPU a retry doubles wait time.
    Raises httpx.TimeoutException on timeout so callers can fall back fast.
    """
    model   = model or settings.OLLAMA_LLM_MODEL
    url     = _generate_url()
    payload: dict[str, Any] = {
        "model":  model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature":  temperature,
            "num_predict":  max_tokens,
            "num_ctx":      2048,       # smaller context = faster on CPU
        },
    }
    if system:
        payload["system"] = system
    if format:
        payload["format"] = format

    logger.debug(
        f"[generate] model={model} prompt_len={len(prompt)} "
        f"max_tokens={max_tokens} timeout={_GEN_READ_TIMEOUT}s"
    )
    async with httpx.AsyncClient(timeout=_GEN_TIMEOUT) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        text = r.json().get("response", "").strip()
        logger.debug(f"[generate] OK response_len={len(text)}")
        return text


async def generate_json(
    prompt: str,
    model: str | None = None,
    system: str | None = None,
    temperature: float = 0.05,
    max_tokens: int = 512,
    max_json_retries: int = 2,
) -> dict:
    for attempt in range(max_json_retries):
        raw = await generate(
            prompt=prompt, model=model, system=system,
            temperature=temperature, max_tokens=max_tokens, format="json",
        )
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip()
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning(f"[generate_json] parse failed attempt {attempt+1}: {raw[:200]}")
            if attempt < max_json_retries - 1:
                prompt += "\n\nReturn ONLY valid JSON. No markdown."

    raise ValueError(f"Failed to get valid JSON after {max_json_retries} attempts")


async def generate_stream(
    prompt: str,
    model: str | None = None,
    system: str | None = None,
    temperature: float = 0.1,
) -> AsyncGenerator[str, None]:
    model   = model or settings.OLLAMA_LLM_MODEL
    url     = _generate_url()
    payload: dict[str, Any] = {
        "model": model, "prompt": prompt, "stream": True,
        "options": {"temperature": temperature, "num_ctx": 2048},
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(timeout=_GEN_TIMEOUT) as client:
        async with client.stream("POST", url, json=payload) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break
