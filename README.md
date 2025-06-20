# nexcode
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/release/python-370/)

一款基于 AI 的 Git 自动提交工具，能够实现对本地仓库的自动提交、自动生成提交信息、自动推送分支等功能，旨在大幅提升开发效率。

## ✨ 项目亮点

- **智能提交信息**：自动分析代码变更，生成符合语义化标准的提交信息。
- **一键操作**：将 `git add`、`git commit`、`git push` 等多个命令集于一身，一键完成。
- **分支管理**：支持自动创建新分支并完成推送，简化工作流。
- **简单易用**：人性化的命令行设计，操作直观，上手快。

## 📦 安装

1.  **克隆仓库**
    ```bash
    git clone https://github.com/YOUR_USERNAME/nexcode.git
    cd nexcode
    ```
    > 请将 `YOUR_USERNAME` 替换为实际的 GitHub 用户名。

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

3.  **安装命令行工具**
    为了在任何路径下都能使用 `nexcode` 命令，请执行：
    ```bash
    pip install .
    ```

## ⚙️ 配置

在使用前，你需要配置你的 AI 服务凭证。`nexcode` 通过环境变量读取 OpenAI API Key。

```bash
export OPENAI_API_KEY='sk-xxxxxxxxxxxxxxxxxxxxxxxx'
```
> 建议将此行代码添加到你的 `.bashrc`、`.zshrc` 或其他 shell 配置文件中，以便永久生效。

## 🚀 使用指南

### 场景一：为已暂存的更改生成提交信息

当你已经使用 `git add` 将文件暂存后，可以运行以下命令：

```bash
nexcode commit
```
此命令会自动分析暂存区的内容，生成提交信息并执行 `git commit`。

### 场景二：自动提交所有变更

如果你想让工具自动暂存所有变更、生成提交信息并推送到远程仓库，可以使用：

```bash
nexcode push
```
该命令会依次执行 `git add .`、`git commit -m "..."` 和 `git push`。

### 场景三：在新的分支上进行开发和推送

当需要在一个新分支上进行开发时，可以使用 `--branch` 选项：

```bash
nexcode push --branch "feat/new-feature"
```
工具会自动创建名为 `feat/new-feature` 的新分支，然后执行 add、commit 和 push 操作，并将本地新分支推送到远程。

## 📝 命令参考

| 命令 | 选项 | 说明 |
|---|---|---|
| `nexcode commit` | | 分析已暂存的变更，生成提交信息并提交。 |
| `nexcode push` | | 自动暂存所有变更，提交并推送到当前分支。 |
| | `--branch <branch_name>` | 创建一个新分支，然后暂存、提交并推送到新分支。 |

## 🚀 高价值功能建议

### 1. **配置管理命令** (推荐优先级：⭐⭐⭐⭐⭐)
```bash
nexcode config --list                    # 查看当前配置
nexcode config --set model.name gpt-4    # 修改配置
nexcode config --reset                   # 重置为默认配置
```

### 2. **提交历史分析** (推荐优先级：⭐⭐⭐⭐)
```bash
nexcode analyze                          # 分析最近的提交质量
nexcode suggest-improvements             # AI 建议如何改进提交习惯
```

### 3. **干运行模式** (推荐优先级：⭐⭐⭐⭐⭐)
```bash
nexcode push --dry-run                   # 预览将要进行的操作，不实际执行
nexcode commit --preview                 # 只生成提交信息，不提交
```

### 4. **多种提交信息风格** (推荐优先级：⭐⭐⭐)
```bash
nexcode commit --style conventional      # 默认的 conventional commits
nexcode commit --style semantic          # 语义化提交
nexcode commit --style simple            # 简洁风格
```

### 5. **交互式文件选择** (推荐优先级：⭐⭐⭐⭐)
```bash
nexcode commit --interactive             # 交互式选择要提交的文件
```

## 🛠️ 实用性功能

### 6. **版本信息和自更新**
```bash
nexcode --version                        # 显示版本信息
nexcode update                           # 检查并自更新
```

### 7. **模板和预设**
```bash
nexcode template --save "my-template"    # 保存当前配置为模板
nexcode template --use "my-template"     # 使用指定模板
```

### 8. **统计和报告**
```bash
nexcode stats                            # 显示使用统计
nexcode report --last-week               # 生成上周的提交报告
```

## ❓ 常见问题

- **AI 模型使用的是哪个？**  
  默认使用 `gpt-3.5-turbo`，你可以在配置文件中修改（如果项目支持）。
- **如何保证提交信息的质量？**  
  提交信息的质量依赖于 AI 模型的理解能力。清晰、原子化的代码提交有助于 AI 生成更准确的信息。
- **支持哪些 Git 平台？**  
  支持所有标准的 Git 仓库，如 GitHub, GitLab, Bitbucket 等。

## 🤝 贡献指南

我们欢迎任何形式的贡献！无论是提交 issue、修复 Bug 还是添加新功能。

1.  Fork 本仓库
2.  创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3.  提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4.  推送到分支 (`git push origin feature/AmazingFeature`)
5.  提交一个 Pull Request

## 📄 License

本项目采用 [MIT License](https://opensource.org/licenses/MIT) 授权。

---

你可以根据实际实现情况，补充依赖、API Key 配置等细节。如果需要，我可以直接帮你修改 README.md 文件。是否需要我直接帮你编辑？