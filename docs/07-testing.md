# 07 · 测试与验收规范

> 版本：v1.0 ｜ 更新：2024-XX-XX ｜ 作者：学生（AI 协作）
> 上游：04 接口、06 任务；目标：定义"怎么算做对了"

---

## 1. 测试分层与策略

| 层 | 工具 | 覆盖 | 说明 |
| --- | --- | --- | --- |
| 单元测试 | pytest | SM-2 算法、判分逻辑、工具函数 | 纯逻辑，无需请求 |
| 接口/集成测试 | pytest + FastAPI TestClient | 所有 API（文档 04） | 使用临时 SQLite，隔离数据 |
| 前端手工验收 | 浏览器 DevTools | 页面交互、公式渲染、路由 | 对照验收清单 |
| 端到端冒烟 | 手动 | 五大功能完整链路 | 真实接口跑通 |

## 2. 接口测试矩阵（对应文档 04）

| 测试用例 | 覆盖接口 | 关键断言 |
| --- | --- | --- |
| TC-AUTH-01 | POST /api/auth/login | 正确口令返回 token；错误返回 401 |
| TC-SUBJ-01 | GET/POST/DELETE /api/subjects | CRUD；删除级联（若启用） |
| TC-KG-01 | GET /api/knowledge/graph | 返回 nodes+edges |
| TC-KG-02 | POST /api/knowledge/relations | 建边；重复返回 409 |
| TC-NOT-01 | POST/GET/PUT/DELETE /api/notes | CRUD；tags/knowledge 关联正确；FTS 同步 |
| TC-Q-01 | GET /api/questions?qtype= & difficulty= | 筛选正确 |
| TC-QUIZ-01 | POST /api/quiz/sessions | 返回指定 count 题 |
| TC-QUIZ-02 | POST /api/quiz/sessions/{id}/answers | 判分正确；错题入库 |
| TC-SRS-01 | GET /api/cards/review/queue | 只返回到期卡片 |
| TC-SRS-02 | POST /api/cards/{id}/review | EF/interval/reps/due 正确更新 |
| TC-SEARCH-01 | GET /api/search?q= | 四类结果都命中且可跳转 |

## 3. SM-2 算法单元测试（`tests/test_sm2.py`）

输入 `(reps, interval, ef, rating)`，断言输出：
- `good` 时 reps+1、interval 按 EF 放大、EF 小幅上调。
- `again` 时 reps 归零、interval=1、EF 下调、due 立即。
- 边界：首次学习、连续多次 good 的 interval 增长符合预期。

## 4. 前端手工验收清单（对照文档 05 / 01）

| # | 场景 | 预期 |
| --- | --- | --- |
| 1 | 新建笔记，含 `$...$` 公式 | 正文与公式正确渲染 |
| 2 | 编辑并删除笔记 | 数据同步；列表刷新 |
| 3 | 组卷刷题，作答 | 判定对错、显示解析、错题入错题本 |
| 4 | 在错题本重做 | 答对后可移出错题本 |
| 5 | 创建卡片并复习 | 今日队列正确、打分后 due 更新 |
| 6 | 新建知识点并连边 | 图谱节点/边正确显示 |
| 7 | 全局搜索关键词 | 笔记/题目/卡片/知识点分组返回并可跳转 |
| 8 | 登录（启用鉴权） | 无 token 时引导登录；错误 token 提示 |
| 9 | 跨设备（可选） | 配置 apiBase 后另一设备可访问 |

## 5. 验收标准（对应文档 01 第 6 节）

1. 五大功能均可创建/查看内容，持久化到 SQLite。
2. 公式渲染正确。
3. 间隔重复正确计算今日到期并更新调度。
4. 检索返回跨类型结果并可跳转。
5. 前端全流程只走 REST API（不直连数据库）。
6. 后端 `pytest` 通过；关键接口测试覆盖文档 04 矩阵。

## 6. 缺陷级别与处理

| 级别 | 定义 | 处理 |
| --- | --- | --- |
| 致命 | 数据丢失 / 无法启动 / 校验崩溃 | 必须修复后才能交付 |
| 严重 | 核心功能不可用（如无法登录、无法刷题） | 修复后再验证 |
| 一般 | 功能可用但体验/边界问题 | 列入后续迭代 |
| 轻微 | 文案/样式 | 可合并处理 |

## 7. 完成定义（DoD）复核

每项任务完成需同时满足：
- □ 功能按文档 04/05 契约实现
- □ 对应接口测试（07 矩阵）通过或已记录
- □ 代码标注对应需求/接口编号
- □ 文档 06 任务状态已更新
