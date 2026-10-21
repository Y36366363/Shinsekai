"""Play keyword-matched recordings, not synthesized or translated dialogue."""
import json
import shutil
import time
import wave
from pathlib import Path

from sdk.adapters.tts import TTSAdapter
from sdk.plugin import PluginBase

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / 'data/voicepacks/kaguya-rainbow'


class KaguyaVoicepackAdapter(TTSAdapter):
    requires_reference_audio = False

    def __init__(self, **kwargs):
        self.last_played = float('-inf')

    def generate_speech(self, text, file_path=None, **kwargs):
        output = Path(file_path or ROOT / 'temp/kaguya-reaction.wav')
        output.parent.mkdir(parents=True, exist_ok=True)
        rules = json.loads((PACK / 'reactions.json').read_text(encoding='utf-8'))
        chosen = None
        name = kwargs.get('character_name')
        if name in (None, '四宫辉夜') and time.monotonic() - self.last_played >= 12:
            for rule in rules:
                if any(word in str(text) for word in rule['keywords']):
                    candidate = (PACK / 'wav' / rule['file']).resolve()
                    if candidate.parent == (PACK / 'wav').resolve() and candidate.is_file():
                        chosen = candidate
                        break
        if chosen:
            shutil.copyfile(chosen, output)
            self.last_played = time.monotonic()
        else:
            # Valid short silence avoids the manager's retry/failure path.
            with wave.open(str(output), 'wb') as stream:
                stream.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
                stream.writeframes(b'\x00\x00' * 2400)
        return str(output.resolve())

    def switch_model(self, model_info):
        return None

    def stop_server(self):
        return None


class KaguyaVoicepackPlugin(PluginBase):
    @property
    def plugin_id(self):
        return 'local.kaguya_voicepack'

    @property
    def plugin_name(self):
        return '辉夜日语录音包（关键词短句，非全文朗读）'

    @property
    def plugin_version(self):
        return '0.1.0'

    @property
    def plugin_description(self):
        return '匹配回复关键词播放本地录音；未匹配时静音。不生成新语音。'

    def initialize(self, register, plugin_root, host):
        register.register_tts_adapter('kaguya-voicepack', KaguyaVoicepackAdapter)


Plugin = KaguyaVoicepackPlugin
