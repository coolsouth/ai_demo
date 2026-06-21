"""
配置文件：管理API地址、超时、重试等配置
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()


class Config:
    """基础配置"""
    
    # API基础URL
    BASE_URL = os.getenv("BASE_URL", "https://jsonplaceholder.typicode.com")
    
    # 请求超时时间（秒）
    TIMEOUT = int(os.getenv("TIMEOUT", 30))
    
    # 最大重试次数
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    
    # 请求头
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    # 如果需要认证，从环境变量读取
    API_KEY = os.getenv("API_KEY", "")
    API_SECRET = os.getenv("API_SECRET", "")

    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")  # 或 deepseek-v4-pro


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


# 根据环境变量选择配置
def get_config():
    env = os.getenv("ENV", "development")
    if env == "production":
        return ProductionConfig()
    return DevelopmentConfig()