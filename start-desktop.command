#!/bin/bash
set -e
trap 'code=$?; if [ "$code" -ne 0 ]; then echo "启动失败，请把上方错误发给我。按回车关闭。"; read -r reply; fi' EXIT
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ] || [ ! -f frontend/dist/index.html ]; then
    echo "请先运行 setup.command 完成首次安装。"
    exit 1
fi
exec .venv/bin/python scripts/desktop_window.py "$@"
