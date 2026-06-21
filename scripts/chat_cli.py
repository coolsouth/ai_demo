"""
交互式CLI对话程序 - 支持多轮对话
"""
import os
import sys
import logging
from typing import List, Dict, Optional

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.deepseek_client import DeepSeekClient
from src.config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatCLI:
    def __init__(self):
        self.client = None
        self.context_file = None
        self.running = False
        
        # 颜色代码（用于美化输出）
        self.colors = {
            'user': '\033[94m',      # 蓝色
            'ai': '\033[92m',        # 绿色
            'system': '\033[93m',    # 黄色
            'error': '\033[91m',     # 红色
            'reset': '\033[0m'       # 重置
        }
    
    def _print_colored(self, text: str, color: str = 'reset', end: str = '\n'):
        """打印带颜色的文本"""
        print(f"{self.colors.get(color, '')}{text}{self.colors['reset']}", end=end)
    
    def _print_welcome(self):
        """打印欢迎信息"""
        print("\n"+"="*50)
        self._print_colored("🤖 DeepSeek 智能对话系统", 'system')
        print("="*60)
        print("命令说明:")
        print("  /clear    - 清空对话历史")
        print("  /history  - 显示对话历史")
        print("  /system   - 查看/设置系统提示词")
        print("  /context  - 加载上下文文件（项目README等）")
        print("  /quit     - 退出程序")
        print("  /help     - 显示帮助")
        print("="*60)
        print()

    def _print_history(self):

        history = self.client.get_history()

        if not history:
            self._print_colored("当前没有对话历史。", 'error')
            return
        
        print("\n" + "="*50)
        self._print_colored("📜 对话历史", 'system')
        print("="*50)

        for i, msg in enumerate(history,1):
            role = "👤 用户" if msg['role'] == 'user' else "🤖 AI"
            color = 'user' if msg['role'] == 'user' else 'ai'

            content = msg['content']
            if len(content) > 200:
                content = content[:200] + "..."  # 截断长消息
            
            print(f"[{i}] ", end=' ')
            self._print_colored(f"{role}:", color)
            print(f" {content}")

    def _load_context(self, file_path: str):
        try:
            if not os.path.isabs(file_path):
                file_path = os.path.join(os.getcwd(), file_path)

            if not os.path.exists(file_path):
                self._print_colored(f"文件不存在: {file_path}", 'error')
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                context = f.read()

            self.context_file = file_path

            context_prompt = f"""你是一个专业的项目助手。以下是项目的详细信息：

{context}

请根据以上项目信息回答用户的问题。如果问题与项目无关，请礼貌地说明。
你可以参考项目文档来回答技术问题、解释功能、提供建议等。"""
            
            self.client.set_system_prompt(context_prompt)
            
            self._print_colored(f"✅ 上下文加载成功！", 'system')
            self._print_colored(f"📄 文件: {os.path.basename(file_path)}", 'system')
            self._print_colored(f"📊 大小: {len(context)} 字符", 'system')
            return True
        
        except Exception as e:
            self._print_colored(f"❌ 加载上下文失败: {str(e)}", 'error')
            return False

    def _handle_command(self, command: str)->bool:
        parts = command.strip().split(maxsplit=1)
        cmd = parts[0].lower()

        if cmd == "/quit":
            self._print_colored("👋 再见！", 'system')
            return False
        
        elif cmd == "/clear":
            self.client.clear_history()
            self._print_colored("🧹 对话历史已清空。", 'system')
            return True
        
        elif cmd == "/history":
            self._print_history()
            return True
        
        elif cmd == "/system":
            if len(parts) > 1:
                new_prompt = ' '.join(parts[1:])
                self.client.set_system_prompt(new_prompt)
                self._print_colored("✅ 系统提示词已更新！", 'system')
            else:
                # 显示当前系统提示词
                print("\n" + "-"*60)
                self._print_colored("📝 当前系统提示词:", 'system')
                print("-"*60)
                print(self.client.system_prompt)
                print("-"*60 + "\n")
            return True
        
        elif cmd == "/context":
            if len(parts) < 2:
                self._print_colored("用法: /context <文件路径>", 'error')
                self._print_colored("示例: /context docs/README.md", 'error')
                return True
            
            file_path = ' '.join(parts[1:])
            self._load_context(file_path)
            return True
        
        elif cmd == "/help":
            self._print_welcome()
            return True
        
        else:
            self._print_colored(f"未知命令: {cmd}", 'error')
            self._print_colored("输入 /help 获取命令列表。", 'error')
            return True
        
    def run(self):
        try:
            self.client = DeepSeekClient()
            self._print_welcome()

            default_context = os.path.join(project_root, 'docs', 'README.md')
            if os.path.exists(default_context):
                self._load_context(default_context)
            
            self.running = True

            while self.running:
                try:
                    self._print_colored("👤 你: ", 'user', end='')
                    user_input = input().strip()

                    if not user_input:
                        continue

                    if user_input.startswith("/"):
                        self.running = self._handle_command(user_input)
                        continue

                    response = self.client.chat(
                        user_message=user_input,
                        stream=True
                    )

                except KeyboardInterrupt:
                    print()
                    self._print_colored("⚠️ 按 Ctrl+C 退出，或输入 /quit", 'system')
                    continue
                    
                except Exception as e:
                    self._print_colored(f"❌ 错误: {str(e)}", 'error')
                    logger.error(f"运行错误: {str(e)}", exc_info=True)
                    
        except Exception as e:
            self._print_colored(f"❌ 初始化失败: {str(e)}", 'error')
            logger.error(f"初始化失败: {str(e)}", exc_info=True)
            return
        
def main():
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("❌ 错误: 请在 .env 文件中设置 DEEPSEEK_API_KEY")
        sys.exit(1)
    
    cli = ChatCLI()
    cli.run()

if __name__ == "__main__":
    main()
