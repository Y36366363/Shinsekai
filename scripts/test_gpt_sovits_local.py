"""Synthesize new Japanese lines before changing the working chat configuration."""
import argparse
import io
import json
import time
import wave
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
LINES = ['今日はどんな一日でしたか。よければ、私に聞かせてください。',
         '無理をしないでくださいね。少し休んでから、一緒に考えましょう。']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', required=True, type=Path)
    reference_text = parser.add_mutually_exclusive_group(required=True)
    reference_text.add_argument('--transcript', help='Exact Japanese words in the reference')
    reference_text.add_argument('--reference-only', action='store_true',
                                help='v2 audition without an unverified reference transcript')
    args = parser.parse_args()
    reference = args.reference.resolve(strict=True)
    output = ROOT / 'temp/gpt-sovits-audition'
    output.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.trust_env = False
    results = []
    for index, line in enumerate(LINES, 1):
        start = time.monotonic()
        response = session.post('http://127.0.0.1:9880/tts', json={
            'text': line, 'text_lang': 'ja', 'ref_audio_path': str(reference),
            'prompt_text': args.transcript or '', 'prompt_lang': 'ja',
            'text_split_method': 'cut5', 'batch_size': 1,
            'media_type': 'wav', 'streaming_mode': False,
        }, timeout=600)
        if not response.ok:
            raise RuntimeError(f'TTS HTTP {response.status_code}: {response.text[:2000]}')
        with wave.open(io.BytesIO(response.content)) as audio:
            duration = audio.getnframes() / audio.getframerate()
            if duration <= 0:
                raise RuntimeError('Empty audio')
        path = output / f'japanese-{index}.wav'
        path.write_bytes(response.content)
        result = {'text': line, 'seconds_to_generate': round(time.monotonic()-start, 2),
                  'audio_seconds': round(duration, 2), 'path': str(path),
                  'ai_generated': True, 'reference': str(reference),
                  'reference_only': args.reference_only}
        results.append(result)
        print(json.dumps(result, ensure_ascii=False))
    (output / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
