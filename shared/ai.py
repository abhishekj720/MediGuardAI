"""Insforge AI Gateway client.

Wraps the Insforge chat completion API (POST /api/ai/chat/completion)
for use by all agents. Uses OpenRouter model identifiers.
"""

import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

INSFORGE_API_KEY = os.getenv("INSFORGE_API_KEY", "")
INSFORGE_API_BASE_URL = os.getenv("INSFORGE_API_BASE_URL", "http://localhost:7130")

DEFAULT_MODEL = "anthropic/claude-sonnet-4.6"

async def chat_completion(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """Send a chat completion request through the Insforge AI gateway.

    Returns the response content as a string.
    """
    # Read env vars at call time to support dynamic configuration
    api_key = os.getenv("INSFORGE_API_KEY", INSFORGE_API_KEY)
    base_url = os.getenv("INSFORGE_API_BASE_URL", INSFORGE_API_BASE_URL)

    payload: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "maxTokens": max_tokens,
    }
    if system_prompt:
        payload["systemPrompt"] = system_prompt

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url}/api/ai/chat/completion",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    return data.get("text", "")


async def chat_completion_json(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    system_prompt: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> dict:
    """Chat completion that parses the response as JSON.

    Uses lower temperature by default for more deterministic structured output.
    """
    content = await chat_completion(
        messages=messages,
        model=model,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Try to parse JSON directly
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    if "```json" in content:
        json_str = content.split("```json")[1].split("```")[0].strip()
        return json.loads(json_str)
    if "```" in content:
        json_str = content.split("```")[1].split("```")[0].strip()
        return json.loads(json_str)

    # Try to find JSON object between curly braces
    try:
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start:end+1])
    except json.JSONDecodeError:
        pass

    raise ValueError(f"Could not parse JSON from AI response: {content[:200]}")


async def generate_embeddings(
    inputs: list[str],
    model: str = "openai/text-embedding-3-small",
) -> list[list[float]]:
    """Generate vector embeddings via Insforge POST /api/ai/embeddings.

    Returns a list of 1536-dim float vectors, one per input string.
    Batches are handled by the caller — pass up to 20 inputs at a time.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{INSFORGE_API_BASE_URL}/api/ai/embeddings",
            headers={
                "Authorization": f"Bearer {INSFORGE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": model, "input": inputs},
        )
        response.raise_for_status()
        data = response.json()

    # Sort by index to preserve input order
    items = sorted(data["data"], key=lambda x: x["index"])
    return [item["embedding"] for item in items]
