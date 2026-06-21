# MyVueApp - Vue 3 企业级管理系统

## 项目概述
这是一个基于 Vue 3 构建的企业级管理系统模板，提供了完整的用户管理、权限控制和响应式界面。

## 技术栈
- **前端框架**: Vue 3.3.x (Composition API)
- **构建工具**: Vite 5.x
- **状态管理**: Pinia 2.x
- **UI组件库**: Element Plus 2.x
- **路由**: Vue Router 4.x
- **HTTP客户端**: Axios 1.x
- **样式方案**: SCSS + CSS Modules

## 核心功能
1. **用户管理**
   - 用户列表（分页、搜索、筛选）
   - 用户详情查看
   - 用户创建/编辑/删除
   - 批量操作（删除、导出）

2. **权限系统**
   - 基于角色的访问控制 (RBAC)
   - 动态路由
   - 按钮级权限控制

3. **系统设置**
   - 个人资料修改
   - 密码重置
   - 主题切换（明暗模式）

## 项目结构
src/
├── api/ # API接口定义
├── assets/ # 静态资源
├── components/ # 公共组件
├── composables/ # 组合式函数
├── layouts/ # 布局组件
├── router/ # 路由配置
├── stores/ # Pinia状态管理
├── styles/ # 全局样式
├── utils/ # 工具函数
└── views/ # 页面组件

text

## 环境变量
- `VITE_API_BASE_URL`: API基础地址
- `VITE_APP_TITLE`: 应用标题
- `VITE_APP_VERSION`: 应用版本

## 开发命令
```bash
npm run dev         # 启动开发服务器
npm run build       # 构建生产版本
npm run preview     # 预览生产构建
npm run lint        # 代码检查
部署方式
支持 Nginx、Docker、Vercel 等多种部署方式。

浏览器支持
Chrome >= 90

Firefox >= 88

Safari >= 14

Edge >= 90