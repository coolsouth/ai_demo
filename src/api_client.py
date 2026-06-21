"""
API客户端：封装requests调用，支持GET/POST/PUT/DELETE
"""
import time
import logging
from typing import Optional, Dict, Any, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import get_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIClient:
    """通用API客户端"""
    
    def __init__(self, base_url: Optional[str] = None, config=None):
        """
        初始化API客户端
        
        Args:
            base_url: API基础URL，如果不提供则从配置读取
            config: 配置对象，如果不提供则使用默认配置
        """
        self.config = config or get_config()
        self.base_url = base_url or self.config.BASE_URL
        self.timeout = self.config.TIMEOUT
        
        # 创建会话
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update(self.config.HEADERS)
        
        # 添加认证（如果需要）
        if self.config.API_KEY:
            self.session.headers.update({
                "Authorization": f"Bearer {self.config.API_KEY}"
            })
        
        # 配置重试策略
        self._setup_retry()
        
        logger.info(f"API客户端初始化完成，Base URL: {self.base_url}")
    
    def _setup_retry(self):
        """配置重试策略"""
        retry_strategy = Retry(
            total=self.config.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _build_url(self, endpoint: str) -> str:
        """构建完整的URL"""
        return urljoin(self.base_url, endpoint.lstrip('/'))
    
    def _log_request(self, method: str, url: str, **kwargs):
        """记录请求日志"""
        logger.debug(f"{method} {url}")
        if kwargs.get('params'):
            logger.debug(f"Params: {kwargs['params']}")
        if kwargs.get('json'):
            logger.debug(f"JSON: {kwargs['json']}")
    
    def _log_response(self, response: requests.Response):
        """记录响应日志"""
        logger.debug(f"Response Status: {response.status_code}")
        if response.text:
            logger.debug(f"Response Body: {response.text[:500]}...")
    
    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> requests.Response:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE等)
            endpoint: API端点路径
            params: URL查询参数
            json: JSON请求体
            data: 表单数据或原始数据
            headers: 额外的请求头
            timeout: 超时时间（秒）
            **kwargs: 其他requests参数
        
        Returns:
            requests.Response对象
        
        Raises:
            requests.RequestException: 请求失败时抛出
        """
        url = self._build_url(endpoint)
        timeout = timeout or self.timeout
        
        # 合并请求头
        merged_headers = self.session.headers.copy()
        if headers:
            merged_headers.update(headers)
        
        # 记录请求
        self._log_request(method, url, params=params, json=json)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                headers=merged_headers,
                timeout=timeout,
                **kwargs
            )
            
            self._log_response(response)
            
            # 自动抛出HTTP错误
            response.raise_for_status()
            
            return response
            
        except requests.exceptions.Timeout:
            logger.error(f"请求超时: {url}")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"连接错误: {url}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP错误: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {str(e)}")
            raise
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """发送GET请求"""
        return self.request("GET", endpoint, params=params, **kwargs)
    
    def post(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        data: Optional[Any] = None,
        **kwargs
    ) -> requests.Response:
        """发送POST请求"""
        return self.request("POST", endpoint, json=json, data=data, **kwargs)
    
    def put(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        data: Optional[Any] = None,
        **kwargs
    ) -> requests.Response:
        """发送PUT请求"""
        return self.request("PUT", endpoint, json=json, data=data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """发送DELETE请求"""
        return self.request("DELETE", endpoint, **kwargs)
    
    def close(self):
        """关闭会话"""
        self.session.close()
    
    def __enter__(self):
        """支持上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时自动关闭会话"""
        self.close()