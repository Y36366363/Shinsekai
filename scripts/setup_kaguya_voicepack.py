"""Convert an already-downloaded voice pack and enable local reactions."""
import html
import json
import shutil
import subprocess
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'data/voicepacks/kaguya-rainbow'
RULES = [
    {'keywords': ['晚安', 'おやすみ'], 'file': 'time_sleep.wav'},
    {'keywords': ['可爱', '可愛い', 'かわいい'], 'file': 'okawai.wav'},
    {'keywords': ['对不起', '抱歉', 'ごめん'], 'file': 'gome.wav'},
    {'keywords': ['别这样', '住手', 'やめて'], 'file': 'yamede.wav'},
]


def main():
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise SystemExit('找不到 ffmpeg，请安装后重试。')
    sources = sorted((PACK / 'voices').glob('*.mp3'))
    if not sources:
        raise SystemExit('请先下载语音包至 data/voicepacks/kaguya-rainbow。')
    (PACK / 'wav').mkdir(exist_ok=True)
    for source in sources:
        subprocess.run([ffmpeg, '-nostdin', '-v', 'error', '-y', '-i', str(source), '-ac', '1', '-ar', '24000', '-c:a', 'pcm_s16le', str(PACK / 'wav' / (source.stem + '.wav'))], check=True)
    rules = PACK / 'reactions.json'
    if not rules.exists():
        rules.write_text(json.dumps(RULES, ensure_ascii=False, indent=2), encoding='utf-8')
    cards = ''.join(f'<section><h3>{html.escape(p.stem)}</h3><audio controls preload="none" src="wav/{html.escape(p.stem)}.wav"></audio></section>' for p in sources)
    (PACK / '试听.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>辉夜录音试听</title><style>body{font:18px system-ui;max-width:800px;margin:40px auto;background:#fff7fa}section{padding:16px;border-bottom:1px solid #dcc}</style><h1>辉夜日语录音包 · 22 段试听</h1><p>文件名来自原仓库，未核对逐字台词。触发词表示场景匹配，不是字幕翻译。此包不是实时语音模型。</p><p><a href="https://github.com/Currycurrycurry/Shinomiya-Kaguya-rainbow-fart">来源：Currycurrycurry</a></p>' + cards + '</html>', encoding='utf-8')
    for filename in ('api.yaml', 'plugins.yaml'):
        path = ROOT / 'data/config' / filename
        backup = path.with_suffix('.before-voicepack.yaml')
        if path.exists() and not backup.exists():
            shutil.copyfile(path, backup)
    path = ROOT / 'data/config/plugins.yaml'
    plugins = yaml.safe_load(path.read_text()) or []
    entry = 'plugins.kaguya_voicepack.plugin:KaguyaVoicepackPlugin'
    for item in plugins:
        if item.get('entry') == entry:
            item['enabled'] = True
            break
    else:
        plugins.append({'entry': entry, 'enabled': True})
    path.write_text(yaml.safe_dump(plugins, allow_unicode=True, sort_keys=False))
    path = ROOT / 'data/config/api.yaml'
    api = yaml.safe_load(path.read_text())
    api['tts_provider'] = 'kaguya-voicepack'
    api['tts_split_enabled'] = False
    path.write_text(yaml.safe_dump(api, allow_unicode=True, sort_keys=False))
    print(f'已转换 {len(sources)} 段录音并启用 kaguya-voicepack。请重启聊天。')
    print('试听页：' + str(PACK / '试听.html'))


if __name__ == '__main__':
    main()
