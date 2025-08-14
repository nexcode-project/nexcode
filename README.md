# NexCode

<div align="center">
  <img src="docs/images/logo.png" alt="NexCode Logo" width="200">
  <h3>Intelligent AI Coding Assistant & Collaboration Platform</h3>
  <p>A LLM-powered toolkit to augment the end-to-end software engineering workflow for teams.</p>
</div>

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Node.js](https://img.shields.io/badge/node.js-16%2B-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green.svg)
![React](https://img.shields.io/badge/React-18%2B-blue.svg)

</div>

## 🌟 Core Features

### 🤖 AI-Powered Coding Assistance
- Intelligent code review: detect potential bugs, security risks, and performance issues
- Commit message generation: produce standard, high-quality commit messages
- Code quality checks: comprehensive static quality analysis and suggestions
- Smart Q&A: development-oriented Q&A with context awareness

### 🔧 Multi-Client Collaboration
- CLI: powerful terminal tooling integrated with Git workflow
- Web collaborative docs: real-time co-editing for develop documents
- Admin Console: full system management and monitoring

### 🔐 Enterprise-Grade Capabilities
- Multi-auth support: username/password, CAS SSO, JWT
- Role-based access control: fine-grained permissions
- Analytics & insights: usage stats and trends
- System health monitoring: real-time status

## 🏗️ Architecture

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   nexcode_cli   │  │   nexcode_web   │  │  nexcode_admin  │
│ (Command Line)  │  │   (Web UI)      │  │  (Admin Panel)  │
└─────────┬───────┘  └─────────┬───────┘  └─────────┬───────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                    ┌─────────────────┐
                    │ nexcode_server  │
                    │  (FastAPI)      │
                    └─────────┬───────┘
                              │
                    ┌─────────────────┐
                    │  DB & LLMs      │
                    │ (SQLite/OpenAI) │
                    └─────────────────┘
```

## 🚀 Quick Start

### Option A: Docker Compose (Recommended)

```bash
# 1) Clone the project
git clone https://github.com/your-org/nexcode.git
cd nexcode

# 2) Start all services
cd docker
docker-compose up -d

# 3) Access services
# Web:       http://localhost:3000
# Admin:     http://localhost:5433
# API Docs:  http://localhost:8000/docs
```

### Option B: Local Development

<details>
<summary>Expand detailed steps</summary>

#### 1) Backend (FastAPI)
```bash
cd nexcode_server
pip install -r requirements_server.txt

# Initialize DB
python scripts/init_db.py

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2) Web App (optional)
```bash
cd nexcode_web
npm install
npm run dev
# Visit: http://localhost:3000
```

#### 3) Admin Console (optional)
```bash
cd nexcode_admin
npm install
npm run dev
# Visit: http://localhost:5433
```

#### 4) CLI
```bash
cd nexcode_cli
pip install -e .

# Configure CLI
nexcode config set api_server.url "http://localhost:8000"
nexcode config set openai.api_key "your-openai-api-key"
```

</details>

## 💻 Usage Guide

### 🖥️ CLI (Developer Recommended)

```bash
# Code quality checks
nexcode check                          # check current changes
nexcode check --files src/main.py      # check specific files

# Smart commits
nexcode commit                         # generate and commit
nexcode commit --dry-run               # preview commit message

# Intelligent Q&A
nexcode ask "How to optimize this function?" --files src/utils.py
nexcode ask "Difference between Git rebase and merge?"

# Git error diagnosis
nexcode diagnose                       # diagnose the last Git error

# Push strategy
nexcode push                           # get smart push suggestions
nexcode push --dry-run                 # preview push plan

# Repository analysis
nexcode analyze --type overview        # project overview
nexcode analyze --type structure       # structure analysis
nexcode analyze --type dependencies    # dependency analysis
```

### 🌐 Web UI

Visit `http://localhost:3000` with default accounts:
- Demo: `demo` / `demo123`
- Admin: `admin` / `admin123`

Key features:
- Dual-mode AI chat: built-in assistant + OpenAI GPT
- Runtime tunables: switch model, temperature, max tokens
- Contextual conversation: multi-turn with history
- Responsive design: desktop and mobile friendly

### 🛠️ Admin Console

Visit `http://localhost:5433`

Highlights:
- System dashboard: status, performance, resource usage
- User management: accounts, roles, API keys
- Analytics: commit stats, quality trends, user activity
- System settings: global configs, CAS, security
- API monitoring: usage stats, latency, errors

### 🔌 OpenAI API Compatible

```python
import openai

# Use NexCode as a drop-in replacement
client = openai.OpenAI(
    api_key="your-openai-api-key",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello, NexCode!"}]
)
```

## 📋 Feature Matrix

### ✅ Implemented

- Code Review based on Git diff
- Commit Message Generation
- Git Error Analysis
- Code Quality Check
- Intelligent Q&A (Git, code, workflow)
- Push Strategy Analysis
- Repository Analysis
- CLI, Web Chat UI, Admin Panel, Responsive UI
- Auth (multi-methods), RBAC, Usage Analytics
- OpenAI Compatibility Layer, Dockerized deployment

### 🔧 Configuration Management
- Environment variables
- CLI config system (local & global)
- TOML-based prompt templates
- Multiple model providers (OpenAI, Azure OpenAI, ...)

## 🚧 Roadmap

### 🎯 Near-term (v1.3.0)
- Real repository analysis (read & analyze project files)
- RAG Q&A over repository content
- Context-aware code review with project history
- Intelligent code completion

- Test generation (`nexcode test`)
- Doc generation (`nexcode doc`)
- Code scaffolding (`nexcode generate`)
- Refactoring assistant (`nexcode refactor`)

- Dependency vulnerability scanning
- Secrets scanning (`nexcode scan:secrets`)
- Coverage reporting
- Performance profiling

### 🔮 Mid-term (v1.4.0)
- GitHub App for PR reviews
- GitLab integration (webhooks)
- Jenkins plugin (CI/CD)
- Automation workflows (rule-based)

- Collaborative code review
- Team knowledge base
- Linting / style enforcement
- Technical debt tracking

- Code complexity metrics
- Architecture dependency analysis
- Code evolution & hotspots
- Developer productivity metrics

### 🌟 Long-term (v2.0.0)
- Multimodal understanding (images, diagrams)
- Natural language programming for complex tasks
- Smart debugging based on error traces
- Automated refactoring

- Plugin system
- IDE integrations (VSCode, JetBrains)
- Cloud/SaaS offering
- Enterprise-scale deployment

## 📊 Tech Stack

### Backend
- FastAPI (Python)
- SQLAlchemy, Alembic, Pydantic
- PostgreSQL/SQLite

### Frontend
- Next.js 14, React 18, TypeScript
- Tailwind CSS, Zustand, Framer Motion

### CLI
- Click, GitPython, Rich, PyYAML

### AI & Integration
- OpenAI API, LangChain, Tiktoken, Jinja2

## 🔧 Configuration

Environment variables (examples):

```bash
# OpenAI settings
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# Database
DATABASE_URL=sqlite:///./nexcode.db

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Auth
REQUIRE_AUTH=false
JWT_SECRET_KEY=your-secret-key
CAS_SERVER_URL=https://cas.example.com
```

CLI config:

```bash
# View configs
nexcode config list
nexcode config get openai.api_key

# Set configs
nexcode config set openai.api_key "sk-..."
nexcode config set api_server.url "http://localhost:8000"
nexcode config set model.temperature 0.7

# Reset configs
nexcode config reset
```

## 🌐 API Overview

OpenAI-compatible:
- POST `/v1/chat/completions`
- POST `/v1/completions`
- GET `/v1/models`

NexCode endpoints:
- POST `/v1/code-review`
- POST `/v1/commit-message`
- POST `/v1/intelligent-qa`
- POST `/v1/git-error-analysis`
- POST `/v1/code-quality-check`
- POST `/v1/push-strategy`
- POST `/v1/repository-analysis`

Admin endpoints:
- POST `/v1/auth/login`
- GET `/v1/auth/me`
- GET `/v1/users`
- GET `/v1/commits`
- GET `/v1/admin/stats`

## 🚀 Deployment

### Docker (Recommended)
```bash
# 1) Clone
git clone https://github.com/your-org/nexcode.git
cd nexcode

# 2) Env
cp docker/.env.example docker/.env
# edit docker/.env

# 3) Start
cd docker
docker-compose up -d

# 4) Status
docker-compose ps
docker-compose logs -f
```

### Manual Deployment

<details>
<summary>Expand detailed steps</summary>

Backend:
```bash
cd nexcode_server
pip install -r requirements_server.txt

# Env
export OPENAI_API_KEY="your-key"
export DATABASE_URL="postgresql://user:pass@localhost/nexcode"

# Init DB
python scripts/init_db.py

# Run
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Web:
```bash
cd nexcode_web
npm install
npm run build
# serve the build with nginx or any static server
```

Admin:
```bash
cd nexcode_admin
npm install
npm run build
# serve the build with a static server
```

</details>

## 🔍 Monitoring & Logs

Health checks:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
```

Logs:
```bash
docker-compose logs -f nexcode_server
# or a specific time window
docker-compose logs --since="2024-01-01" nexcode_server
```

## 🤝 Contributing

We welcome all kinds of contributions!

Workflow:
1. Fork the repo
2. Create a branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'feat: add amazing feature'`
4. Push branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Guidelines:
- Follow existing code style
- Add appropriate test coverage
- Update relevant docs
- Use Conventional Commits

## 📄 License

MIT License. See `LICENSE`.

## 🙏 Acknowledgements

Thanks to these awesome projects and communities:
- OpenAI — LLM capabilities
- FastAPI — high-performance web framework
- Next.js — excellent React framework
- Click — Python CLI framework
- Ant Design — enterprise-grade UI components

## 📞 Contact

- Project: https://github.com/your-org/nexcode
- Docs: https://nexcode.dev
- Issues: https://github.com/your-org/nexcode/issues
- Discussions: https://github.com/your-org/nexcode/discussions

---

<div align="center">
  <p><strong>NexCode Team</strong> — Empower every line of code with AI</p>
  <p>⭐ If you find this project helpful, please give us a star!</p>
</div> 
