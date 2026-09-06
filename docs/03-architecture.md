# 03 · 架构设计

> 版本：v1.0 ｜ 更新：2024-XX-XX ｜ 作者：学生（AI 协作）
> 上游：01、02；下游：04 接口、05 界面、06 任务

---

## 1. 总体架构

前后端分离的 **C/S（Browser-Server）** 架构：

```
┌─────────────────────────── 浏览器（前端） ───────────────────────────┐
│  Vue3 + TS + Vite    Pinia(状态)   Vue Router(路由)   KaTeX(公式渲染)  │
│        │  REST/JSON (HTTP)                                            │
└────────┼──────────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────── 后端 ──────────────────────────────────────┐
│  FastAPI (Python 3.11+)                                               │
│   ├─ Routers : HTTP 层（参数校验、契约）                               │
│   ├─ Services: 业务层（SM-2、检索、组卷）                               │
│   ├─ Repos   : 数据访问层（SQLAlchemy ORM）                           │
│   └─ Auth    : 访问鉴权（Bearer Token）                                │
│         │                                                            │
│         ▼                                                            │
│  SQLite（单文件数据库，含 FTS5 全文检索）                                │
└──────────────────────────────────────────────────────────────────────┘
```

- **前端只通过 REST API 与后端通信**，遵守文档 04 契约。
- **后端持有全部业务逻辑与数据**，前端做纯展示与交互。

## 2. 技术选型与理由

| 层 | 选型 | 理由 |
| --- | --- | --- |
| 前端框架 | Vue 3 + TypeScript | 模板直观、生态成熟、TS 类型安全 |
| 构建 | Vite | 开发热更新快、配置简单 |
| 状态管理 | Pinia | Vue3 官方推荐，简单够用 |
| 路由 | Vue Router 4 | 标准方案 |
| 公式渲染 | KaTeX | 快、无网络依赖、中意数学场景 |
| Markdown | marked/markdown-it + KaTeX 插件 | 渲染笔记正文 |
| HTTP 请求 | axios | 拦截器统一处理 token/错误 |
| 后端 | FastAPI | 异步、自动生成 OpenAPI 文档、Pydantic 校验 |
| ORM | SQLAlchemy 2.0 | 成熟、支持 SQLite |
| 校验/序列化 | Pydantic v2 | 与 FastAPI 深度集成 |
| 数据库 | SQLite + FTS5 | 单文件、零配置、支持全文检索 |
| 测试 | pytest + httpx + TestClient | 后端单测与接口级测试 |

## 3. 后端模块划分（对应 README 目录）

```
backend/app/
├── main.py            # FastAPI 应用工厂、CORS、路由挂载
├── core/
│   ├── config.py      # 环境变量、DB 路径、密钥、鉴权开关
│   ├── auth.py        # Token 签发/校验（单用户可选）
│   └── errors.py      # 统一异常与错误响应
├── models/            # SQLAlchemy 模型（映射文档 02）
│   ├── __init__.py    # 汇总导出
│   └── *.py           # subject/knowledge/note/question/quiz/card
├── schemas/           # Pydantic 契约（对应文档 04）
│   ├── note.py / question.py / card.py / knowledge.py / quiz.py ...
├── services/
│   ├── sm2.py         # 间隔重复算法
│   ├── search.py      # FTS5 全文检索
│   ├── quiz.py        # 组卷与判分
├── routers/
│   ├── subjects.py / notes.py / questions.py / cards.py
│   ├── knowledge.py / quiz.py / search.py / auth.py
└── db.py / init_db.py # 引擎、会话、建表与种子数据
```

## 4. 关键横切设计

### 4.1 LaTeX / Markdown 渲染
- 后端**原样存储** Markdown/LaTeX 文本（不做转义）。
- 前端统一封装 `<MarkdownRenderer>`：用 `markdown-it` 解析正文，用 **KaTeX** 渲染 `$...$`（行内）与 `$$...$$`（块级）公式。
- 渲染失败（如缺少数学积号）时降级显示原始文本，不回退成一个错误页。

### 4.2 全文检索（FTS5）
- SQLite 内置 **FTS5** 虚表，对 `Note.title/content`、`Question.content`、`Card.front/back`、`KnowledgePoint.name/description` 建独立 FTS 表。
- 写入时同步更新 FTS 表（触发器或在服务层统一维护）。
- 检索命中后按类型分组，返回 `{notes:[], questions:[], cards:[], knowledge:[]}`。

### 4.3 间隔重复（SM-2）
- `services/sm2.py` 实现 `SM-2` 简化版：
  - 评分 `0=忘记(again) 1=模糊(hard) 2=记得(good) 3=简单(easy)`。
  - 更新 `repetitions`、`interval`（用 EF 放大）、`ease_factor`、`due_date`。
- 每日复习队列 = `due_date <= now` 的卡片。

### 4.4 访问鉴权（跨设备）
- 单用户，但允许其它设备经网络访问。
- 默认开启**简单 Bearer Token**：首次启动在 `.env` 生成 `ACCESS_TOKEN`（或用户设置密码）。前端登录页输入 token，axios 拦截器加到 `Authorization: Bearer <token>`。
- 后端 `auth.py` 对受保护路由校验 token。本机开发可关闭（`AUTH_ENABLED=false`）以简化。
- 若运行在 DeepSeek Harness / 其它容器环境，面向外网时建议再加反向代理 + HTTPS（超出本系统范围，仅作提示）。

### 4.5 配置与部署形态
- 通过 **环境变量 / `.env`** 配置：`DATABASE_URL`、`ACCESS_TOKEN`、`AUTH_ENABLED`、`CORS_ORIGINS`。
- **本机开发**：`uvicorn app.main:app --reload --host 127.0.0.1`；前端 `npm run dev`，Vite proxy `/api → 127.0.0.1:8000`。
- **跨设备访问**：后端监听 `0.0.0.0`，前端通过 `VITE_API_BASE` 指向后端地址。（由用户在需要时自行配置，本系统提供开关与说明。）

## 5. 前后端接口约定摘要

- 统一前缀 `/api`。
- 请求/响应均 JSON；时间用 ISO8601（UTC）。
- 错误统一格式：`{"detail": "...", "code": "<错误码>"}`。
- 完整契约见 **文档 04**。

## 6. 技术约束与已排除方案

- **不使用 Redux**（有 Pinia）。**不使用数据库迁移框架 Alembic**（初版直接 `create_all` + 种子，后续可引入）。**不使用 Docker**（单用户本机优先，保留部署说明）。
- **不做**多租户、多人协作、实时协同——超出需求范围。
