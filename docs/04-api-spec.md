# 04 · API 接口规范

> 版本：v1.0 ｜ 更新：2024-XX-XX ｜ 作者：学生（AI 协作）
> 上游：02、03；下游：05 界面、06 任务、07 测试
> 基址：`/api` ｜ 数据格式：JSON ｜ 时间：ISO8601 (UTC) ｜ 版本：由实现以 `v1` 前缀保留，初版无版本号

---

## 0. 通用约定

### 0.1 认证
- 除 `/api/auth/*` 外均需 `Authorization: Bearer <token>`。
- `AUTH_ENABLED=false` 时校验跳过（本机开发）。

### 0.2 错误响应
```json
{ "detail": "错误描述", "code": "ERR_XXX" }
```
| HTTP 状态 | 说明 |
| --- | --- |
| 400 | 参数校验失败 |
| 401 | 未认证 / token 无效 |
| 404 | 资源不存在 |
| 409 | 冲突（如重复） |
| 500 | 服务器错误 |

### 0.3 通用分页
查询列资源均返回 `{ items: [...], total: n }`。为简化初版，列表接口默认返回全部（单用户数据量小）；`limit/offset` 预留。

---

## 1. 认证 Auth（`/api/auth`）

### 1.1 获取 Token
`POST /api/auth/login`
```json
// Request
{ "token": "用户设置访问口令" }
// 200 Response
{ "token": "<生成或校验通过的 Bearer Token>", "valid": true }
// 401
{ "detail": "invalid token", "code": "ERR_AUTH_INVALID" }
```
> 说明：单用户场景，口令即访问口令；后端校验通过后返回一个签名 Bearer Token（简单 JWT/内部等价物）。

### 1.2 校验 Token
`GET /api/auth/verify` → `200 { "valid": true }`

---

## 2. 学科 Subjects（`/api/subjects`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/subjects` | 列表 |
| POST | `/api/subjects` | 新增 |
| DELETE | `/api/subjects/{id}` | 删除（级联清理其下知识点/内容） |

**POST body**：`{ "name": "数学分析", "description": "..." }`
**Subject 对象**（列表项）：
```json
{ "id": 1, "name": "数学分析", "description": "..." }
```

---

## 3. 知识点 Knowledge（`/api/knowledge`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/knowledge` | 列表，可 `?subject_id=` 过滤 |
| POST | `/api/knowledge` | 新增 |
| GET | `/api/knowledge/{id}` | 详情 |
| PUT | `/api/knowledge/{id}` | 更新 |
| DELETE | `/api/knowledge/{id}` | 删除 |
| GET | `/api/knowledge/graph?subject_id=` | 返回原子图（节点+边）用于可视化 |
| POST | `/api/knowledge/relations` | 新增依赖边 |
| DELETE | `/api/knowledge/relations` | 删除依赖边 |
| GET | `/api/knowledge/{id}/related` | 返回该点的笔记/题目/卡片 |

**KnowledgePoint 对象**：
```json
{ "id": 1, "subject_id": 1, "name": "柯西收敛准则", "description": "$\\lim...$" }
```
**GET graph 响应**：
```json
{ "nodes": [{"id":1,"name":"..."}], "edges": [{"source":1,"target":2}] }
```
**POST relations body**：`{ "source_id": 1, "target_id": 2 }`

---

## 4. 笔记 Notes（`/api/notes`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/notes` | 列表；`?subject_id=&tag=&knowledge_id=&q=` |
| POST | `/api/notes` | 新增 |
| GET | `/api/notes/{id}` | 详情 |
| PUT | `/api/notes/{id}` | 更新 |
| DELETE | `/api/notes/{id}` | 删除 |

**Note 对象**：
```json
{
  "id": 1, "subject_id": 1, "title": "极限的定义",
  "content": "...#markdown#...",
  "tags": ["极限"], "knowledge_ids": [1,2],
  "created_at": "...", "updated_at": "..."
}
```
**POST/PUT body**：`{ "subject_id":1, "title":"...", "content":"...", "tags":["..."], "knowledge_ids":[1] }`
> 服务端在保存时同步更新 FTS 索引。

---

## 5. 标签 Tags（`/api/tags`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/tags` | 全量标签 |
| POST | `/api/tags` | `{ "name": "..." }` 新增（重复返回 409） |

---

## 6. 题目 Questions（`/api/questions`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/questions` | 列表；`?subject_id=&knowledge_id=&qtype=&difficulty=&chapter=&q=` |
| POST | `/api/questions` | 新增 |
| GET | `/api/questions/{id}` | 详情（含知识点关联） |
| PUT | `/api/questions/{id}` | 更新 |
| DELETE | `/api/questions/{id}` | 删除 |

**Question 对象**：
```json
{
  "id": 1, "subject_id": 1,
  "qtype": "calculation",       // calculation(计算)/proof(证明)
  "content": "题干...", "options": null,
  "answer": "参考答案", "explanation": "解析...", "difficulty": 3,
  "number": "6.2.2", "chapter": 6, "section": 2,
  "knowledge_ids": [1],
  "core_idea": "核心思路...", "steps": ["步骤1","步骤2"],
  "image_path": "uploads/xxx.png", "source": "image"
}
```
> 作答：计算/证明题不做自动判分，由用户自评「我答对/我答错」（`self_correct`，见 §7）。

### 6.1 图片上传（图片提取功能）
`POST /api/questions/upload-image`（multipart，字段 `file`）
```json
// 200
{ "path": "uploads/xxxx.png", "url": "/uploads/xxxx.png", "size": 1234 }
```
> 前端录题表单的图片上传区支持**点击选择、拖拽图片、以及 Ctrl+V 直接粘贴截图**（读取剪贴板 `image/*` 项后调用本接口上传）。

### 6.2 从图片提取初稿（需配置 LLM_API_KEY）
`POST /api/questions/extract`（multipart，字段 `file`）
```json
// 200（未配置 LLM_API_KEY 时返回 400 code=ERR_LLM_NOT_CONFIGURED）
{
  "content": "题干文本...", "core_idea": "核心思路",
  "steps": ["步骤一","步骤二"], "answer": "答案", "explanation": "解析",
  "category": "example", "number": "", "solve_type": "calculation"
}
```
> 说明：此端点调用 OpenAI 兼容的视觉接口（后端 `.env` 配置 `LLM_API_KEY`/`LLM_BASE_URL`/`LLM_MODEL`），返回的是**初稿**，由用户在录题表单确认后再入库（对应需求「AI 初稿 + 人工确认」）。
> 用 DeepSeek 视觉模型时：`LLM_BASE_URL=https://api.deepseek.com`、`LLM_MODEL=deepseek-v4-flash-vision-exp`（其它模型会报 400 "This model does not support image"）。支持的图片格式 JPEG/PNG/GIF/WebP。

### 6.3 数学条目（定理/命题/例题）
`/api/entries`：数学内容按类别归档。`category` 取值 `theorem`(定理)/`proposition`(命题)/`example`(例题)，**无标注默认 `example`**；`number` 保留标注编号（如 `6.2.2`）。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/entries` | 列表；`?category=&subject_id=&q=`；按 类别→编号 排序 |
| POST | `/api/entries` | 新增 |
| GET | `/api/entries/{id}` | 详情 |
| PUT | `/api/entries/{id}` | 更新 |
| DELETE | `/api/entries/{id}` | 删除 |
| POST | `/api/entries/extract` | 图片提取+自动分类（返回含 `category`/`number` 的初稿） |

**Entry 对象**：
```json
{
  "id": 1, "subject_id": 1, "category": "proposition", "number": "6.2.2",
  "content": "命题 6.2.2 ...", "core_idea": "...", "steps": ["..."],
  "answer": "...", "explanation": "...", "image_path": "uploads/x.png", "source": "image"
}
```
**POST /api/entries/extract**（multipart `file`）返回：在 §6.2 基础上多出 `category`、`number`。

---

## 7. 刷题 Quiz（`/api/quiz`）

### 7.1 创建刷题会话
`POST /api/quiz/sessions`
```json
// body: 可选过滤，随机抽取 count 题
{ "subject_id": 1, "knowledge_ids": [1], "count": 10, "qtype": null, "difficulty": null }
// 200
{ "session_id": 10, "questions": [ {Question对象, "order_index":1} ] }
```
> 服务端按筛选条件随机抽 `count` 道（不足则取全部）。

### 7.2 提交单题作答
`POST /api/quiz/sessions/{id}/answers`
```json
{ "question_id": 1, "user_answer": "过程文本(可选)", "self_correct": true }
// 200
{ "is_correct": true, "correct_answer": "参考答案", "explanation": "..." }
```
> 计算/证明题不做自动判分：`is_correct` 由 `self_correct`（你自评答对/答错）决定。

### 7.3 结束会话（可选，统计）
`POST /api/quiz/sessions/{id}/finish` → `{ "total":10, "correct":7, "wrong_ids":[...] }`

### 7.4 错题本
`GET /api/quiz/wrong?subject_id=` → 返回答错的题目列表 `{ items: [Question对象], total }`

---

## 8. 记忆卡片 Cards（`/api/cards`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/cards` | 列表；`?subject_id=&knowledge_id=&status=&due=` |
| POST | `/api/cards` | 新增 |
| GET | `/api/cards/{id}` | 详情 |
| PUT | `/api/cards/{id}` | 更新（重置调度可选） |
| DELETE | `/api/cards/{id}` | 删除 |
| GET | `/api/cards/review/queue` | 今日到期卡片 |
| POST | `/api/cards/{id}/review` | 复习打分，更新 SM-2 |
| GET | `/api/cards/{id}/history` | 复习历史 |

**Card 对象**：
```json
{
  "id": 1, "subject_id": 1, "front": "...", "back": "...",
  "ease_factor": 2.5, "interval": 0, "repetitions": 0,
  "status": "new", "due_date": "...", "knowledge_ids": [1]
}
```
**POST body**：`{ "subject_id":1, "front":"...", "back":"...", "knowledge_ids":[1] }`
**POST /review body**：`{ "rating": "good" }`（`again|hard|good|easy`）
**GET /review/queue**：返回 `{ "items": [Card对象], "total": n }`

---

## 9. 检索 Search（`/api/search`）

`GET /api/search?q=关键词`
```json
// 200
{
  "notes": [{ "id":1, "title":"...", "snippet":"..." }],
  "questions": [{ "id":1, "content":"...", "snippet":"..." }],
  "cards": [{ "id":1, "front":"...", "snippet":"..." }],
  "knowledge": [{ "id":1, "name":"...", "snippet":"..." }]
}
```

---

## 9b. 快速复习（`/api/review`）
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/review/items` | 取复习批：`?type=entry|question|mixed&subject_id=&chapter=&category=&qtype=&count=`；返回 `item_type,id,front,core_idea,steps,answer,explanation,traps,category,solve_type,number,chapter,section` |
| POST | `/api/review/submit` | 自评：`{ "item_type":"entry","item_id":1,"mastery":"hazy" }`（unfamiliar/hazy/familiar）→ 更新掌握度+写日志 |
| GET | `/api/review/stats` | `{ today_count, streak, distribution:{unfamiliar,hazy,familiar}, weak_chapters:[{chapter,count}] }` |

> `traps`（坑点/易错点，JSON 数组）同时出现在 Question 与 MathEntry 对象中，复习时高亮。

---

## 10. 接口覆盖映射（回溯表）

| 接口 | 满足需求 |
| --- | --- |
| `/api/notes*` | RQ-NOT-01~05 |
| `/api/questions*` | RQ-QUIZ-01~03 |
| `/api/quiz*` | RQ-QUIZ-04~06 |
| `/api/cards*` | RQ-SRS-01~04 |
| `/api/knowledge*` | RQ-KG-01~04 |
| `/api/search` | RQ-SEARCH-01~03 |
| `/api/subjects*`、`/api/tags` | RQ-COMMON-01 |

> 测试用例（文档 07）以本表为其覆盖目标。
