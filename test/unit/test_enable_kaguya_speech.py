import importlib.util
import json
from pathlib import Path

import yaml

spec = importlib.util.spec_from_file_location('enable_speech', Path(__file__).resolve().parents[2] / 'scripts/enable_kaguya_speech.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_enable_preserves_settings_and_backs_up(tmp_path):
    config = tmp_path / 'data/config'
    config.mkdir(parents=True)
    templates = tmp_path / 'data/character_templates'
    templates.mkdir()
    ref = tmp_path / 'data/voicepacks/kaguya-rainbow/wav/time_noon2.wav'
    ref.parent.mkdir(parents=True)
    ref.touch()
    original = {'tts_provider': 'kaguya-voicepack', 'other_setting': 'unchanged'}
    for name, value in [('api', original), ('system_config', {'voice_language': 'zh'}),
                        ('characters', [{'name': '四宫辉夜', 'sprites': [{'path': 'sprite.png', 'voice_type': 'preset'}]}])]:
        (config / f'{name}.yaml').write_text(yaml.safe_dump(value))
    (config / 'template_tab_last_launch.json').write_text(json.dumps({'scenario_text': '日常聊天', 'system_template_text': ''}))
    (templates / '_temp_split.json').write_text(json.dumps({'scenario': '日常聊天', 'system': ''}))
    (templates / '_temp.txt').write_text('original')
    module.enable(tmp_path)
    api = yaml.safe_load((config / 'api.yaml').read_text())
    assert api['tts_provider'] == 'gpt-sovits'
    assert api['other_setting'] == 'unchanged'
    session = json.loads((config / 'template_tab_last_launch.json').read_text())
    assert session['voice_lang'] == 'ja'
    assert session['use_tr_yes'] and not session['use_choice_yes']
    backup = next((tmp_path / 'data/backups').iterdir())
    assert yaml.safe_load((backup / 'api.yaml').read_text()) == original
    module.enable(tmp_path)
    assert (templates / '_temp.txt').read_text().count(module.RULE) == 1
