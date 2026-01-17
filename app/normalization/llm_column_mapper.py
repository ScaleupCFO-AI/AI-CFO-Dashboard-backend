import json
import os
import time
import logging
import requests
from typing import Dict, Any


# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
logger = logging.getLogger("llm.column_mapper")


# ------------------------------------------------------------
# Feature flag (HARD OFF by default)
# ------------------------------------------------------------
ENABLE_LLM_COLUMN_MAPPING = (
    os.getenv("ENABLE_LLM_COLUMN_MAPPING", "false").lower() == "true"
)


# ------------------------------------------------------------
# Ollama configuration
# ------------------------------------------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_COLUMN_MAPPING_MODEL", "llama3:8b")

REQUEST_TIMEOUT = 360  # seconds
MAX_RETRIES = 2


# ------------------------------------------------------------
# SYSTEM PROMPT (INLINE, INTENTIONAL)
# ------------------------------------------------------------
SYSTEM_PROMPT = """
You are a data normalization assistant.

Your task is to suggest mappings between raw data columns and canonical metric keys.

You will be given:
- A list of unmapped numeric column names
- A list of ambiguous column names with candidate metrics
- A list of allowed canonical metric keys

You are an ADVISORY system only.
Your suggestions will be validated by deterministic rules.
Incorrect suggestions will be rejected.

STRICT RULES (NON-NEGOTIABLE):

1. You may ONLY use canonical metric keys provided in the input.
2. You MUST NOT invent, rename, or modify metrics.
3. You MUST NOT map one raw column to multiple metrics.
4. You MUST NOT map multiple raw columns to the same metric.
5. You are NOT required to map every column.
6. If a raw column does NOT clearly and directly match any canonical metric,
   you MUST return "NO_MATCH" for that column.
7. Do NOT force mappings based on vague similarity
   (e.g. “profitability”, “performance”, “growth”).
8. Percentage, ratio, or margin columns MUST NOT be mapped
   to absolute-value metrics.
9. If you are unsure, prefer "NO_MATCH".

OUTPUT FORMAT (STRICT):

You MUST respond with VALID JSON ONLY.
The response MUST match this schema exactly:

{
  "suggestions": [
    {
      "raw_column": "<string>",
      "canonical_metric": "<metric_key>"
    }
  ]
}

If no confident mappings exist, return:
{ "suggestions": [] }

Do NOT include any text outside JSON.


Additional constraints:
- Use EXACT raw column names as provided.
- Use EXACT canonical metric keys as provided.
- Do NOT include explanations, comments, or extra fields.
- If no valid mappings exist, return an empty "suggestions" array.

"""


# ------------------------------------------------------------
# LLM COLUMN MAPPER (OLLAMA)
# ------------------------------------------------------------
def llm_column_mapper(llm_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Advisory-only LLM column mapper using Ollama.

    Guarantees:
    - JSON-only output expected
    - No validation here
    - Fail-closed behavior
    - Never blocks ingestion
    """

    if not ENABLE_LLM_COLUMN_MAPPING:
        logger.info("LLM column mapping disabled via feature flag")
        return {"suggestions": []}

    prompt = (
        SYSTEM_PROMPT.strip()
        + "\n\nINPUT:\n"
        + json.dumps(llm_input, ensure_ascii=False)
    )

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            t0 = time.time()
            logger.info(
                "LLM column-mapper call started (ollama)",
                extra={"attempt": attempt},
            )

            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0
                    }
                },
                timeout=REQUEST_TIMEOUT,
            )

            duration_ms = int((time.time() - t0) * 1000)

            logger.info(
                "LLM column-mapper call finished",
                extra={
                    "attempt": attempt,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                },
            )

            response.raise_for_status()

            raw_text = response.json().get("response", "").strip()

            # ----------------------------------------------------
            # 🔍 CRITICAL DEBUG LOG (safe, truncated)
            # ----------------------------------------------------
            logger.info(
                "LLM raw response received (truncated)",
                raw_text[:500],
            )

            # ----------------------------------------------------
            # Strict JSON parse (fail closed)
            # ----------------------------------------------------
            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError:
                logger.warning(
                    "LLM returned non-JSON output, ignoring",
                )
                return {"suggestions": []}

            # ----------------------------------------------------
            # Shape validation (contract enforcement)
            # ----------------------------------------------------
            if not isinstance(parsed, dict):
                logger.warning(
                    "LLM JSON root is not an object, ignoring",
                )
                return {"suggestions": []}

            if "suggestions" not in parsed:
                logger.warning(
                    "LLM JSON missing 'suggestions' key, ignoring",
                )
                return {"suggestions": []}

            if not isinstance(parsed["suggestions"], list):
                logger.warning(
                    "LLM 'suggestions' is not a list, ignoring",
                )
                return {"suggestions": []}

            logger.info(
                "LLM column-mapper suggestions parsed successfully",
                extra={"suggestion_count": len(parsed["suggestions"])},
            )

            return parsed

        except Exception as e:
            last_error = e
            logger.warning(
                "LLM column-mapper call failed",
                exc_info=True,
                extra={"attempt": attempt},
            )

    # --------------------------------------------------------
    # Fail closed (after retries)
    # --------------------------------------------------------
    logger.error(
        "LLM column-mapper failed after retries",
        exc_info=last_error,
    )
    return {"suggestions": []}
