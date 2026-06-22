import os
import json
import re
import logging
from typing import List, Optional, Dict, Any, Union,Generator, Tuple
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
                assistant_message = response.choices[0].message.content

                if save_to_history:
                    self.conversation_history.append({"role": "assistant", "content": assistant_message})
                logger.debug(f"收到回复: {assistant_message[:50]}...长度: {len(assistant_message)}字符")
                return assistant_message
        except Exception as e:
            logger.error(f"API请求失败: {str(e)}")
            raise e
    
    def chat_stream(
        self,
        user_message: str,
        reasoning_effort: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        extra_body: Optional[Dict] = None,
        save_to_history: bool = True,
        callback: Optional[callable] = None
    ) -> Generator[str, None, None]:
        """
        流式对话 - 生成器版本
        
        Args:
            user_message: 用户消息
            reasoning_effort: 推理力度
            temperature: 温度参数
            max_tokens: 最大输出token数
            extra_body: 额外请求参数
            save_to_history: 是否保存到历史
            callback: 每个chunk的回调函数
        
        Yields:
            每次生成的文本片段
        """
        # 先构建消息列表（包含当前用户消息）
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        # 打印调试信息
        print(f"📤 发送消息: {user_message[:50]}...")
        print(f"📚 历史消息数: {len(self.conversation_history)}")
        
        # 准备请求参数
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if reasoning_effort and self.model == "deepseek-v4-pro":
            kwargs["reasoning_effort"] = reasoning_effort

        if extra_body:
            kwargs["extra_body"] = extra_body

        
        print(f"🔧 请求参数: {kwargs}")

        try:
            stream = self.client.chat.completions.create(**kwargs)
            collected_content = []

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    collected_content.append(content)
                    if callback:
                        callback(content)
                    else:
                        yield content

            full_response = "".join(collected_content)

            if save_to_history:
                self.conversation_history.append({"role": "assistant", "content": full_response})
        except Exception as e:
            logger.error(f"流式请求失败: {str(e)}")
            raise e
        
    def chat_structured(
        self,
        user_message: str,
        schema: Dict[str, Any],
        description: str = "",
        temperature: float = 0.1,  # 结构化输出使用低温度
        max_tokens: int = 4096,
        save_to_history: bool = False
    ) -> Dict[str, Any]:
        """
        结构化输出 - 返回JSON格式
        
        Args:
            user_message: 用户消息
            schema: JSON Schema定义期望的输出结构
            description: 输出描述
            temperature: 温度（结构化输出建议使用低温度）
            max_tokens: 最大输出token数
            save_to_history: 是否保存到历史（通常不保存）
        
        Returns:
            解析后的JSON对象
        """
        # 构建更强制性的结构化提示词
        schema_json = json.dumps(schema, indent=2, ensure_ascii=False)
        # 构建结构化提示词
        system_prompt = f"""你是一个严格的数据提取助手。你的唯一任务是根据用户输入，输出符合以下JSON Schema的JSON数据。

## 输出格式要求
你必须严格按照以下JSON Schema输出，不要添加任何额外的文字、解释或Markdown标记：

```json
{schema_json}
```
重要规则（必须遵守）
只输出纯JSON，不要有任何前缀或后缀文字

不要使用Markdown代码块（不要用 json）

所有字段名必须使用双引号

字符串值使用双引号

如果某个字段没有数据，使用 null

确保JSON格式正确，可以被 json.loads() 解析

输出示例
正确的输出格式：
{{"field1": "value1", "field2": 123, "field3": ["item1", "item2"]}}

错误的输出格式（禁止）：

json{{"field1": "value1"}}

根据分析，结果是：{{"field1": "value1"}}

{description}

现在请根据用户输入，输出符合Schema的JSON数据。"""
        original_system = self.system_prompt
        try:
            self.set_system_prompt(system_prompt)
            response = self.chat(user_message, stream=False, temperature=temperature, max_tokens=max_tokens, save_to_history=save_to_history)
            logger.debug(f"原始响应: {response}")

            json_str = self._extract_json(response)
            logger.debug(f"提取的JSON字符串: {json_str}")

            if not json_str:
                json_str = response.strip()
                json_str = re.sub(r'^```json\s*', '', json_str) 
                json_str = re.sub(r'```\s*$', '', json_str)
                json_str = json_str.strip()

            # 尝试解析JSON
            try:
                parsed_response = json.loads(json_str)
                return parsed_response
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}")
            
                return self._fix_and_parse_json(json_str)
        finally:
            self.set_system_prompt(original_system)

    def _extract_json(self, text: str) -> str:
        """
        从文本中提取JSON字符串
        
        Args:
            text: 包含JSON的文本
        
        Returns:
            提取的JSON字符串
        """
        # 尝试匹配 ```json ... ``` 或 ``` ... ```
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'(\{[\s\S]*\})',
            r'(\[[\s\S]*\])'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # 如果没有匹配，尝试直接使用整个文本
        return text.strip()
    
    def _fix_and_parse_json(self, json_str: str) -> Dict[str, Any]:
        """
        尝试修复并解析JSON
        
        Args:
            json_str: 可能有问题的JSON字符串
        
        Returns:
            解析后的JSON对象
        """
        try:
            # 尝试替换单引号为双引号
            fixed = re.sub(r"'", '"', json_str)
            return json.loads(fixed)
        except:
            # 尝试更激进的修复：移除注释
            fixed = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
            fixed = re.sub(r'/\*.*?\*/', '', fixed, flags=re.DOTALL)
            try:
                return json.loads(fixed)
            except:
                # 返回错误信息
                return {
                    "error": "JSON解析失败",
                    "raw_content": json_str[:500]
                }

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

        