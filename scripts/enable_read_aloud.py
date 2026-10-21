"""Enable the installed speech plugin without changing conversation settings."""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import yaml
from dotenv import load_dotenv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    load_dotenv(ROOT / '.env')
    path = ROOT / 'data/config/api.yaml'
    config = yaml.safe_load(path.read_text()) or {}
    options = config.setdefault('tts_extra_configs', {}).setdefault('openai-standard', {})
    key = os.getenv('OPENAI_API_KEY') or options.get('api_key')
    if not key:
        raise SystemExit('请先在 .env 中填写 OPENAI_API_KEY。')
    options['api_key'] = key
    options.setdefault('model', 'gpt-4o-mini-tts')
    options.setdefault('voice', 'coral')
    if args.test:
        from plugins.openai_standard_tts.plugin import OpenAIStandardTTSAdapter
        adapter = OpenAIStandardTTSAdapter(**options)
        try:
            adapter.generate_speech('今天辛苦了。有什么想和我聊的吗？', str(ROOT / 'temp/kaguya-voice-preview.wav'))
        except Exception as exc:
            raise SystemExit('语音测试失败：' + type(exc).__name__) from None
        finally:
            adapter.stop_server()
        print('语音测试成功：temp/kaguya-voice-preview.wav（AI 合成声音）')
    config['tts_provider'] = 'openai-standard'
    path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False))
    path = ROOT / 'data/config/plugins.yaml'
    plugins = yaml.safe_load(path.read_text()) if path.exists() else []
    entry = 'plugins.openai_standard_tts.plugin:OpenAIStandardTTSPlugin'
    for item in plugins:
        if item.get('entry') == entry:
            item['enabled'] = True
            break
    else:
        plugins.append({'entry': entry, 'enabled': True})
    path.write_text(yaml.safe_dump(plugins, allow_unicode=True, sort_keys=False))
    print('已开启自动朗读。重启后开始新聊天生效；日常聊天设定保持不变。')


if __name__ == '__main__':
    main()
