import os
import sys
import json
from typing import Optional, Dict, Any,List,Callable
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
from src.deepseek_client import DeepSeekClient

class CodeReviewer:
    def __init__(self,api_key: Optional[str]=None):
        self.client = DeepSeekClient(api_key=api_key)
        self.review_schema = {
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

        self.review_description = """对前端代码进行全面的代码审查，输出结构化的审查报告。
        
审查维度：
1. 代码质量（命名规范、代码复杂度、重复代码）
2. 性能问题（不必要的渲染、内存泄漏、大对象）
3. 安全性（XSS漏洞、敏感信息暴露、输入验证）
4. 可维护性（注释、模块化、依赖管理）
5. 最佳实践（框架最佳实践、ES6+特性使用）"""

    def review_code(
        self,
        code: str,
        file_name: str = "unknown.js",
        framework: str = "Vue 3",
        stream: bool = False,
        on_chunk: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        审查代码并返回结构化报告
        
        Args:
            code: 要审查的代码
            file_name: 文件名
            framework: 使用的框架
            stream: 是否流式输出
            on_chunk: 流式输出的回调函数
        
        Returns:
            结构化审查报告
        """
        prompt = self._build_review_prompt(code, file_name, framework)
        print("\n 提示词："+prompt)

        if stream:
            return self._review_stream(prompt, on_chunk)
        else:
            return self._review_structured(prompt)
        
    def _build_review_prompt(
        self,
        code: str,
        file_name: str,
        framework: str
    ) -> str:
        """构建审查提示词"""
        return f"""请对以下 {framework} 代码进行全面的代码审查，按照指定的JSON格式输出结果。

文件名: {file_name}
框架: {framework}

代码内容:
```{file_name.split('.')[-1] if '.' in file_name else 'javascript'}
{code}
请重点检查：

代码质量：命名是否规范、是否有重复代码、复杂度是否合理

性能问题：是否有性能瓶颈、内存泄漏风险

安全性：是否有XSS漏洞、敏感信息泄露

可维护性：是否易于理解、是否缺少注释

框架特定：是否符合{framework}最佳实践

请输出结构化的JSON报告。"""
    def _review_structured(self, prompt: str) -> Dict[str, Any]:
        """获取结构化审查结果"""
        response = self.client.chat_structured(
            user_message=prompt,
            schema=self.review_schema,
            description=self.review_description,
            temperature=0.1
        )
        return response
    
    def _review_stream(self, prompt: str, on_chunk: Optional[Callable]) -> Generator[Dict[str, Any], None, None]:
        """流式获取审查结果"""
        print("正在审查代码，结果将实时输出...\n")
        print("-"*60)
        print(prompt)
        print("-"*60)

        full_response = ""
        for chunk in self.client.chat_stream(
            user_message=prompt,
            save_to_history=False,
            callback=on_chunk,
            temperature=0.1
        ):
            full_response += chunk
            if on_chunk:
                on_chunk(chunk)
            else:
                print(chunk, end='', flush=True)
        print("\n" + "-"*60)
        print("审查完成！")

        json_str = self.client._extract_json(full_response)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON解析失败，尝试修复...")
            return self.client._fix_and_parse_json(json_str)
        
    def review_file(
        self,
        file_path: str,
        framework: str = "Vue 3",
        stream: bool = True
    ) -> Dict[str, Any]:
        """
        审查代码文件

        Args:
        file_path: 文件路径
        framework: 使用的框架
        stream: 是否流式输出

        Returns:
        结构化审查报告
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件未找到: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        return self.review_code(code, file_name=os.path.basename(file_path), framework=framework, stream=stream)
    
    def format_report(self, report: Dict[str, Any]) -> str:
        """格式化审查报告为可读文本"""
        if not report:
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
    
    def export_report(self, report: Dict[str, Any], output_path: str) -> None:
        """将审查报告导出为JSON文件"""
        report_wxport = {
            "timestamp": datetime.now().isoformat(),
            "report": report
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_wxport, f, ensure_ascii=False, indent=2)
        print(f"审查报告已导出到: {output_path}")

class CodeReviewerBuilder:
    @staticmethod
    def for_vue(api_key: Optional[str] = None) -> CodeReviewer:
        """构建适用于Vue项目的代码审查器"""
        return CodeReviewer(api_key=api_key)
    
    @staticmethod
    def for_react(api_key: Optional[str] = None) -> CodeReviewer:
        """构建适用于React项目的代码审查器"""
        return CodeReviewer(api_key=api_key)
    
    @staticmethod
    def for_javascript(api_key: Optional[str] = None) -> CodeReviewer:
        """构建适用于纯JavaScript项目的代码审查器"""
        return CodeReviewer(api_key=api_key)
                
