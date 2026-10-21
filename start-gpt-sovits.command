#!/bin/bash
set -euo pipefail
trap 'status=$?; if [ "$status" -ne 0 ]; then echo "语音服务启动失败，请保留上方错误信息。"; if [ -t 0 ]; then read -r -p "按回车关闭……" reply; fi; fi' EXIT
cd "$(dirname "$0")"
PROJECT_DIR="$PWD"
export PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
if [ ! -x runtime-services/gpt-sovits-env/bin/python ]; then
    echo "尚未安装语音服务，请先运行 bash scripts/install_gpt_sovits.sh"
    exit 1
fi
if curl --noproxy '*' --silent --fail --max-time 3 http://127.0.0.1:9880/openapi.json | grep -q '"/tts"'; then
    echo "语音服务已在运行，无需重复启动：http://127.0.0.1:9880/docs"
    exit 0
fi
echo "正在载入语音模型，首次启动可能需要几分钟。请保持此窗口打开。"
cd runtime-services/GPT-SoVITS
"$PROJECT_DIR/runtime-services/gpt-sovits-env/bin/python" -u api_v2.py -a 127.0.0.1 -p 9880 -c "$PROJECT_DIR/config_templates/gpt-sovits-mac.yaml"
