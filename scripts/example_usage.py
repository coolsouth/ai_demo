import json
import logging
from src.api_client import APIClient
from src.config import get_config

logging.basicConfig(level=logging.INFO)

def example_post_create():
    print("\n" + "="*50)
    print("示例2: POST请求 - 创建新帖子")
    print("="*50)

    with APIClient() as client:
        try:
            new_data = {
                "model": "deepseek-v4-pro",
                "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
                ],
                "thinking": {"type": "enabled"},
                "reasoning_effort": "high",
                "stream": False
            }
            response = client.post(
                "/chat/completions",
                json=new_data
            )
            data = response.json()
            print(f"状态码: {response.status_code}")
            print(f"创建成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
        except Exception as e:
            print(f"请求失败: {e}")

if __name__ == "__main__":
    print("开始运行API调用示例...")
    example_post_create()
    print("\n" + "="*50)
    print("所有实例运行完成！")
    print("="*50)