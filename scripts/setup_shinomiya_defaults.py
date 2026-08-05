"""Create non-secret local defaults for the Shinomiya Kaguya setup."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "data" / "config"
API_TEMPLATE = ROOT / "config_templates" / "api.deepseek-first.yaml"
SYSTEM_TEMPLATE = ROOT / "config_templates" / "system.zh.yaml"
PLUGIN_ENTRY = "plugins.openai_standard_tts.plugin:OpenAIStandardTTSPlugin"


def read_yaml(path: Path, default):
    if not path.is_file():
        return default
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return default if value is None else value


def merge_missing(existing: dict, defaults: dict) -> dict:
    result = dict(existing)
    for key, value in defaults.items():
        if key not in result:
            result[key] = value
        elif isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_missing(result[key], value)
    return result


def write_yaml(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    api_path = CONFIG_DIR / "api.yaml"
    api_defaults = read_yaml(API_TEMPLATE, {})
    api_existing = read_yaml(api_path, {})
    api = merge_missing(api_existing, api_defaults)
    api["llm_provider"] = "Deepseek"
    api["llm_base_url"] = "https://api.deepseek.com/v1"
    api.setdefault("llm_model", {})["Deepseek"] = "deepseek-v4-flash"
    api["tts_provider"] = "openai-standard"
    env_keys = {
        "Deepseek": os.getenv("DEEPSEEK_API_KEY", "").strip(),
        "ChatGPT": os.getenv("OPENAI_API_KEY", "").strip(),
        "Gemini": os.getenv("GEMINI_API_KEY", "").strip(),
    }
    api.setdefault("llm_api_key", {})
    for provider, api_key in env_keys.items():
        if api_key:
            api["llm_api_key"][provider] = api_key
    openai_key = env_keys["ChatGPT"]
    if openai_key:
        api.setdefault("tts_extra_configs", {}).setdefault(
            "openai-standard", {}
        )["api_key"] = openai_key
    write_yaml(api_path, api)

    system_path = CONFIG_DIR / "system_config.yaml"
    system = merge_missing(read_yaml(system_path, {}), read_yaml(SYSTEM_TEMPLATE, {}))
    system["ui_language"] = "zh_CN"
    system["voice_language"] = "zh"
    write_yaml(system_path, system)

    plugins_path = CONFIG_DIR / "plugins.yaml"
    plugins = read_yaml(plugins_path, [])
    if not isinstance(plugins, list):
        raise ValueError(f"{plugins_path} must contain a YAML list")
    if not any(isinstance(item, dict) and item.get("entry") == PLUGIN_ENTRY for item in plugins):
        plugins.append({"entry": PLUGIN_ENTRY, "enabled": True})
    write_yaml(plugins_path, plugins)

    print(f"Configured DeepSeek defaults: {api_path}")
    print(f"Configured Chinese voice language: {system_path}")
    print(f"Enabled OpenAI standard TTS plugin: {plugins_path}")
    configured = [provider for provider, api_key in env_keys.items() if api_key]
    print("Synced API keys (values hidden): " + ", ".join(configured))
    print("Keys are stored only in git-ignored data/config/api.yaml.")


if __name__ == "__main__":
    main()
