import os
import json
import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from openai import OpenAI

from src.config import get_config

logger = logging.getLogger(__name__)

class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None, config=None):
        """
        初始化DeepSeek客户端
        
        Args:
            api_key: DeepSeek API密钥，如果不提供则从配置读取
            base_url: DeepSeek API基础URL，如果不提供则从配置读取
            model: 使用的模型名称，如果不提供则从配置读取
            config: 配置对象，如果不提供则使用默认配置
        """
        self.config = get_config()
        self.api_key = api_key or self.config.DEEPSEEK_API_KEY
        self.base_url = base_url or self.config.DEEPSEEK_BASE_URL
        self.model = model or self.config.DEEPSEEK_MODEL
        
        # 初始化OpenAI客户端
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        # 对话历史
        self.conversation_history: List[Dict[str, str]] = []

        # 系统提示词
        self.system_prompt = "YOU ARE A HELPFUL ASSISTANT."
        
        logger.info(f"DeepSeek客户端初始化完成，Base URL: {self.base_url}, Model: {self.model}")
    
    def set_system_prompt(self, prompt: str):
        """设置系统提示词"""
        self.system_prompt = prompt
        logger.info(f"系统提示词已更新: {self.system_prompt[:50]}...")

    def clear_history(self):
        """清除对话历史"""
        self.conversation_history = []
        logger.info("对话历史已清除")

    def get_history(self) -> List[Dict[str, str]]:
        """获取当前对话历史"""
        return self.conversation_history.copy()
    
    def get_history_with_system(self) -> List[Dict[str, str]]:
        """获取包含系统提示词的完整对话历史"""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history)
        return messages
    
    def chat(self, user_message: str, stream: bool = False,
             reasoning_effort: Optional[str] = None,
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                extra_body: Optional[Dict] = None,
                save_to_history: bool = True
        ) -> str:
        """
        发送消息并获取回复
        
        Args:
            user_message: 用户消息
            stream: 是否流式输出
            reasoning_effort: 推理力度 (high/medium/low)，仅对deepseek-v4-pro有效
            temperature: 温度参数 (0-1)
            max_tokens: 最大输出token数
            extra_body: 额外请求参数
            save_to_history: 是否保存到对话历史
        
        Returns:
            AI回复内容
        """
        # 添加用户消息到历史
        if save_to_history:
            self.conversation_history.append({"role": "user", "content": user_message})

        # 构建请求体
        messages = self.get_history_with_system()

        #准备请求参数
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # 添加推理力度
        if reasoning_effort and self.model == "deepseek-v4-pro":
            kwargs["reasoning_effort"] = reasoning_effort

        # 添加额外参数
        if extra_body:
            kwargs["extra_body"] = extra_body

        try:
            logger.debug(f"发送消息: {user_message[:50]}..., 参数: {kwargs}")

            if stream:
                return self._handle_streaming_response(**kwargs, save_to_history=save_to_history)
            else:
                response = self.client.chat.completions.create(**kwargs)
                assistant_message = response.choices[0].message["content"]

                if save_to_history:
                    self.conversation_history.append({"role": "assistant", "content": assistant_message})
                logger.debug(f"收到回复: {assistant_message[:50]}...长度: {len(assistant_message)}字符")
                return assistant_message
        except Exception as e:
            logger.error(f"API请求失败: {str(e)}")
            raise e
    
    def _handle_streaming_response(self, **kwargs) -> str:
        """处理流式响应"""
        save_to_history = kwargs.pop("save_to_history", True)

        try:
            stream = self.client.chat.completions.create(**kwargs)
            collected_content = []

            print("\n🤖 AI: ", end="", flush=True)

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    collected_content.append(content)
                    print(content, end="", flush=True)

            print("\n")

            full_response = "".join(collected_content)

            if save_to_history:
                self.conversation_history.append({"role": "assistant", "content": full_response})
            return full_response
        except Exception as e:
            logger.error(f"处理流式响应失败: {str(e)}")
            raise

    def chat_with_context(
            self,
            user_message: str,
            context: str,
            **kwargs
    )->str:
        """
        带上下文的对话（用于接入项目文档）
        
        Args:
            user_message: 用户消息
            context: 上下文内容（如项目README）
            **kwargs: 其他参数传递给chat方法
        
        Returns:
            AI回复内容
        """
        # 临时保存原系统提示词
        original_system_prompt = self.system_prompt
        
        # 构建包含上下文的系统提示词
        context_prompt = f"""你是一个专业的项目助手。以下是一个项目的详细信息：

{context}

请根据以上项目信息回答用户的问题。如果问题与项目无关，请礼貌地说明。

当前项目信息已提供，请基于这些信息回答问题。"""
        
        self.set_system_prompt(context_prompt)

        try:
            return self.chat(user_message, **kwargs)
        finally:
            # 恢复原系统提示词
            self.set_system_prompt(original_system_prompt)

    def count_tokens(self, text:str)->int:
        return len(text) // 2  # 这是一个非常粗略的估算，实际token数可能会有所不同
    
    def get_history_summary(self)->Dict:
        """获取对话历史摘要"""
        total_meaasges = len(self.conversation_history)
        total_tokens = sum(self.count_tokens(msg["content"]) for msg in self.conversation_history)
        return {
            "total_messages": total_meaasges,
            "total_tokens": total_tokens,
            "system_prompt": self.system_prompt[:50] + "..." if self.system_prompt else "",
            "history": self.conversation_history[-5:]  # 仅返回最近5条消息
        }
    
class DeepSeekClientBuilder:
    """DeepSeek客户端构建器（支持多模型切换）"""
    
    @staticmethod
    def create_chat_client(api_key: str = None) -> DeepSeekClient:
        """创建标准对话客户端"""
        return DeepSeekClient(
            model="deepseek-chat",
            api_key=api_key
        )
    
    @staticmethod
    def create_reasoning_client(api_key: str = None) -> DeepSeekClient:
        """创建推理增强客户端（使用v4-pro）"""
        return DeepSeekClient(
            model="deepseek-v4-pro",
            api_key=api_key
        )
    
    @staticmethod
    def create_client_with_thinking(api_key: str = None) -> DeepSeekClient:
        """创建支持思考过程的客户端"""
        client = DeepSeekClient(
            model="deepseek-v4-pro",
            api_key=api_key
        )
        return client

        