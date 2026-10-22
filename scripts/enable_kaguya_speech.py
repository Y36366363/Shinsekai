"""Enable the auditioned local voice; back up configuration before changing it."""
import json
import shutil
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RULE = """【日常聊天与自动日语配音：覆盖上文冲突的输出要求】
每次回复仅输出 JSON：{"dialog":[{"character_name":"四宫辉夜","sprite":"01","speech":"中文台词","translate":"同一句台词的自然日语翻译"}]}。
speech 必须为简体中文，用于显示；每一个辉夜 dialog 元素都必须包含非空 translate，用自然日语完整表达对应 speech，仅用于语音合成。
translate 不得包含中文、舞台动作或解释。sprite 仍按情绪选择。不要输出 CHOICE、STAT、旁白或固定场景；不要替用户行动。
普通闲聊每次一至两条简短台词，解释问题时可以适当增加。直接回应用户，不需要介绍开场情境。
"""


def enable(root=ROOT):
    data = root / 'data'
    ref = data / 'voicepacks/kaguya-rainbow/wav/time_noon2.wav'
    if not ref.is_file():
        raise FileNotFoundError(f'缺少已试听参考音频：{ref}')
    paths = [data / 'config' / name for name in
             ('api.yaml', 'characters.yaml', 'system_config.yaml', 'template_tab_last_launch.json')]
    paths += [data / 'character_templates' / name for name in ('_temp.txt', '_temp_split.json')]
    # Parse all inputs before making changes; backups may contain secrets and stay local.
    api, characters, system = [yaml.safe_load(p.read_text()) for p in paths[:3]]
    session = json.loads(paths[3].read_text())
    meta = json.loads(paths[5].read_text())
    character = next(c for c in characters if c['name'] == '四宫辉夜')
    backup = data / 'backups' / ('before-auto-speech-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    backup.mkdir(parents=True)
    for path in paths:
        shutil.copy2(path, backup / path.name)
    api.update(tts_provider='gpt-sovits', gpt_sovits_url='http://127.0.0.1:9880/',
               gpt_sovits_api_path='', tts_split_enabled=False)
    character.update(refer_audio_path=str(ref.resolve()), prompt_text='', prompt_lang='ja',
                     gpt_model_path='', sovits_model_path='', speech_speed=1.0)
    # Preset sprite audio would bypass synthesis, so retain files but disable overrides.
    for sprite in character.get('sprites', []):
        for key in ('voice_type', 'voice_text', 'voice_path'):
            sprite.pop(key, None)
    system['voice_language'] = 'ja'
    session.update(voice_lang='ja', use_tr_yes=True, use_choice_yes=False,
                   use_narration_yes=False, use_stat_yes=False)
    for mapping, key in ((session, 'system_template_text'), (meta, 'system')):
        if RULE not in mapping.get(key, ''):
            mapping[key] = mapping.get(key, '').rstrip() + '\n\n' + RULE
    for path, value in zip(paths[:3], (api, characters, system)):
        path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding='utf-8')
    paths[3].write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding='utf-8')
    paths[5].write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    paths[4].write_text('<<<EASYAI_USER_SCENARIO>>>\n' + meta['scenario'] +
                       '\n<<<EASYAI_SYSTEM_TEMPLATE>>>\n' + meta['system'] + '\n', encoding='utf-8')
    print('已启用中文显示、日语自动配音。请关闭旧聊天并重新打开辉夜聊天。')
    print(f'原配置备份：{backup}')


if __name__ == '__main__':
    enable()
