"""OpenAI standard text-to-speech adapter.

This adapter intentionally uses a built-in synthetic voice. It does not clone,
imitate, or consume a character reference recording.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openai import OpenAI

from sdk.adapters.tts import TTSAdapter
from sdk.plugin import PluginBase
from sdk.plugin_host_context import PluginHostContext
from sdk.register import PluginCapabilityRegistry


class OpenAIStandardTTSAdapter(TTSAdapter):
    """Synthesize WAV audio through ``POST /v1/audio/speech``."""

    requires_reference_audio = False

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini-tts",
        voice: str = "coral",
        instructions: str = "请用自然、清晰、优雅而克制的年轻女性中文语气朗读。不要模仿任何真实人物或声优。",
        timeout_seconds: float = 120.0,
        **_ignored: Any,
    ) -> None:
        self.api_key = str(api_key or "").strip()
        self.base_url = str(base_url or "https://api.openai.com/v1").strip().rstrip("/")
        self.model = str(model or "gpt-4o-mini-tts").strip()
        self.voice = str(voice or "coral").strip()
        self.instructions = str(instructions or "").strip()
        self.timeout_seconds = max(10.0, float(timeout_seconds or 120.0))

        if not self.api_key:
            raise ValueError("OpenAI standard TTS API key is empty")
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @classmethod
    def get_config_schema(cls) -> dict[str, dict]:
        return {
            "api_key": {
                "label": "OpenAI TTS API Key",
                "description": "仅用于语音合成，不会写入角色包。",
                "default": "",
                "secret": True,
                "type": "str",
            },
            "base_url": {
                "label": "OpenAI TTS Base URL",
                "default": "https://api.openai.com/v1",
                "type": "str",
            },
            "model": {
                "label": "语音模型",
                "default": "gpt-4o-mini-tts",
                "type": "str",
            },
            "voice": {
                "label": "内置音色",
                "description": "初版建议 coral；可在 OpenAI.fm 试听后更换。",
                "default": "coral",
                "type": "str",
            },
            "instructions": {
                "label": "说话风格",
                "default": "请用自然、清晰、优雅而克制的年轻女性中文语气朗读。不要模仿任何真实人物或声优。",
                "type": "str",
            },
            "timeout_seconds": {
                "label": "请求超时（秒）",
                "default": 120,
                "min": 10,
                "max": 300,
                "type": "int",
            },
        }

    def generate_speech(self, text, file_path=None, **kwargs):
        clean_text = str(text or "").strip()
        if not clean_text:
            return None

        output = Path(file_path or "temp/openai_standard_tts.wav").resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            speed = float(kwargs.get("speed_factor") or 1.0)
        except (TypeError, ValueError):
            speed = 1.0
        speed = min(4.0, max(0.25, speed))

        payload: dict[str, Any] = {
            "model": self.model,
            "voice": self.voice,
            "input": clean_text,
            "response_format": "wav",
            "speed": speed,
        }
        if self.instructions and not self.model.startswith("tts-1"):
            payload["instructions"] = self.instructions

        with self._client.audio.speech.with_streaming_response.create(
            **payload,
            timeout=self.timeout_seconds,
        ) as response:
            response.stream_to_file(output)

        audio_header = output.read_bytes()[:12] if output.is_file() else b""
        if (
            len(audio_header) < 12
            or not audio_header.startswith(b"RIFF")
            or audio_header[8:12] != b"WAVE"
        ):
            output.unlink(missing_ok=True)
            raise RuntimeError("OpenAI TTS response was not a valid WAV file")
        return str(output)

    def switch_model(self, model_info):
        # Built-in preset voices are independent of the active character.
        return None

    def stop_server(self) -> None:
        self._client.close()


class OpenAIStandardTTSPlugin(PluginBase):
    @property
    def plugin_id(self) -> str:
        return "local.openai_standard_tts"

    @property
    def plugin_version(self) -> str:
        return "0.1.0"

    @property
    def plugin_name(self) -> str:
        return "OpenAI Standard TTS"

    @property
    def plugin_description(self) -> str:
        return "使用 OpenAI 内置合成音色朗读角色对白，不需要参考音频或声音克隆。"

    def initialize(
        self,
        register: PluginCapabilityRegistry,
        plugin_root: Path,
        host: PluginHostContext,
    ) -> None:
        _ = plugin_root, host
        register.register_tts_adapter("openai-standard", OpenAIStandardTTSAdapter)


Plugin = OpenAIStandardTTSPlugin
