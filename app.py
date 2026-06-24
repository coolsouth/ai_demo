"""
AI对话工具 - Streamlit Web界面
支持：多轮对话、流式输出、结构化输出、代码审查
"""
import os
import sys
import json
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.ai_toolkit import AIToolkit

# 加载环境变量
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="AI 对话工具",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .stChatMessage {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .review-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #007bff;
    }
    .severity-critical { color: #dc3545; }
    .severity-major { color: #fd7e14; }
    .severity-minor { color: #28a745; }
    .severity-suggestion { color: #17a2b8; }
</style>
""", unsafe_allow_html=True)

class StreamlitApp:
    """Streamlit应用"""
    
    def __init__(self):
        self.init_session_state()
        self.init_sidebar()
        self.render_main()

    def init_session_state(self):
        """初始化session state"""
        if 'toolkit' not in st.session_state:
            try:
                st.session_state.toolkit = AIToolkit()
                st.session_state.messages = []
                st.session_state.current_mode = "chat"
                st.session_state.review_result = None
            except Exception as e:
                st.error(f"初始化失败: {str(e)}")
                st.stop()
        
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'current_mode' not in st.session_state:
            st.session_state.current_mode = "chat"
        
        if 'review_result' not in st.session_state:
            st.session_state.review_result = None

    def init_sidebar(self):
        """初始化侧边栏"""
        with st.sidebar:
            st.title("⚙️ 设置")
            
            # 模型选择
            model = st.selectbox(
                "选择模型",
                ["deepseek-chat", "deepseek-v4-pro"],
                help="deepseek-v4-pro支持推理增强"
            )
            st.session_state.toolkit.model = model
            
            # 温度控制
            temperature = st.slider(
                "温度 (Temperature)",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="越高越随机，越低越确定"
            )
            st.session_state.toolkit.config.TEMPERATURE = temperature
            
            # 系统提示词
            st.subheader("系统提示词")
            system_prompt = st.text_area(
                "系统提示词",
                value=st.session_state.toolkit.system_prompt,
                height=100,
                help="设置AI的角色和行为"
            )
            if st.button("更新系统提示词"):
                st.session_state.toolkit.set_system_prompt(system_prompt)
                st.success("✅ 系统提示词已更新")
            
            st.divider()
            
            # 上下文管理
            st.subheader("📚 上下文管理")
            context_file = st.file_uploader(
                "上传项目文档 (README.md)",
                type=['md', 'txt', 'json']
            )
            if context_file:
                try:
                    content = context_file.read().decode('utf-8')
                    st.session_state.toolkit.set_context(content, source=context_file.name)
                    st.success(f"✅ 已加载上下文: {context_file.name}")
                except Exception as e:
                    st.error(f"加载失败: {str(e)}")
            
            # 或直接输入上下文
            context_text = st.text_area(
                "或直接输入上下文",
                height=100,
                placeholder="输入项目信息、文档等..."
            )
            if st.button("应用上下文"):
                if context_text:
                    st.session_state.toolkit.set_context(context_text, source="manual")
                    st.success("✅ 上下文已应用")
            
            st.divider()
            
            # 操作按钮
            st.subheader("操作")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ 清空历史"):
                    st.session_state.toolkit.clear_history()
                    st.session_state.messages = []
                    st.success("已清空")
            with col2:
                if st.button("💾 保存对话"):
                    filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    st.session_state.toolkit.save_conversation(filename)
                    st.success(f"已保存: {filename}")
            
            # 对话统计
            if st.session_state.messages:
                st.divider()
                st.subheader("📊 统计")
                history = st.session_state.toolkit.get_history()
                st.metric("对话轮次", len(history) // 2)
                st.metric("消息数", len(history))

    def render_main(self):
        """渲染主界面"""
        # 标签页
        tabs = st.tabs(["💬 对话", "🔍 代码审查", "📄 结构化输出"])
        
        with tabs[0]:
            self.render_chat_tab()
        
        with tabs[1]:
            self.render_review_tab()
        
        with tabs[2]:
            self.render_structured_tab()

    def render_chat_tab(self):
        """渲染对话标签页"""
        st.header("💬 AI 对话")
        
        # 显示对话历史
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # 输入框
        if prompt := st.chat_input("输入你的消息..."):
            # 添加用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 获取AI回复
            with st.chat_message("assistant"):
                try:
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    # 流式输出
                    temperature = st.session_state.toolkit.config.TEMPERATURE if hasattr(st.session_state.toolkit.config, 'TEMPERATURE') else 0.7
                    
                    for chunk in st.session_state.toolkit.chat(
                        user_message=prompt,
                        stream=True,
                        temperature=temperature
                    ):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                    
                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                except Exception as e:
                    st.error(f"错误: {str(e)}")

    def render_review_tab(self):
        """渲染代码审查标签页"""
        st.header("🔍 AI 代码审查")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            code = st.text_area(
                "输入要审查的代码",
                height=300,
                placeholder="// 粘贴你的代码..."
            )
        
        with col2:
            file_name = st.text_input("文件名", value="component.vue")
            framework = st.selectbox(
                "框架",
                ["Vue 3", "React", "JavaScript", "TypeScript", "HTML/CSS", "Python"]
            )
            stream_review = st.checkbox("流式输出", value=True)
            
            if st.button("🚀 开始审查", type="primary"):
                if not code.strip():
                    st.warning("请先输入代码")
                else:
                    try:
                        with st.spinner("AI正在审查代码..."):
                            report = st.session_state.toolkit.review_code(
                                code=code,
                                file_name=file_name,
                                framework=framework,
                                stream=stream_review
                            )
                            st.session_state.review_result = report
                            st.success("✅ 审查完成")
                    except Exception as e:
                        st.error(f"审查失败: {str(e)}")
        
        # 显示审查结果
        if st.session_state.review_result:
            report = st.session_state.review_result
            
            if "error" in report:
                st.error(f"解析失败: {report.get('error', 'Unknown error')}")
                if "raw" in report:
                    st.text(report["raw"])
                return
            
            # 摘要
            summary = report.get("summary", {})
            st.subheader("📊 审查摘要")
            cols = st.columns(5)
            cols[0].metric("总问题", summary.get("total_issues", 0))
            cols[1].metric("🔴 严重", summary.get("critical_count", 0), delta_color="off")
            cols[2].metric("🟡 主要", summary.get("major_count", 0), delta_color="off")
            cols[3].metric("🟢 次要", summary.get("minor_count", 0), delta_color="off")
            cols[4].metric("评分", f"{summary.get('overall_score', 0)}/100")
            
            if summary.get("overall_assessment"):
                st.info(f"📝 {summary.get('overall_assessment')}")
            
            # 问题列表
            issues = report.get("issues", [])
            if issues:
                st.subheader(f"🐛 问题列表 ({len(issues)}个)")
                for issue in issues:
                    severity = issue.get("severity", "minor")
                    emoji = {"critical": "🔴", "major": "🟡", "minor": "🟢", "suggestion": "💡"}.get(severity, "⚪")
                    
                    with st.expander(f"{emoji} [{severity.upper()}] {issue.get('title', 'N/A')}"):
                        st.write(f"**描述:** {issue.get('description', 'N/A')}")
                        if issue.get("suggestion"):
                            st.write(f"**💡 建议:** {issue.get('suggestion')}")
                        if issue.get("line_numbers"):
                            st.write(f"**行号:** {', '.join(map(str, issue.get('line_numbers', [])))}")
                        if issue.get("code_snippet"):
                            st.code(issue.get("code_snippet"), language="javascript")
            
            # 改进建议
            suggestions = report.get("improvement_suggestions", [])
            if suggestions:
                st.subheader("🚀 改进建议")
                for suggestion in suggestions:
                    st.write(f"• {suggestion}")
            
            # 导出
            if st.button("📥 导出报告"):
                filename = f"review_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                st.success(f"已导出: {filename}")

    def render_structured_tab(self):
        """渲染结构化输出标签页"""
        st.header("📄 结构化输出")
        
        st.markdown("""
        AI会按照指定的JSON格式输出结果，方便程序化处理。
        """)
        
        # 预设场景
        scenario = st.selectbox(
            "选择场景",
            ["自定义", "产品信息提取", "问题分析", "会议纪要", "代码审查"]
        )
        
        if scenario == "产品信息提取":
            schema = {
                "product_name": {"type": "string", "description": "产品名称"},
                "category": {"type": "string", "description": "产品类别"},
                "price": {"type": "number", "description": "价格"},
                "features": {"type": "array", "items": {"type": "string"}, "description": "功能列表"},
                "rating": {"type": "number", "description": "评分", "minimum": 0, "maximum": 5}
            }
            default_prompt = "请分析这个产品：AI智能编程助手，售价99.99美元，支持代码生成和审查，评分4.8"
        else:
            schema = {
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "details": {"type": "object"}
                }
            }
            default_prompt = ""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Schema (JSON结构)")
            schema_text = st.text_area(
                "定义输出结构",
                value=json.dumps(schema, indent=2, ensure_ascii=False),
                height=200
            )
            
            user_prompt = st.text_area(
                "用户消息",
                value=default_prompt,
                height=150,
                placeholder="输入要处理的内容..."
            )
        
        with col2:
            st.subheader("输出结果")
            
            if st.button("🚀 生成结构化输出", type="primary"):
                try:
                    schema_dict = json.loads(schema_text)
                    
                    with st.spinner("AI正在生成..."):
                        result = st.session_state.toolkit.chat_structured(
                            user_message=user_prompt,
                            schema=schema_dict,
                            temperature=0.1
                        )
                        
                        st.json(result)
                        
                        # 复制按钮
                        json_str = json.dumps(result, indent=2, ensure_ascii=False)
                        st.code(json_str, language="json")
                        
                except json.JSONDecodeError as e:
                    st.error(f"Schema格式错误: {str(e)}")
                except Exception as e:
                    st.error(f"生成失败: {str(e)}")

def main():
    """主函数"""
    if not os.environ.get('DEEPSEEK_API_KEY'):
        st.error("""
        ❌ 请设置 DEEPSEEK_API_KEY 环境变量
        
        在项目根目录创建 `.env` 文件：```DEEPSEEK_API_KEY=your_api_key_here```""")
        return 
    # 运行应用
    app = StreamlitApp()


if __name__ == "__main__":
    main()