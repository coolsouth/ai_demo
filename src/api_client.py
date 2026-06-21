import time
import logging
from typing import Optional, Dict, Any, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIClient:
    
    def __init__(self, base_url: Optional[str] = None, config=None):
        self.config = config or get_config()
        self.base_url = base_url or self.config.BASE_URL
        self.timeout = self.config.TIMEOUT

        self.session = requests.Session()

        self.session.headers.update(self.config.HEADERS)

        if self.config.DEEPSEEK_API_KEY:
            self.session.headers.update({
                "Authorization": f"Bearer {self.config.DEEPSEEK_API_KEY}"
            })

        self._setup_retry()

        logger.info(f"API客户端初始化完成，Base URL：{self.base_url}")

    def _setup_retry(self):
        retry_strategy = Retry(
            total=self.config.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429,500,502,503,504],
            allowed_methods=["GET","POST","PUT","DELETE"]
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _build_url(self,endpoint: str)->str:
        return urljoin(self.base_url, endpoint.lstrip('/'))
    
    def _log_request(self, methods: str, url: str, **kwargs):
        logger.debug(f"{methods} {url}")
        if kwargs.get('params'):
            logger.debug(f"Params: {kwargs['params']}")
        if kwargs.get('json'):
            logger.debug(f"JSON: {kwargs['json']}")

    def _log_response(self, response: requests.Response):
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
    )-> requests.Response:
        url = self._build_url(endpoint)
        timeout = timeout or self.timeout

        merged_headers = self.session.headers.copy()
        if headers:
            merged_headers.update(headers)
        
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

            response.raise_for_status()

            return response
        
        except requests.exceptions.Timeout:
            logger.error(f"请求超时： {url}")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"连接错误：{url}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP错误：{e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败：{str(e)}")
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
        