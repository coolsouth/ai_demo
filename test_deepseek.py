"""
测试DeepSeek API连接
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from src.deepseek_client import DeepSeekClient

def test_basic_chat():
    """测试基本对话"""
    print("="*50)
    print("测试1: 基本对话")
    print("="*50)
    
    client = DeepSeekClient()
    
    response = client.chat(
        "你好！请用中文介绍一下你自己。",
        stream=True
    )
    
    print(f"\n完整回复长度: {len(response)} 字符\n")

def test_multi_turn():
    """测试多轮对话"""
    print("="*50)
    print("测试2: 多轮对话")
    print("="*50)
    
    client = DeepSeekClient()
    
    # 第一轮
    print("👤 用户: 我叫小明")
    response = client.chat("我叫小明", stream=False)
    print(f"🤖 AI: {response[:100]}...\n")
    
    # 第二轮
    print("👤 用户: 我叫什么名字？")
    response = client.chat("我叫什么名字？", stream=False)
    print(f"🤖 AI: {response}\n")
    
    # 查看历史
    print("对话历史:")
    for msg in client.get_history():
        print(f"  {msg['role']}: {msg['content'][:50]}...")
    print()

def test_with_context():
    """测试带上下文的对话"""
    print("="*50)
    print("测试3: 带上下文的对话")
    print("="*50)
    
    client = DeepSeekClient()
    
    # 模拟项目信息
    context = """
    项目名称: MyVueApp
    技术栈: Vue 3, Vite, Pinia, Element Plus
    功能: 用户管理系统，包含登录、注册、用户列表、权限管理
    特性: 响应式设计、国际化(i18n)、暗色主题
    """
    
    response = client.chat_with_context(
        "这个项目用了什么UI框架？",
        context=context
    )
    print(f"🤖 AI: {response}\n")

if __name__ == "__main__":
    print("开始测试DeepSeek API...\n")
    
    test_basic_chat()
    test_multi_turn()
    test_with_context()
    
    print("测试完成！")