import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3:8b"

def call_llm(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=600
    )
    response.raise_for_status()
    return response.json()["response"]
