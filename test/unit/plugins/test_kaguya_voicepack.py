import json
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from plugins.kaguya_voicepack import plugin
from sdk.register import PluginCapabilityRegistry


class VoicepackTests(unittest.TestCase):
    def test_match_cooldown_silence_and_character_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'wav').mkdir()
            audio = root / 'wav/cute.wav'
            with wave.open(str(audio), 'wb') as stream:
                stream.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
                stream.writeframes(b'\x01\x00' * 24000)
            (root / 'reactions.json').write_text(json.dumps([{'keywords': ['可爱'], 'file': 'cute.wav'}]))
            output = root / 'out.wav.part'
            with patch.object(plugin, 'PACK', root):
                adapter = plugin.KaguyaVoicepackAdapter()
                adapter.generate_speech('真可爱', output, character_name='四宫辉夜')
                self.assertEqual(output.read_bytes(), audio.read_bytes())
                adapter.generate_speech('真可爱', output, character_name='四宫辉夜')
                with wave.open(str(output)) as stream:
                    self.assertEqual(stream.getnframes(), 2400)
                other = plugin.KaguyaVoicepackAdapter()
                other.generate_speech('真可爱', output, character_name='其他角色')
                self.assertNotEqual(output.read_bytes(), audio.read_bytes())
                other.generate_speech('没有匹配', output)
                self.assertNotEqual(output.read_bytes(), audio.read_bytes())

    def test_plugin_registration(self):
        registry = PluginCapabilityRegistry()
        plugin.KaguyaVoicepackPlugin().initialize(registry, Path('.'), None)
        self.assertIs(registry.tts_adapters['kaguya-voicepack'], plugin.KaguyaVoicepackAdapter)


if __name__ == '__main__':
    unittest.main()
