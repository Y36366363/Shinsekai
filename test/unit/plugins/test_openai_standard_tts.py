from pathlib import Path
from unittest.mock import MagicMock

import pytest

from plugins.openai_standard_tts.plugin import (
    OpenAIStandardTTSAdapter,
    OpenAIStandardTTSPlugin,
)
from sdk.register import PluginCapabilityRegistry


def wav_bytes() -> bytes:
    return b"RIFF" + (4).to_bytes(4, "little") + b"WAVE" + b"data"


def test_adapter_requires_api_key():
    with pytest.raises(ValueError, match="API key is empty"):
        OpenAIStandardTTSAdapter(api_key="")


def test_adapter_writes_wav_and_clamps_speed(tmp_path):
    adapter = OpenAIStandardTTSAdapter(api_key="sk-test")
    response = MagicMock()
    response.stream_to_file.side_effect = lambda path: Path(path).write_bytes(wav_bytes())
    context = MagicMock()
    context.__enter__.return_value = response
    adapter._client = MagicMock()
    create = adapter._client.audio.speech.with_streaming_response.create
    create.return_value = context
    output = tmp_path / "speech.wav.part"

    result = adapter.generate_speech("你好", output, speed_factor=9)

    assert result == str(output.resolve())
    assert output.read_bytes() == wav_bytes()
    payload = create.call_args.kwargs
    assert payload["model"] == "gpt-4o-mini-tts"
    assert payload["voice"] == "coral"
    assert payload["response_format"] == "wav"
    assert payload["speed"] == 4.0


def test_adapter_rejects_non_wav_response(tmp_path):
    adapter = OpenAIStandardTTSAdapter(api_key="sk-test")
    response = MagicMock()
    response.stream_to_file.side_effect = lambda path: Path(path).write_bytes(b"not audio")
    context = MagicMock()
    context.__enter__.return_value = response
    adapter._client = MagicMock()
    adapter._client.audio.speech.with_streaming_response.create.return_value = context

    with pytest.raises(RuntimeError, match="valid WAV"):
        adapter.generate_speech("你好", tmp_path / "bad.wav")


def test_plugin_registers_adapter():
    registry = PluginCapabilityRegistry()
    plugin = OpenAIStandardTTSPlugin()
    plugin.initialize(registry, Path("."), MagicMock())
    assert registry.tts_adapters["openai-standard"] is OpenAIStandardTTSAdapter
