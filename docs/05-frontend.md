# 05 · 前端界面与路由规范

> 版本：v1.0 ｜ 更新：2024-XX-XX ｜ 作者：学生（AI 协作）
> 上游：01、02、03、04；下游：06 任务、07 测试
> 技术：Vue 3 + TypeScript + Vite + Pinia + Vue Router + KaTeX

---

## 1. 应用骨架

- **单页应用（SPA）**，侧边栏主导航 + 顶部栏 + 主内容区。
- **布局组件**：`AppLayout`（侧边栏导航 + `<router-view>` 内容区）。

## 2. 路由表（Router）

| 路由 | 页面组件 | 说明 |
| --- | --- | --- |
| `/` | `DashboardView` | 仪表盘（统计、今日复习入口、快捷操作） |
| `/login` | `LoginView` | token 登录（`AUTH_ENABLED=true` 时引导） |
| `/notes` | `NotesView` | 笔记列表（过滤/搜索） |
| `/notes/:id` | `NoteDetailView` | 笔记详情（渲染） |
| `/notes/new` | `NoteEditorView` | 新建/编辑笔记 |
| `/quiz` | `QuizView` | 题库列表与筛选 |
| `/quiz/prepare` | `QuizPrepareView` | 组卷参数（学科/知识点/题数） |
| `/quiz/session/:id` | `QuizPlayView` | 逐题作答 |
| `/quiz/wrong` | `WrongBookView` | 错题本 |
| `/cards` | `CardsView` | 卡片列表 |
| `/cards/review` | `ReviewView` | 今日复习（正反面翻转 + 打分） |
| `/review` | `QuickReview` | 交互式快速复习：高频短时多轮（糊/生回收）+ 坑点 + 统计 |
| `/knowledge` | `KnowledgeView` | 知识点列表 |
| `/knowledge/graph` | `KnowledgeGraphView` | 知识点图谱可视化 |
| `/entries` | `EntriesView` | 数学条目（定理/命题/例题）：按类别筛选、类别+编号徽标、图片上传+AI 自动分类 |
| `/search` | `SearchView` | 全局检索 |

> 说明：路由粒度最小必备。编辑/新增可合并到 `new+edit` 组件以内联或独立页实现。

## 3. 状态管理（Pinia stores）

| Store | 状态 | 职责 |
| --- | --- | --- |
| `useAuthStore` | token, apiBase | 登录、token 持久化（localStorage）、axios 拦截器 |
| `useNoteStore` | notes, filters | 笔记列表/详情 CRUD |
| `useQuestionStore` | questions, filters | 题库 |
| `useCardStore` | cards, reviewQueue | 卡片与复习 |
| `useKnowledgeStore` | knowledge, graph | 知识点与图谱 |
| `useQuizStore` | session, answers | 刷题会话 |
| `useSubjectStore` | subjects | 学科下拉选项 |

## 4. 通用组件（components）

| 组件 | 说明 |
| --- | --- |
| `MarkdownRenderer.vue` | 统一用 markdown-it + KaTeX 渲染富文本（笔记/题目/卡片） |
| `MathInline.vue` / 由 Renderer 集成 | 行内/块级公式 |
| `TagInput.vue` | 标签输入 |
| `KnowledgePicker.vue` | 多选知识点（下拉/树） |
| `SubjectSelect.vue` | 学科下拉 |
| `QuestionCard.vue` | 展示/作答单个题目 |
| `Flashcard.vue` | 正反面翻转卡片 |
| `EmptyState.vue` / `Loading.vue` | 空态/加载 |

## 5. 关键页面交互规范

### 5.1 笔记编辑器（NoteEditorView）
- 左侧编辑 `textarea`/编辑器，右侧实时预览（`MarkdownRenderer`）。
- 提供 KaTeX 公式插入按钮。
- 保存时提交 `POST/PUT /api/notes`，成功后跳转详情。

### 5.2 题库与刷题（QuizPrepare / QuizPlay）
- 组卷页选择学科/知识点/题数 → `POST /api/quiz/sessions`。
- 作答页逐题展示，选择/输入答案 → `POST /api/quiz/sessions/{id}/answers`，即时反馈对错与解析。
- 结束显示统计，错题进入错题本。

### 5.3 间隔重复复习（ReviewView）
- 加载 `GET /api/cards/review/queue`。
- 每张卡片：先显示正面 → 点击"显示答案"翻开背面 → 按 `again/hard/good/easy` 评分 → 调 `POST /api/cards/{id}/review`。
- 队列完成后显示本轮统计。

### 5.4 知识点图谱（KnowledgeGraphView）
- 调 `GET /api/knowledge/graph?subject_id=`。
- 用轻量图渲染（初版用 `force-graph` 或自绘 SVG；若依赖较重可降级为**树/列表视图**）。
- 点击节点进入该知识点，展示其关联笔记/题目/卡片。

### 5.5 检索（SearchView）
- 顶部搜索框，`GET /api/search?q=`。
- 结果按类型分组（笔记/题目/卡片/知识点），点击跳转对应详情；关键命中词高亮（初版可选）。

## 6. API 客户端与拦截器
- `src/api/client.ts` 封装 axios，`baseURL = import.meta.env.VITE_API_BASE || '/api'`。
- 请求拦截器附加 `Authorization`；响应拦截器统一处理 `401`（跳登录）与错误提示。

## 7. 公式渲染约定
- `MarkdownRenderer` 内联 KaTeX：行内 `$...$` 与块级 `$$...$$`。
- 在 `<script setup>` 中引入 `katex`，并 `import 'katex/dist/katex.min.css'`。
- 渲染失败捕获并显示原始文本（不中断整个页面）。

## 8. 主题与体验
- 简洁、专注学习的界面；默认浅色主题。
- 所有列表均支持空态提示；加载态统一 `Loading` 组件。
- 移动端响应式优先保证可读性（可选做，非 P0 验收）。
