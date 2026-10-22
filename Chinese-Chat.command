#!/bin/bash
set -e
cd "$(dirname "$0")"
.venv/bin/python scripts/enable_kaguya_speech.py --language zh
echo "已恢复中文文字、日语配音。请关闭旧聊天，重新打开辉夜聊天并开始新聊天。"
read -r -p "按回车关闭……" reply
