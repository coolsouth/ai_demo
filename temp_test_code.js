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