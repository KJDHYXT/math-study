# 数学学硕备考 · 学习与复习功能专区

一个基于**规范驱动开发（SDD）** 的前后端分离网页系统，服务用户备考**数学学硕（数学分析、高等代数/线性代数）**。
覆盖：**笔记管理、题库与刷题、知识点图谱、知识检索、记忆卡片/间隔重复** 五大能力，支持 LaTeX 公式渲染，单用户本机使用、预留跨设备访问。题库支持**题目图片上传**，并可**从图片自动提取「核心思路 + 简明操作步骤」**（AI 初稿，人工确认后入库）。另有**数学条目**归档：按 **定理/命题/例题** 分类并**保留编号**，图片自动归类（无标注默认「例题」）。题库题目**按章节（章/节）组织**，题型为 **计算/证明**（作答时自评对错），提取时自动识别计算或证明。新增**交互式快速复习**：把定理/命题/例题与题目做成"框框"，**展示→主动回忆→看答案→自评(熟/糊/生)→糊/生本轮再现**，支持**坑点/易错标注**与**掌握度/今日复习量/连续打卡/薄弱章节**统计。

> 所有规范文档见 [docs/](./docs/README.md)，是实现与验收的唯一依据。

## 技术栈

- **前端**：Vue 3 + TypeScript + Vite + Pinia + Vue Router + KaTeX
- **后端**：Python + FastAPI + SQLAlchemy + Pydantic + SQLite
- **测试**：pytest（后端）｜ Vite 构建 + 手工验收（前端）

## 目录结构

```
analysis/
├── docs/        # SDD 规范文档体系（00~07）
├── backend/     # FastAPI 后端
│   ├── app/
│   │   ├── main.py        # 入口
│   │   ├── models/        # SQLAlchemy 模型
│   │   ├── schemas/       # Pydantic 契约
│   │   ├── services/      # SM-2 / 检索 / 判分 / 序列化
│   │   ├── routers/       # API 路由
│   │   └── init_db.py     # 建库 + 种子
│   └── tests/             # pytest
└── frontend/    # Vue3 Vite 前端
    └── src/     # views / components / stores / api / router
```

## 快速开始

### 1. 后端（本机）

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- 首次启动自动建库 `math_study.db` 并写入示例（学科/知识点/笔记/题目/卡片）。
- 打开 `http://127.0.0.1:8000/docs` 可查看自动生成的 OpenAPI 文档。
- 可选：复制 `.env.example` 为 `.env` 以启用鉴权、更改端口/数据库。

### 2. 前端（本机）

```powershell
cd frontend
npm install
npm run dev
```

打开 `http://127.0.0.1:5173`。开发模式下 Vite 将 `/api` 代理到 `http://127.0.0.1:8000`。

### 3. 测试

```powershell
cd backend
.venv\Scripts\python -m pytest -q
```

### 3.5 配「从图片提取核心思路/步骤」（可选，用 DeepSeek 视觉模型）

在 `backend/.env` 填三项，然后重启后端：

```ini
LLM_API_KEY=你的DeepSeek密钥
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash-vision-exp
```

- **必须**用支持图片的视觉模型 `deepseek-v4-flash-vision-exp`（其它模型调用图片会报 400 "This model does not support image"）。
- 支持的图片格式：JPEG / PNG / GIF / WebP。
- 不配置时「从图片提取」按钮会提示手动填写（有意为之的降级）。
- 也可换成任何 OpenAI 兼容的视觉接口（OpenAI `gpt-4o-mini`、通义 `qwen-vl`、本地 Ollama 等），改对应 `LLM_BASE_URL`/`LLM_MODEL` 即可。

### 4. 跨设备访问（可选）

- 后端监听 `0.0.0.0`：`uvicorn app.main:app --host 0.0.0.0 --port 8000`
- 前端设置后端地址：复制 `frontend/.env.example` 为 `.env.local`，设 `VITE_API_BASE=http://<后端IP>:8000`。
- 建议开启鉴权（后端 `.env` 设 `AUTH_ENABLED=true` 并设置 `ACCESS_TOKEN`），并在前端登录页输入对应口令。
- 若对外暴露，建议搭配反向代理 + HTTPS（超出本系统范围）。

## 文档状态

| 里程碑 | 状态 |
| --- | --- |
| M0 项目与骨架 | ✅ |
| M1 数据层与基础设施 | ✅ |
| M2 后端核心 API（5 大功能，pytest 通过） | ✅ |
| M3 前端基础设施 | ✅ |
| M4 前端功能页面（已构建 + 联调） | ✅ |
| M5 集成与验收（端到端验证） | ✅ |

> 对应文档 [06 任务分解](./docs/06-task-breakdown.md)。
