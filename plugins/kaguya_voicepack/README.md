# 辉夜日语录音包接入

来源：https://github.com/Currycurrycurry/Shinomiya-Kaguya-rainbow-fart

下载版本：6036dbfe789c69150816ed4630df0097c1a5f8f9。原仓库用于 VS Code Rainbow Fart，包含 22 段 MP3，没有语音合成模型。原仓库 README 和 manifest 保留在本地下载目录，未见明确许可证；录音不随本项目提交或重新分发。

## 使用

本地已下载至 `data/voicepacks/kaguya-rainbow`。运行项目 Python 的 `scripts/setup_kaguya_voicepack.py` 可转换为 WAV 并启用插件。转换需要 ffmpeg，重新运行会保留自定义 reactions.json。

重启所有设置和聊天窗口后，「AI 服务」的语音提供商应为 `kaguya-voicepack`。日常聊天模板无需修改。默认按照辉夜回复中的“晚安”“可爱”“抱歉/对不起”“住手/别这样”等词播放相应文件，每 12 秒最多一段。中文和日文关键词都支持。没有匹配时仅显示文字，不调用收费语音接口。

这是原声反应短句，不是全文朗读或翻译；字幕继续显示 AI 回复，录音可能与回复不逐字对应。初始映射基于文件名，建议先试听确认语境。为避免随机说出不相干台词，不设置随机兜底。

打开本地 `data/voicepacks/kaguya-rainbow/试听.html` 可听全部 22 段。编辑同目录 reactions.json 可以更改触发词与 wav 文件映射，下一次回复自动读取。不要把某段录音的触发词当成逐字译文。

更换：在 AI 服务选择 none 可静音，选择 openai-standard 可恢复普通合成。初始配置备份为 data/config/api.before-voicepack.yaml 和 plugins.before-voicepack.yaml。不要把包含密钥的配置备份上传 GitHub。

固定录音包不能让角色用该声线说任意新句子，也没有被用于训练或克隆模型。
