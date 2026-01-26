import requests
import time
import logging
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


logger = logging.getLogger("llm")

def call_llm(prompt):
    t0 = time.time()
    logger.info("LLM call started")

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=600
    )

    logger.info("LLM call finished", extra={
        "duration_ms": int((time.time() - t0) * 1000)
    })

    response.raise_for_status()
    return response.json()["response"]
