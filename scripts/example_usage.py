"""
示例脚本：演示如何使用API客户端
"""
import json
import logging
from src.api_client import APIClient
from src.config import get_config

# 设置日志级别
logging.basicConfig(level=logging.INFO)


def example_get_posts():
    """示例：GET请求 - 获取帖子列表"""
    print("\n" + "="*50)
    print("示例1: GET请求 - 获取帖子列表")
    print("="*50)
    
    with APIClient() as client:
        try:
            # 获取帖子列表（带参数）
            response = client.get(
                "/posts",
                params={"userId": 1}
            )
            
            data = response.json()
            print(f"状态码: {response.status_code}")
            print(f"获取到 {len(data)} 条帖子")
            print(f"第一条帖子: {json.dumps(data[0], indent=2, ensure_ascii=False)}")
            
        except Exception as e:
            print(f"请求失败: {e}")


def example_post_create():
    """示例：POST请求 - 创建新帖子"""
    print("\n" + "="*50)
    print("示例2: POST请求 - 创建新帖子")
    print("="*50)
    
    with APIClient() as client:
        try:
            # 创建新帖子
            new_post = {
                "title": "使用Python requests调用API",
                "body": "这是一个使用requests库调用API的示例",
                "userId": 1
            }
            
            response = client.post(
                "/posts",
                json=new_post
            )
            
            data = response.json()
            print(f"状态码: {response.status_code}")
            print(f"创建成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
        except Exception as e:
            print(f"请求失败: {e}")


def example_put_update():
    """示例：PUT请求 - 更新帖子"""
    print("\n" + "="*50)
    print("示例3: PUT请求 - 更新帖子")
    print("="*50)
    
    with APIClient() as client:
        try:
            # 更新帖子
            updated_post = {
                "id": 1,
                "title": "更新后的标题",
                "body": "这是更新后的内容",
                "userId": 1
            }
            
            response = client.put(
                "/posts/1",
                json=updated_post
            )
            
            data = response.json()
            print(f"状态码: {response.status_code}")
            print(f"更新成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
        except Exception as e:
            print(f"请求失败: {e}")


def example_delete():
    """示例：DELETE请求 - 删除帖子"""
    print("\n" + "="*50)
    print("示例4: DELETE请求 - 删除帖子")
    print("="*50)
    
    with APIClient() as client:
        try:
            response = client.delete("/posts/1")
            print(f"状态码: {response.status_code}")
            print(f"删除成功")
            
        except Exception as e:
            print(f"请求失败: {e}")


def example_custom_headers():
    """示例：自定义请求头"""
    print("\n" + "="*50)
    print("示例5: 自定义请求头")
    print("="*50)
    
    # 创建配置实例
    config = get_config()
    
    with APIClient(config=config) as client:
        try:
            # 添加自定义请求头
            custom_headers = {
                "X-Custom-Header": "MyCustomValue",
                "Accept-Language": "zh-CN"
            }
            
            response = client.get(
                "/posts/1",
                headers=custom_headers
            )
            
            data = response.json()
            print(f"状态码: {response.status_code}")
            print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
        except Exception as e:
            print(f"请求失败: {e}")


def example_error_handling():
    """示例：错误处理"""
    print("\n" + "="*50)
    print("示例6: 错误处理")
    print("="*50)
    
    with APIClient() as client:
        try:
            # 访问不存在的端点
            response = client.get("/posts/99999")
            data = response.json()
            print(data)
            
        except Exception as e:
            print(f"请求失败（预期）: {e}")


if __name__ == "__main__":
    print("开始运行API调用示例...")
    
    # 运行所有示例
    example_get_posts()
    example_post_create()
    example_put_update()
    example_delete()
    example_custom_headers()
    example_error_handling()
    
    print("\n" + "="*50)
    print("所有示例运行完成！")
    print("="*50)