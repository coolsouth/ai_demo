---
## 🤖 AI Demo 项目结构
### 基于 DeepSeek API 的 Python 示例项目，包含模块化客户端、交互式命令行工具及完整配置。

## 📁 项目目录
```text
ai_demo/
├── .env                          # DEEPSEEK_API_KEY=你的密钥
├── .gitignore                    # Git 忽略文件
├── requirements.txt              # 依赖清单（openai, python-dotenv 等）
├── test_api.py                   # 基础 API 测试
├── test_deepseek.py              # DeepSeek 专用测试
├── src/                          # 核心源码目录
│   ├── __init__.py
│   ├── api_client.py             # 通用 HTTP 客户端封装
│   ├── config.py                 # 全局配置管理
│   └── deepseek_client.py        # DeepSeek 客户端实现（新增）
├── scripts/                      # 实用脚本目录
│   ├── __init__.py
│   ├── example_usage.py          # 功能示例
│   └── chat_cli.py               # 交互式命令行对话工具（新增）
└── docs/
    └── README.md                 # 示例项目说明文档

```
    
## 🐍 环境要求
### Python：3.14 或更高版本

## 🚀 快速开始
1. 进入项目目录
```bash
cd ai_demo
```
2. 激活虚拟环境（如已创建）
```bash
.venv\Scripts\activate
```
3. 安装依赖
```bash
pip install -r requirements.txt
```
4. 运行交互式对话程序
```bash
python -m scripts.chat_cli
```

## 📦 核心模块说明
模块	功能描述

src/api_client.py	封装通用 HTTP 请求，支持重试与日志

src/config.py	加载 .env 配置，统一管理 API 密钥等参数

src/deepseek_client.py	DeepSeek API 专用客户端，提供对话接口

scripts/chat_cli.py	交互式命令行聊天界面，支持连续对话
## 📝 备注
### 请确保在 .env 文件中正确设置 DEEPSEEK_API_KEY。
