"""
演示结构化输出功能
"""
import os
import sys
import json

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.deepseek_client import DeepSeekClient
from src.code_reviewer import CodeReviewer,CodeReviewerBuilder

def demo_basic_structured():
    print("\n"+"="*60)
    print("📝 示例1: 基本结构化输出 - 产品信息提取")
    print("=" * 60)

    client = DeepSeekClient()

    schema = {
        "type": "object",
        "properties": {
            "product_name": {"type": "string"},
            "category": {"type": "string"},
            "price": {"type": "number"},
            "currency": {"type": "string"},
            "features": {"type": "array", "items": {"type": "string"}},
            "rating": {"type": "number", "minimum": 0, "maximum": 5},
            "in_stock": {"type": "boolean"}
        },
        "required": ["product_name", "price", "category"]
    }

    user_message = """请提取以下产品信息：
    
产品名称：AI智能编程助手
类别：开发工具
价格：99.99美元
主要功能：代码生成、代码审查、Bug修复、文档生成
评分：4.8分
库存状态：有货"""

    result = client.chat_structured(
        user_message=user_message,
        schema=schema,
        description="提取产品信息并返回结构化JSON"
    )

    print("\n 提取结果：")
    print(json.dumps(result, indent=2, ensure_ascii=False))

def demo_code_review():
    """演示代码审查工具"""
    print("\n" + "=" * 60)
    print("🔍 示例2: AI代码审查工具")
    print("=" * 60)

    reviewer = CodeReviewer()

    sample_code = """
// 一个包含多种问题的Vue组件示例
<template>
  <div>
    <h1>{{ title }}</h1>
    <div v-for="item in items" :key="item.id">
      {{ item.name }}
    </div>
    <button @click="handleClick">点击</button>
  </div>
</template>

<script>
export default {
  name: 'SampleComponent',
  data() {
    return {
      title: 'Hello World',
      items: [],
      // 未使用的变量
      unused: '这个变量没有使用'
    }
  },
  methods: {
    // 缺少错误处理
    async fetchData() {
      const response = await fetch('/api/data')
      this.items = await response.json()
    },
    // 性能问题：每次都会重新创建函数
    handleClick() {
      // 直接操作DOM（在Vue中不推荐）
      document.querySelector('h1').style.color = 'red'
      // 潜在的内存泄漏
      setInterval(() => {
        console.log('interval running')
      }, 1000)
    },
    // 过长的函数
    longFunction() {
      // 这里省略了100行代码...
      console.log('do something')
      console.log('do something else')
      console.log('do more')
      // ...
    }
  },
  mounted() {
    this.fetchData()
    // 缺少清理
  }
}
</script>

<style scoped>
h1 {
  color: blue;
}
/* 未使用的样式 */
.unused-style {
  display: none;
}
</style>
"""

    print("\n📄 正在审查代码...\n")
    report = reviewer.review_code(
        code=sample_code,
        file_name="SampleComponent.vue",
        framework="Vue 3",
        stream=True
    )

    print("\n"+reviewer.format_report(report))

def demo_code_review_from_file():
    """演示从文件审查代码"""
    print("\n" + "=" * 60)
    print("📁 示例3: 从文件审查代码")
    print("=" * 60)

    test_file = os.path.join(project_root, "temp_test_code.js")

    test_code = """
// 一个有问题的JavaScript函数
function processUserData(data) {
  // 缺少类型检查
  let result = []
  for (let i = 0; i < data.length; i++) {
    // 直接修改原始数据
    data[i].processed = true
    // 使用var而不是let/const
    var temp = data[i].name
    result.push(temp)
  }
  // 没有返回值
}

// 安全性问题
function getUserInput() {
  const input = document.getElementById('userInput').value
  // 直接插入HTML (XSS漏洞)
  document.getElementById('output').innerHTML = input
}

// 性能问题
function badLoop() {
  for (let i = 0; i < 1000000; i++) {
    // 在循环中创建数组
    let arr = new Array(1000)
    for (let j = 0; j < arr.length; j++) {
      arr[j] = i + j
    }
  }
}
"""

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_code)

    try:
        reviewer = CodeReviewer()
        report = reviewer.review_file(
            file_path=test_file,
            framework='JavaScript',
            stream=True
        )
        print("\n"+reviewer.format_report(report))

        output_path = os.path.join(project_root, "review_report.json")
        reviewer.export_report(report,output_path)

    finally:
        if os.path.exists(test_file):
            os.remove(test_file)
    
def demo_structured_with_thinking():
    """演示带思考过程的结构化输出"""
    print("\n" + "=" * 60)
    print("🧠 示例4: 带思考过程的结构化输出")
    print("=" * 60)
    
    client = DeepSeekClient()
    
    schema = {
        "type": "object",
        "properties": {
            "problem": {"type": "string"},
            "root_cause": {"type": "string"},
            "solution": {"type": "string"},
            "steps": {"type": "array", "items": {"type": "string"}},
            "risks": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["problem", "solution"]
    }
    
    user_message = """我在使用Vue 3时遇到一个性能问题：
    
现象：列表渲染时，当数据量超过1000条，页面卡顿严重。
场景：使用v-for渲染列表，每个列表项包含复杂的计算属性。
排查：已经使用了v-for的key，但问题仍然存在。"""

    # 使用v4-pro模型，启用思考过程
    client.model = "deepseek-v4-pro"
    
    result = client.chat_structured(
        user_message=user_message,
        schema=schema,
        description="分析性能问题并提供解决方案",
        temperature=0.3
    )
    
    print("\n✅ 分析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    print("开始演示结构化输出功能...")

    #开始测试开启下面其中任意几个
    demo_basic_structured()
    #demo_code_review()
    #demo_code_review_from_file()
    #demo_structured_with_thinking()
    
    print("\n" + "=" * 60)
    print("✅ 所有演示完成！")
    print("=" * 60)


