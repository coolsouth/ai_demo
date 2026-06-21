ai_demo\
├── .env                          # DEEPSEEK_API_KEY=你的密钥
├── .gitignore
├── requirements.txt              # 包含 openai, python-dotenv 等
├── test_api.py                   # 简单测试
├── test_deepseek.py              # DeepSeek测试
├── src/
│   ├── __init__.py
│   ├── api_client.py             # 通用HTTP客户端
│   ├── config.py                 # 配置
│   └── deepseek_client.py        # DeepSeek客户端（新增）
├── scripts/
│   ├── __init__.py
│   ├── example_usage.py
│   └── chat_cli.py              # 交互式CLI（新增）
└── docs/
    └── README.md                # 示例项目文档


python环境 python3.14

运行命令cmd：

cd 项目目录

# 确保虚拟环境已激活
.venv\Scripts\activate

# 运行交互式对话程序
python -m scripts.chat_cli