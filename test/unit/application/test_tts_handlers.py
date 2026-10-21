"""Unit tests for the application TTS handler chain."""

from unittest.mock import MagicMock

import pytest

from sdk.messages import LLMDialogMessage
from application.chat.handlers.registry import TtsMessageDispatcher
from application.chat.handlers.tts import (
    DefaultCharacterTtsHandler,
    BgmTtsHandler,
    CgTtsHandler,
    get_tts_handlers,
)


class TestDefaultCharacterTtsHandler:
    @pytest.mark.parametrize("model_path", [None, ""])
    def test_optional_model_paths_do_not_block_recorded_audio(
        self, mock_app_runtime, monkeypatch, tmp_path, model_path
    ):
        from types import SimpleNamespace
        from pathlib import Path
        from plugins.kaguya_voicepack.plugin import KaguyaVoicepackAdapter
        from plugins.kaguya_voicepack import plugin
        import json
        import wave

        (tmp_path / 'wav').mkdir()
        source = tmp_path / 'wav/test.wav'
        with wave.open(str(source), 'wb') as audio:
            audio.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
            audio.writeframes(b'\x01\x00' * 2400)
        (tmp_path / 'reactions.json').write_text(json.dumps([
            {'keywords': ['晚安'], 'file': 'test.wav'}
        ]))
        monkeypatch.setattr(plugin, 'PACK', tmp_path)
        character = SimpleNamespace(
            name='四宫辉夜', sovits_model_path=model_path, gpt_model_path=model_path,
            refer_audio_path=None, prompt_text='', prompt_lang='zh',
            sprites=[], speech_speed=1,
        )
        monkeypatch.setattr('application.chat.handlers.tts.get_character_by_name', lambda name: character)
        runtime = mock_app_runtime
        runtime.text_processor.remove_parentheses.side_effect = lambda text: text
        monkeypatch.setattr('application.chat.handlers.tts._config', runtime.config)
        runtime.config.config.api_config.tts_split_enabled = False
        runtime.tts_manager = MagicMock()
        adapter = KaguyaVoicepackAdapter()
        output = tmp_path / 'output.wav'
        runtime.tts_manager.generate_tts.side_effect = lambda text, **kw: adapter.generate_speech(text, output, **kw)
        emit = MagicMock()
        monkeypatch.setattr('application.chat.handlers.tts.tts_emit_to_ui_queue', emit)
        DefaultCharacterTtsHandler().handle(LLMDialogMessage(name='四宫辉夜', text='晚安', asset_id=None))
        runtime.tts_manager.generate_tts.assert_called_once()
        assert Path(emit.call_args.args[3]).read_bytes() == source.read_bytes()
        assert runtime.tts_manager.switch_model.call_args.args[0]['gpt_model_path'] == ''

    def test_can_handle_any_message(self, mock_app_runtime):
        """DefaultCharacterTtsHandler is the catch-all — always returns True."""
        handler = DefaultCharacterTtsHandler()
        msg = LLMDialogMessage(name="TestChar", text="Hello", asset_id="0")
        assert handler.can_handle(msg) is True

    def test_none_asset_id_uses_default_sprite_and_continues_tts(
        self, mock_app_runtime, monkeypatch
    ):
        runtime = mock_app_runtime
        runtime.tts_manager = MagicMock()
        runtime.tts_manager.generate_tts.return_value = "voice.wav"
        monkeypatch.setattr(
            "application.chat.handlers.tts._config", runtime.config
        )
        emit = MagicMock()
        monkeypatch.setattr(
            "application.chat.handlers.tts.tts_emit_to_ui_queue", emit
        )

        DefaultCharacterTtsHandler().handle(
            LLMDialogMessage(name="TestChar", text="Hello", asset_id=None)
        )

        runtime.tts_manager.generate_tts.assert_called_once()
        emit.assert_called_once_with(
            "TestChar",
            "Hello",
            "-1",
            "voice.wav",
            is_system_message=False,
            effect="",
        )


class TestSpecializedHandlers:
    def test_bgm_handler_matches_bgm(self, mock_app_runtime):
        handler = BgmTtsHandler()
        msg = LLMDialogMessage(name="BGM", text="...", asset_id="0")
        assert handler.can_handle(msg) is True

    def test_cg_handler_matches_cg(self, mock_app_runtime):
        handler = CgTtsHandler()
        msg = LLMDialogMessage(name="CG", text="...", asset_id="0")
        assert handler.can_handle(msg) is True

    def test_handler_chain_has_default_last(self):
        handlers = list(get_tts_handlers())
        assert len(handlers) > 0
        assert isinstance(handlers[-1], DefaultCharacterTtsHandler)


class TestTtsMessageDispatcher:
    def test_dispatcher_requires_at_least_one_handler(self):
        with pytest.raises(ValueError, match="至少需要一个"):
            TtsMessageDispatcher([])

    def test_dispatcher_calls_first_matching_handler(self):
        handler1 = MagicMock()
        handler1.can_handle.return_value = True
        handler2 = MagicMock()
        handler2.can_handle.return_value = True

        dispatcher = TtsMessageDispatcher([handler1, handler2])
        msg = LLMDialogMessage(name="Test", text="Hi", asset_id="0")
        dispatcher.dispatch(msg)

        handler1.pre_process.assert_called_once()
        handler1.handle.assert_called_once()
        handler1.post_process.assert_called_once()
        # handler2 should NOT be called since handler1 matched first
        handler2.handle.assert_not_called()

    def test_dispatcher_skips_non_matching(self):
        handler1 = MagicMock()
        handler1.can_handle.return_value = False
        handler2 = MagicMock()
        handler2.can_handle.return_value = True

        dispatcher = TtsMessageDispatcher([handler1, handler2])
        msg = LLMDialogMessage(name="Test", text="Hi", asset_id="0")
        dispatcher.dispatch(msg)

        handler1.handle.assert_not_called()
        handler2.handle.assert_called_once()

    def test_dispatcher_raises_when_no_handler_matches(self):
        handler = MagicMock()
        handler.can_handle.return_value = False
        dispatcher = TtsMessageDispatcher([handler])
        msg = LLMDialogMessage(name="Test", text="Hi", asset_id="0")

        with pytest.raises(RuntimeError, match="无 TTS handler 匹配"):
            dispatcher.dispatch(msg)

    def test_init_handlers_called_on_all(self):
        handler1 = MagicMock()
        handler2 = MagicMock()
        dispatcher = TtsMessageDispatcher([handler1, handler2])
        dispatcher.init_handlers()
        handler1.init.assert_called_once()
        handler2.init.assert_called_once()
