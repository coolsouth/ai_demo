"""
AI工具包 - 整合所有功能
包含：API客户端、多轮对话、流式输出、结构化输出、代码审查
"""
import os
import json
import logging
import re
                
from typing import Optional,Dict,List,Any,Generator,Callable,Union
from datetime import datetime

from openai import OpenAI

from src.config import get_config

logger = logging.getLogger(__name__)

class AIToolkit:
    """
    完整的AI工具包
    整合了DeepSeek API的所有功能
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        config=None
    ):
        """
        初始化AI工具包
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
            config: 配置对象
        """

        self.config = config or get_config()
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("请设置DEEPSEEK_API_KEY环境变量")
        
        self.base_url = base_url or os.environ.get("DEEPSEEK_BASE_URL","https://api.deepseek.com")
        self.model = model or os.environ.get("DEEPSEEK_MODEL","deepseek-chat")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = "You are a helpful assistant."

        self.context = ""
        self.context_file = None

        logger.info(f"AI工具包初始化成功，模型: {self.model}")
    
    # ============ 对话管理 ============
    
    def set_system_prompt(self, system_prompt: str):
        """设置系统提示词"""
        self.system_prompt = system_prompt
        logger.info("系统提示词已更新")
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        logger.info("对话历史已清空")
    
    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history.copy()
    
    def get_history_summary(self) -> Dict:
        """获取对话历史摘要"""
        total_messages = len(self.conversation_history)
        total_tokens = sum(len(msg['content']) // 2 for msg in self.conversation_history)
        
        return {
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "system_prompt": self.system_prompt[:100] + "..." if len(self.system_prompt) > 100 else self.system_prompt,
            "history": self.conversation_history[-5:] if total_messages > 5 else self.conversation_history
        }
    
    # ============ 核心对话功能 ============

    def _build_messages(self, user_message: str) -> List[Dict[str, str]]:
        """构建消息列表"""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role":"user","content":user_message})
        return messages
    
    def chat(
        self,
        user_message: str,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        reasoning_effort: Optional[str] = None,
        extra_body: Optional[Dict] = None,
        save_to_history: bool = True
    ) -> Union[str, Generator]:
        """
        对话接口
        
        Args:
            user_message: 用户消息
            stream: 是否流式输出
            temperature: 温度参数
            max_tokens: 最大输出token数
            reasoning_effort: 推理力度 (仅deepseek-v4-pro)
            extra_body: 额外参数
            save_to_history: 是否保存到历史
        
        Returns:
            字符串或生成器
        """
        messages = self._build_messages(user_message)
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if reasoning_effort and self.model == "deepseek-v4-pro":
            kwargs["reasoning_effort"] = reasoning_effort
        if extra_body:
            kwargs["extra_body"] = extra_body

        try:
            if stream:
                return self._chat_stream(
                    user_message=user_message,
                    save_to_history=save_to_history,
                    **kwargs
                )
            else:
                return self._chat_sync(
                    user_message=user_message,
                    save_to_history=save_to_history,
                    **kwargs
                )
        except Exception as e:
            logger.error(f"对话失败: {str(e)}")
            raise

    def _chat_sync(
        self,
        user_message: str,
        save_to_history: bool,
        **kwargs
    ) -> str:
        """同步对话"""
        # 移除 stream 参数（如果有）
        kwargs.pop('stream', None)
        
        response = self.client.chat.completions.create(**kwargs)
        assistant_message = response.choices[0].message.content
        
        if save_to_history:
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message
    
    def _chat_stream(
        self,
        user_message: str,
        save_to_history: bool,
        **kwargs
    ) -> Generator[str, None, None]:
        """流式对话"""
        # 移除 stream 参数（如果有），因为我们要手动控制
        kwargs.pop('stream', None)
        
        # 创建流式请求
        stream_response = self.client.chat.completions.create(
            **kwargs,
            stream=True  # 显式启用流式
        )
        collected_content = []
        
        for chunk in stream_response:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                collected_content.append(content)
                yield content
        
        full_response = "".join(collected_content)
        
        if save_to_history:
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": full_response})

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
            import re
            # 提取JSON
            patterns = [
                r'```json\s*([\s\S]*?)\s*```',
                r'```\s*([\s\S]*?)\s*```',
                r'(\{[\s\S]*\})',
                r'(\[[\s\S]*\])'
            ]
            
            json_str = response.strip()
            for pattern in patterns:
                match = re.search(pattern, response)
                if match:
                    json_str = match.group(1).strip()
                    break
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # 尝试修复
                fixed = re.sub(r"'", '"', json_str)
                return json.loads(fixed)
        finally:
            self.set_system_prompt(original_system)

    # ============ 上下文管理 ============
    
    def set_context(self, context: str, source: str = "manual"):
        """
        设置上下文
        
        Args:
            context: 上下文内容
            source: 来源描述
        """
        self.context = context
        self.context_file = source
        self.system_prompt = f"""你是一个专业的AI助手。以下是提供的上下文信息：

{context}

请根据以上信息回答用户的问题。如果问题与上下文无关，请礼貌地说明。"""
        logger.info(f"上下文已更新，来源: {source}")

    def set_context_from_file(self, file_path: str):
        """
        从文件加载上下文
        
        Args:
            file_path: 文件路径
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            context = f.read()
        
        self.set_context(context, source=file_path)
        self.context_file = file_path

    # ============ 代码审查 ============
    
    def review_code(
        self,
        code: str,
        file_name: str = "unknown.js",
        framework: str = "Vue 3",
        stream: bool = False,
        on_chunk: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        代码审查
        
        Args:
            code: 要审查的代码
            file_name: 文件名
            framework: 框架名称
            stream: 是否流式输出
            on_chunk: 流式输出回调
        
        Returns:
            审查报告JSON
        """
        schema = {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "object",
                    "properties": {
                        "total_issues": {"type": "integer"},
                        "critical_count": {"type": "integer"},
                        "major_count": {"type": "integer"},
                        "minor_count": {"type": "integer"},
                        "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
                        "overall_assessment": {"type": "string"}
                    },
                    "required": ["total_issues", "critical_count", "major_count", "minor_count", "overall_score", "overall_assessment"]
                },
                "issues": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "severity": {"type": "string", "enum": ["critical", "major", "minor", "suggestion"]},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "line_numbers": {"type": "array", "items": {"type": "integer"}},
                            "code_snippet": {"type": "string"},
                            "suggestion": {"type": "string"},
                            "reference": {"type": "string"}
                        },
                        "required": ["id", "severity", "title", "description", "suggestion"]
                    }
                },
                "best_practices": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "practice": {"type": "string"},
                            "description": {"type": "string"},
                            "benefit": {"type": "string"}
                        },
                        "required": ["practice", "description"]
                    }
                },
                "improvement_suggestions": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["summary", "issues"]
        }

        prompt = f"""请对以下 {framework} 代码进行全面的代码审查，按照指定的JSON格式输出结果。

文件名: {file_name}
框架: {framework}

代码内容:
```{file_name.split('.')[-1] if '.' in file_name else 'javascript'}
{code}
```
请重点检查：

代码质量：命名规范、重复代码、复杂度

性能问题：性能瓶颈、内存泄漏风险

安全性：XSS漏洞、敏感信息泄露

可维护性：代码可读性、注释

框架特定：是否符合{framework}最佳实践

请输出结构化的JSON报告。"""
        
        original_system = self.system_prompt
        try:
            self.set_system_prompt("你是一个专业的代码审查专家，擅长发现代码问题并提供改进建议。")
            if stream:
                print("\n🤖 AI正在审查代码...\n")
                print("-" * 60)

                response = ""
                for chunk in self.chat(
                    user_message=prompt,
                    stream=True,
                    temperature=0.1,
                    save_to_history=False
                ):
                    response += chunk
                    if on_chunk:
                        on_chunk(chunk)
                    else:
                        print(chunk, end="", flush=True)
                print("\n" + "-" * 60)
                print("✅ 审查完成，正在解析结果...\n")

                patterns = [
                r'json\s*([\s\S]*?)\s*',
                r'\s*([\s\S]*?)\s*',
                r'({[\s\S]*})'
                ]

                json_str = response.strip()
                for pattern in patterns:
                    match = re.search(pattern, response)
                    if match:
                        json_str = match.group(1).strip()
                        break

                    try:
                        return json.loads(json_str)
                    except:
                        return {"error": "JSON解析失败", "raw": response[:500]}
            else:
                response = self.chat(
                user_message=prompt,
                temperature=0.1,
                save_to_history=False,
                stream=False
                )
                return json.loads(response)

        finally:
            self.set_system_prompt(original_system)

    def format_review_report(self, report: Dict[str, Any]) -> str:
        """格式化审查报告为可读文本"""
        if "error" in report:
            return f"❌ 审查失败: {report['error']}"
        lines = []
        lines.append("="*60)
        lines.append(f"📊 代码审查报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("="*60)

        #摘要
        summary = report.get("summary", {})
        lines.append(f"\n📊 审查摘要:")
        lines.append(f" ├─ 总问题数: {summary.get('total_issues', 0)}")
        lines.append(f" ├─ 🔴 严重: {summary.get('critical_count', 0)}")
        lines.append(f" ├─ 🟡 主要: {summary.get('major_count', 0)}")
        lines.append(f" ├─ 🟢 次要: {summary.get('minor_count', 0)}")
        lines.append(f" ├─ 📈 综合评分: {summary.get('overall_score', 0)}/100")
        lines.append(f" └─ 📝 总体评价: {summary.get('overall_assessment', 'N/A')}")

        #问题详情
        issues = report.get("issues", [])
        if issues:
            lines.append(f"\n🐞 发现问题:")
            for i,issue in enumerate(issues,1):
                severity = issue.get("severity", "unknown")
                emoji = {"critical": "🔴", "major": "🟡", "minor": "🟢", "suggestion": "💡"}.get(severity, "⚪")
                lines.append(f" {i}. {emoji} [{severity.upper()}] {issue.get('title', '无标题')}")
                lines.append(f"    描述: {issue.get('description', '无描述')}")

                line_nums = issue.get("line_numbers", [])
                if line_nums:
                    lines.append(f"    位置: 行 {', '.join(map(str, line_nums))}")
                code_snippet = issue.get("code_snippet", "")
                if code_snippet:
                    lines.append(f"    代码片段: {code_snippet}")
                suggestion = issue.get("suggestion", "")
                if suggestion:
                    lines.append(f"    修复建议: {suggestion}") 
                reference = issue.get("reference", "")
                if reference:
                    lines.append(f"    参考链接: {reference}")

        #最佳实践
        best_practices = report.get("best_practices", [])
        if best_practices:
            lines.append(f"\n🌟 最佳实践建议{len(best_practices)}个:")
            for practice in best_practices:
                lines.append(f" - {practice.get('practice', '无标题')}: {practice.get('description', '')} (好处: {practice.get('benefit', '')})")
                description = practice.get("description", "")
                if description:
                    lines.append(f"    描述: {description}")
        #改进建议
        improvement_suggestions = report.get("improvement_suggestions", [])
        if improvement_suggestions:
            lines.append(f"\n💡 其他改进建议:")
            for suggestion in improvement_suggestions:
                lines.append(f" - {suggestion}")

        lines.append("\n" + "="*60)
        return "\n".join(lines)
    #============ 工具方法 ============
    def to_json(self, data: Any, indent: int = 2) -> str:
        """转换为JSON字符串"""
        return json.dumps(data, indent=indent, ensure_ascii=False)
    def save_conversation(self, file_path: str):
        """保存对话历史"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "system_prompt": self.system_prompt,
            "history": self.conversation_history
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"对话已保存: {file_path}")

    def load_conversation(self, file_path: str):
        """加载对话历史"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.system_prompt = data.get("system_prompt", self.system_prompt)
            self.conversation_history = data.get("history", [])
        logger.info(f"对话已加载: {file_path}")