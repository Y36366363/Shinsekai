# 辉夜桌面聊天和自动朗读

1. 关闭旧聊天，在旧服务终端按 Control+C。
2. 在项目文件夹双击 `辉夜聊天.app`（保持它在项目目录内；可以为它创建桌面替身）。也可以双击 `start-desktop.command`。
3. 在独立设置窗口选择已保存的日常聊天模板，再启动聊天。聊天将在独立窗口打开。
4. 发送一句话；DeepSeek 生成回复，OpenAI 内置合成音色自动朗读。此声音为 AI 合成，并非官方角色配音，每次合成使用 OpenAI API 余额。
5. 关闭所有窗口后，本次启动的后台服务自动退出。其他已经运行的网页服务不会被关闭。

开启或修复语音：在项目终端运行 `.venv/bin/python scripts/enable_read_aloud.py`，然后重启。加 `--test` 可生成一句试听（会调用语音 API），输出在 `temp/kaguya-voice-preview.wav`。

语音在「AI 服务」选择 `openai-standard`，默认音色 coral。脚本不改日常聊天模板或 DeepSeek 设置。关闭朗读可将语音提供商切换为 none，保存并重新启动聊天。

桌面窗口复用本地网页界面，内部仍有仅绑定 127.0.0.1 的服务，不需要输入端口。它不是完全离线的软件，也暂不包含透明桌宠、口型同步或免安装发行包。

首次如被 macOS 拦截，可右键「打开」。遇到问题使用 `bash start-desktop.command` 查看提示，后台日志在 `temp/desktop.log` 和 `temp/desktop.log.errors`。不要公开完整日志或配置密钥。
