from groq import Groq
import ollama as ollama_client
import logging
from config import settings

logger = logging.getLogger(__name__)

_groq_client = None


def _get_groq():
    global _groq_client
    if _groq_client is None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not set in .env")
        _groq_client = Groq(api_key=settings.groq_api_key)
    return _groq_client


# Public callers

def call_groq(prompt: str, system: str = None, max_tokens: int = 512) -> str:

    client = _get_groq()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def call_ollama(prompt: str, system: str = None, max_tokens: int = 1024) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = ollama_client.chat(
        model=settings.ollama_model,
        messages=messages,
        options={"num_predict": max_tokens, "temperature": 0.4},
    )
    return response["message"]["content"].strip()


def _groq_available() -> bool:
    key = settings.groq_api_key
    return bool(key and key != "your_groq_api_key_here" and len(key) > 20)


def call_fast(prompt: str, system: str = None) -> str:
    if _groq_available():
        try:
            return call_groq(prompt, system)
        except Exception as e:
            logger.warning(f"Groq failed: {e}. Falling back to Ollama.")
    return call_ollama(prompt, system)


def call_smart(prompt: str, system: str = None) -> str:
    try:
        return call_ollama(prompt, system)
    except Exception as e:
        logger.warning(f"Ollama failed: {e}. Falling back to Groq.")
        return call_groq(prompt, system, max_tokens=1024)