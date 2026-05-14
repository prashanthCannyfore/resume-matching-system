"""
Embedding service — Ollama nomic-embed-text (768-dim).

Critical fix: the previous version used run_coroutine_threadsafe() which
DEADLOCKS when called from within the already-running FastAPI event loop.
The fix is simple: always use `await` directly. The sync wrapper is only
kept for legacy call-sites that haven't been converted yet, and it uses
asyncio.run() which creates a NEW event loop — safe to call from sync
context only (not from inside an async function).
"""
import asyncio
import logging

from app.api.services.ollama_client import embed, embed_batch

logger = logging.getLogger(__name__)

# Dimension produced by nomic-embed-text
EMBEDDING_DIM = 768


async def generate_embedding_async(text: str) -> list[float]:
    """
    Primary embedding function — use this everywhere inside async code.
    Returns a zero vector on failure so callers don't crash, but logs the error.
    """
    if not text or not text.strip():
        logger.warning("[embedding] Empty text — returning zero vector")
        return [0.0] * EMBEDDING_DIM

    try:
        vec = await embed(text)
        if len(vec) != EMBEDDING_DIM:
            logger.error(
                f"[embedding] Unexpected dimension {len(vec)}, expected {EMBEDDING_DIM}. "
                "Check OLLAMA_EMBED_MODEL matches the FAISS index dimension."
            )
            return [0.0] * EMBEDDING_DIM
        logger.debug(f"[embedding] Generated dim={len(vec)}")
        return vec
    except Exception as e:
        logger.error(f"[embedding] Failed: {type(e).__name__}: {e}")
        return [0.0] * EMBEDDING_DIM


def generate_embedding(text: str) -> list[float]:
    """
    Sync wrapper — ONLY call this from synchronous (non-async) code.
    Do NOT call from inside an async function — use generate_embedding_async instead.
    Uses asyncio.run() which creates a fresh event loop, safe in sync context.
    """
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIM
    try:
        return asyncio.run(_embed_once(text))
    except RuntimeError as e:
        # asyncio.run() raises RuntimeError if a loop is already running
        # This means the caller is async — they should use generate_embedding_async
        logger.error(
            f"[embedding] generate_embedding() called from async context. "
            f"Use generate_embedding_async() instead. Error: {e}"
        )
        return [0.0] * EMBEDDING_DIM
    except Exception as e:
        logger.error(f"[embedding] Sync embed failed: {e}")
        return [0.0] * EMBEDDING_DIM


async def _embed_once(text: str) -> list[float]:
    return await embed(text)


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Batch embed with bounded concurrency."""
    if not texts:
        return []
    results = await embed_batch(texts)
    return [
        vec if len(vec) == EMBEDDING_DIM else [0.0] * EMBEDDING_DIM
        for vec in results
    ]
