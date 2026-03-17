import os
import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL")


def get_openrouter_key():
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    return key


# openrouter.py

def generate_openrouter_reply(
    messages,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.5, # Reduced for stability
    max_tokens: int = 1000,
):
    api_key = get_openrouter_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "DEKAI",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        # 1. STOP THE LOOPING: Add stop sequences
        "stop": ["</s>", "[s]", "User:", "Assistant:", "Instruction:"],
        # 2. REPETITION PENALTY: Prevents the "hello there hello there" loop
        "frequency_penalty": 0.5, 
        "presence_penalty": 0.5,
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        
        # 3. CLEANING: If the model still leaks the prompt, cut it off
        if "[s]" in content:
            content = content.split("[s]")[0]
            
        return content.strip()
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 503:
            raise RuntimeError(
                "The AI service is temporarily unavailable. Please try again in a few moments. "
                "If the problem persists, the service may be experiencing high demand."
            )
        elif e.response.status_code == 429:
            raise RuntimeError(
                "Rate limit exceeded. Please wait a moment before trying again."
            )
        elif e.response.status_code == 401:
            raise RuntimeError(
                "Authentication failed. Please check API configuration."
            )
        else:
            raise RuntimeError(
                f"AI service error (HTTP {e.response.status_code}): {e.response.text[:200]}"
            )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            "The AI service took too long to respond. Please try again."
        )
    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Failed to connect to AI service: {str(e)}"
        )
