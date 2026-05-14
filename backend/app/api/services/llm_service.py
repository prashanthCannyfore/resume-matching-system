# app/api/services/llm_service.py
import subprocess
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def call_ollama(prompt: str, model: str = None) -> str:
    model = model or settings.OLLAMA_MODEL or "mistral"
    ollama_bin = settings.OLLAMA_PATH or "ollama"

    try:
        result = subprocess.run(
            [ollama_bin, "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=90,          # 1.5 minutes
            check=True
        )
        return result.stdout.strip()
    except FileNotFoundError:
        logger.error("Ollama not found. Make sure Ollama is running.")
        raise RuntimeError("Ollama is not installed or not running")
    except subprocess.TimeoutExpired:
        logger.error("Ollama request timed out")
        raise RuntimeError("Ollama timed out - try a smaller model")
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        raise