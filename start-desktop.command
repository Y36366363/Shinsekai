#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ] || [ ! -f frontend/dist/index.html ]; then
    echo "请先运行 setup.command 完成首次安装。"
    exit 1
fi
exec .venv/bin/python scripts/desktop_window.py "$@"
