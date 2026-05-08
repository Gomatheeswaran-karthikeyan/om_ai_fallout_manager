from __future__ import annotations
import json
import re
import httpx

from app.config.settings import settings
from app.models.response_model import AISuggestion


async def get_ai_suggestion(prompt: str) -> AISuggestion:
    provider = settings.llm_provider.lower()
    if provider == "anthropic":
        raw = await _call_anthropic(prompt)
    elif provider == "groq":
        raw = await _call_groq(prompt)
    elif provider == "gemini":
        raw = await _call_gemini(prompt)
    elif provider == "ollama":
        raw = await _call_ollama(prompt)
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: '{provider}'")

    return _parse_suggestion(raw)


def _parse_suggestion(raw: str) -> AISuggestion:
    # Strip markdown code fences if the model wrapped the JSON
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: wrap the raw text so the response still has structure
        return AISuggestion(
            # root_cause=raw.strip(),
            resolution_steps=["See root_cause field for full details."],
            # escalation="Unable to parse structured response.",
            # prevention="Unable to parse structured response.",
        )

    steps = data.get("resolution_steps", [])
    if isinstance(steps, str):
        steps = [s.strip() for s in steps.splitlines() if s.strip()]
    elif isinstance(steps, list):
        # Flatten if items are dicts e.g. [{"step": "..."}, ...]
        steps = [
            v if isinstance(v, str) else " ".join(str(x) for x in v.values())
            for v in steps
        ]

    return AISuggestion(
        # root_cause=_to_str(data.get("root_cause", "")),
        resolution_steps=steps,
        # escalation=_to_str(data.get("escalation", "")),
        # prevention=_to_str(data.get("prevention", "")),
    )


def _to_str(value) -> str:
    """Coerce any LLM value (string, list of strings/dicts) to a plain string."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(" ".join(str(v) for v in item.values()))
            else:
                parts.append(str(item))
        return " ".join(parts)
    return str(value)


# ── Anthropic ─────────────────────────────────────────────────────────────────

async def _call_anthropic(prompt: str) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    msg = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=settings.llm_max_tokens,
        system=_system_prompt(),
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


# ── Groq (OpenAI-compatible, free tier) ───────────────────────────────────────

async def _call_groq(prompt: str) -> str:

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": settings.groq_model,
        "messages": [
            {
                "role": "system",
                "content": _system_prompt()
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    async with httpx.AsyncClient(
            timeout=60.0,
            verify=False   # TEMP FIX
    ) as client:

        response = await client.post(
            url,
            headers=headers,
            json=payload
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]


# ── Google Gemini (free tier) ─────────────────────────────────────────────────

async def _call_gemini(prompt: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        system_instruction=_system_prompt(),
    )
    response = await model.generate_content_async(prompt)
    return response.text


# ── Ollama (local, fully free) ────────────────────────────────────────────────

async def _call_ollama(prompt: str) -> str:
    import httpx
    # Use Ollama native API directly to support keep_alive
    payload = {
        "model": settings.ollama_model,
        "prompt": f"{_system_prompt()}\n\n{prompt}",
        "stream": False,
        "keep_alive": -1,           # keep model in RAM indefinitely
        "options": {"num_predict": settings.llm_max_tokens},
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{settings.ollama_base_url}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json()["response"]


def _system_prompt() -> str:
    return (
        "You are a senior Order Management Analyst at Brightspeed telecom. "
        "Always respond with valid JSON only. No markdown, no extra explanation."
    )
