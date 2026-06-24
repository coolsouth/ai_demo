import os
import sys
import argparse
from typing import Optional

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__),'...'))
sys.path.insert(0,project_root)

from src.code_reviewer import CodeReviewer,CodeReviewerBuilder
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="AI代码审查工具")
    parser.add_argument(
        "file",
        help="要审查的代码文件路径"
    )
    parser.add_argument(
        "-f","--framework",
        default="Vue 3",
        help="代码使用的框架（默认：Vue 3）"
    )
    parser.add_argument(
        "-o","--output",
        help="输出JSON报告的文件路径"
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="禁用流式输出"
    )
    parser.add_argument(
        "--api-key",
        help="Deepseek API密钥"
    )

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 请设置 DEEPSEEK_API_KEY 环境变量或使用 --api-key 参数")
        sys.exit(1)

    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        sys.exit(1)

    reviewer = CodeReviewer(api_key)

    # 执行审查
    print(f"\n📄 正在审查文件: {args.file}")
    print(f"📚 框架: {args.framework}")
    print("-" * 60)

    try:
        report = reviewer.review_file(
            file_path=args.file,
            framework=args.framework,
            stream=not args.no_stream
        )
        print(reviewer.format_report(report))

        if args.output:
            reviewer.export_report(report, args.output)
        else:
            # 默认输出到同目录
            output_path = os.path.splitext(args.file)[0] + "_review.json"
            reviewer.export_report(report, output_path)

    except Exception as e:
        print(f"❌ 审查失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()


