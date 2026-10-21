#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
SOURCE_REV=b4570b876f5c086819ba84e3215472733c6a7b70
if [ ! -d runtime-services/GPT-SoVITS/.git ]; then
    git clone https://github.com/RVC-Boss/GPT-SoVITS.git runtime-services/GPT-SoVITS
    git -C runtime-services/GPT-SoVITS checkout b4570b876f5c086819ba84e3215472733c6a7b70
fi
if [ "$(git -C runtime-services/GPT-SoVITS rev-parse HEAD)" != "$SOURCE_REV" ]; then
    echo "已有 GPT-SoVITS 版本与本项目验证版本不同，请先检查；不会覆盖已有源码。"
    exit 1
fi
if [ ! -x runtime-services/gpt-sovits-env/bin/python ]; then
    python3 -m venv runtime-services/gpt-sovits-env
fi
runtime-services/gpt-sovits-env/bin/python -m pip install \
    'torch==2.7.1' 'torchaudio==2.7.1' 'resampy==0.4.3' -r runtime-services/GPT-SoVITS/requirements.txt
runtime-services/gpt-sovits-env/bin/python scripts/prepare_gpt_sovits_models.py
(
    cd runtime-services/GPT-SoVITS
    PYTHONPATH=GPT_SoVITS ../gpt-sovits-env/bin/python -c 'from text.japanese import g2p; assert g2p("こんにちは。")'
)
echo '依赖与模型准备完成。请运行 start-gpt-sovits.command 启动服务。'
