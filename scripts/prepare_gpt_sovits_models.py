"""Download only the official v2 inference weights needed for the local service."""
from pathlib import Path
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    snapshot_download(
        'lj1995/GPT-SoVITS',
        revision='8f8857563c040d542de108a2c18b0425abd6c9c5',
        local_dir=ROOT / 'runtime-services/GPT-SoVITS/GPT_SoVITS/pretrained_models',
        allow_patterns=['chinese-hubert-base/*', 'chinese-roberta-wwm-ext-large/*',
                        'gsv-v2final-pretrained/*'],
        ignore_patterns=['*.onnx', '*s2D*'],
        max_workers=2,
    )
