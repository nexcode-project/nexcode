# 🤖 AI Ask 功能演示

AI Commits 新增了 `ask` 功能，让你可以随时向 AI 助手询问关于 Git 提交、版本控制或开发工作流的问题！

## 🚀 使用方法

### 1. 单次问答模式

```bash
# 询问具体问题
aicommit ask --question "如何撤销最后一次提交？"
aicommit ask -q "什么是 conventional commits？"

# 询问最佳实践
aicommit ask -q "如何写好的提交消息？"

# 询问 Git 工作流
aicommit ask -q "什么是 Git Flow 工作流程？"
```

### 2. 交互式问答模式

```bash
# 启动交互式会话
aicommit ask --interactive
aicommit ask -i

# 然后你可以连续提问，直到输入 'exit' 或按 Ctrl+C 退出
```

## 💡 示例问题

### Git 基础操作
- "如何查看提交历史？"
- "如何撤销已经推送的提交？"
- "什么是 rebase 和 merge 的区别？"
- "如何解决合并冲突？"

### 提交最佳实践
- "如何写出清晰的提交消息？"
- "什么时候应该分开多个提交？"
- "如何修改最后一次提交的消息？"
- "什么是原子提交？"

### 工作流和协作
- "什么是 Git Flow 工作流？"
- "如何进行代码审查？"
- "如何管理发布分支？"
- "什么是 feature branch 工作流？"

### 高级话题
- "如何使用 Git hooks？"
- "什么是 signed commits？"
- "如何优化 Git 仓库大小？"
- "如何设置自动化部署？"

## 🎯 功能特点

### ✨ 智能响应
- 基于 AI 大模型的专业回答
- 提供具体的命令示例
- 包含最佳实践建议
- 避免常见陷阱的提醒

### 🎨 用户友好
- 清晰的问答格式
- 带进度指示器的响应等待
- 彩色输出增强可读性
- 支持中断和退出

### 🔧 灵活使用
- 单次问答：快速获取答案
- 交互模式：连续对话学习
- 支持各种复杂度的问题
- 无需离开命令行环境

## 📋 使用场景

### 👨‍💻 开发者日常
```bash
# 遇到 Git 问题时快速求助
aicommit ask -q "我想要回退到上一个版本，但保留工作区的修改"

# 学习新的 Git 功能
aicommit ask -q "Git worktree 是什么？如何使用？"
```

### 📚 学习和培训
```bash
# 启动交互模式进行系统学习
aicommit ask -i

# 然后依次询问：
# "什么是版本控制？"
# "Git 的基本概念有哪些？"
# "如何开始使用 Git？"
```

### 🔍 问题诊断
```bash
# 遇到错误时寻求解决方案
aicommit ask -q "fatal: not a git repository 错误如何解决？"

# 了解错误原因和预防
aicommit ask -q "为什么会出现 merge conflict？如何预防？"
```

## 🎉 示例对话

```
$ aicommit ask -i

🤖 AI Git Assistant - Interactive Mode
Ask me anything about Git commits, version control, or development workflows!
Type 'exit', 'quit', or press Ctrl+C to stop.

❓ Your question: 如何写出好的提交消息？

🤔 Let me think about this...
...

💡 AI Assistant Response:
==================================================
写出好的提交消息是很重要的，这里是一些最佳实践：

1. **使用清晰的格式**
   - 第一行：简短的摘要（50字符以内）
   - 空行
   - 详细描述（如果需要）

2. **遵循约定**
   - 使用现在时态："Add feature" 而不是 "Added feature"
   - 首字母大写
   - 不要以句号结尾

3. **具体示例**
   ```
   feat: add user authentication system
   
   - Implement JWT token-based authentication
   - Add login/logout endpoints
   - Include password hashing with bcrypt
   ```

4. **常见的类型前缀**
   - feat: 新功能
   - fix: 修复
   - docs: 文档
   - style: 代码格式
   - refactor: 重构
   - test: 测试

记住：好的提交消息应该能让其他开发者（包括未来的你）快速理解这次提交做了什么！
==================================================

❓ Your question: exit
👋 Goodbye! Happy coding!
```

## 🔧 技术实现

这个功能遵循了我们重构后的模块化架构：

- **`llm/services.py`**: 添加了 `ask_ai_about_commits()` 服务函数
- **`commands/ask.py`**: 实现了命令处理逻辑
- **`cli.py`**: 添加了命令定义和参数配置

完全符合我们的分层架构设计！🎯 