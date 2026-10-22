#!/bin/bash
set -e
cd "$(dirname "$0")"
.venv/bin/python scripts/enable_kaguya_speech.py --language en
echo "English mode is ready. Close the old chat, then reopen 辉夜聊天 and start a new chat."
read -r -p "Press Enter to close..." reply
