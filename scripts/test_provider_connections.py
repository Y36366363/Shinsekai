"""Safely smoke-test configured LLM/TTS API credentials from ``.env``.

The script never prints credential values. Requests are intentionally tiny.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def clean_error(exc: BaseException, secrets: list[str]) -> str:
    message = str(exc).replace("\n", " ").strip()
    for secret in secrets:
        if secret:
            message = message.replace(secret, "***")
    return message[:500]


def model_ids(client: OpenAI) -> list[str]:
    return sorted(str(item.id) for item in client.models.list().data)


def tiny_chat(client: OpenAI, model: str, provider: str) -> str:
    request = {
        "model": model,
        "messages": [{"role": "user", "content": "只回复 OK"}],
        "max_tokens": 64 if provider == "DeepSeek" else 8,
        "temperature": 0,
    }
    if provider == "DeepSeek":
        request["extra_body"] = {"thinking": {"type": "disabled"}}
    response = client.chat.completions.create(
        **request,
    )
    reply = str(response.choices[0].message.content or "").strip()
    if not reply:
        raise RuntimeError("Chat request succeeded but returned empty text")
    return reply


def choose_model(available: list[str], preferred: list[str], predicate: Callable[[str], bool]) -> str:
    normalized = {item.removeprefix("models/"): item for item in available}
    for candidate in preferred:
        if candidate in normalized:
            return normalized[candidate]
    for item in available:
        if predicate(item.lower()):
            return item
    raise RuntimeError("No suitable text chat model found")


def main() -> int:
    load_dotenv(ENV_PATH, override=False)
    keys = {
        "deepseek": os.getenv("DEEPSEEK_API_KEY", "").strip(),
        "openai": os.getenv("OPENAI_API_KEY", "").strip(),
        "gemini": os.getenv("GEMINI_API_KEY", "").strip(),
    }
    secrets = list(keys.values())
    results: list[dict] = []

    providers = [
        (
            "DeepSeek",
            None,
            lambda: OpenAI(api_key=keys["deepseek"], base_url="https://api.deepseek.com/v1"),
        ),
        (
            "OpenAI",
            None,
            lambda: OpenAI(api_key=keys["openai"], base_url="https://api.openai.com/v1"),
        ),
        (
            "Gemini",
            None,
            lambda: OpenAI(
                api_key=keys["gemini"],
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
        ),
    ]

    for provider, fixed_model, factory in providers:
        started = time.monotonic()
        try:
            if not keys[provider.lower()]:
                raise RuntimeError("API key is missing")
            client = factory()
            available = model_ids(client)
            if fixed_model:
                model = fixed_model
                if model not in {item.removeprefix("models/") for item in available}:
                    raise RuntimeError(f"Configured model is unavailable: {model}")
            elif provider == "DeepSeek":
                model = choose_model(
                    available,
                    ["deepseek-v4-flash", "deepseek-chat", "deepseek-v4-pro"],
                    lambda item: "deepseek" in item and "flash" in item,
                )
            elif provider == "OpenAI":
                model = choose_model(
                    available,
                    ["gpt-4o-mini", "gpt-4.1-mini"],
                    lambda item: item.startswith("gpt-") and "audio" not in item and "realtime" not in item,
                )
            else:
                model = choose_model(
                    available,
                    [
                        "gemini-3.5-flash-lite",
                        "gemini-3.6-flash",
                        "gemini-3.5-flash",
                        "gemini-flash-lite-latest",
                        "gemini-3.1-flash-lite",
                    ],
                    lambda item: "gemini" in item and "flash" in item and not any(
                        token in item for token in ("image", "tts", "live", "audio")
                    ),
                )
            reply = tiny_chat(client, model.removeprefix("models/"), provider)
            results.append(
                {
                    "provider": provider,
                    "status": "ok",
                    "model": model,
                    "reply": reply,
                    "model_count": len(available),
                    "elapsed_seconds": round(time.monotonic() - started, 2),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "provider": provider,
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error": clean_error(exc, secrets),
                    "elapsed_seconds": round(time.monotonic() - started, 2),
                }
            )

    started = time.monotonic()
    try:
        from plugins.openai_standard_tts.plugin import OpenAIStandardTTSAdapter

        adapter = OpenAIStandardTTSAdapter(api_key=keys["openai"])
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "smoke-test.wav"
            result = adapter.generate_speech("你好，这是语音连接测试。", output, speed_factor=0.96)
            size = Path(result).stat().st_size if result else 0
            if size <= 44:
                raise RuntimeError("Generated WAV was empty")
        adapter.stop_server()
        results.append(
            {
                "provider": "OpenAI TTS",
                "status": "ok",
                "model": "gpt-4o-mini-tts",
                "voice": "coral",
                "format": "wav",
                "audio_bytes": size,
                "elapsed_seconds": round(time.monotonic() - started, 2),
            }
        )
    except Exception as exc:
        results.append(
            {
                "provider": "OpenAI TTS",
                "status": "error",
                "error_type": type(exc).__name__,
                "error": clean_error(exc, secrets),
                "elapsed_seconds": round(time.monotonic() - started, 2),
            }
        )

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(item["status"] == "ok" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
