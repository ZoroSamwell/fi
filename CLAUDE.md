# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言

永远使用中文回复用户。

## Project

B站自动回复Bot - 监听@消息并自动回复的机器人程序。

## Running

```bash
python bilibili_bot.py
```

需要配置 `config.py` 文件（参考 `config.example.py`）。

## 安全规则

**提交代码前必须检查敏感信息：**

1. 检查所有配置文件（config.py、.env等）是否包含：
   - API密钥（API_KEY、SECRET等）
   - 密码（password、passwd等）
   - Cookie、Token等认证信息
   - 个人敏感信息

2. 如果发现敏感信息：
   - 立即停止提交
   - 询问用户如何处理
   - 建议添加到 `.gitignore`

3. 已知需要排除的文件：
   - `config.py`（包含B站Cookie和AI API密钥）
   - `processed_ids.json`（运行时数据）

## Architecture

`bilibili_bot.py` - 主程序，包含：
- **消息监听**：轮询B站@通知接口
- **验重逻辑**：使用 `source_id` 作为评论ID，避免重复回复
- **AI回复**：调用mimo API生成自然回复
- **楼中楼回复**：正确回复到评论下方

`config.py` - 配置文件（不提交到git）
`config.example.py` - 配置模板
`processed_ids.json` - 已处理的评论ID（不提交到git）
