"""接口集成测试。对应文档 07 §2 测试矩阵、文档 06 T-5.2。"""
from app.core.config import settings


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---- 学科 ----
def test_subject_crud(client):
    r = client.post("/api/subjects", json={"name": "数学分析"})
    assert r.status_code == 201, r.text
    subj_id = r.json()["id"]

    r = client.get("/api/subjects")
    assert any(s["id"] == subj_id for s in r.json())

    r = client.post("/api/subjects", json={"name": "数学分析"})
    assert r.status_code == 409

    r = client.delete(f"/api/subjects/{subj_id}")
    assert r.status_code == 204


# ---- 知识点 ----
def test_knowledge_graph_and_relations(client):
    subj = client.post("/api/subjects", json={"name": "数学分析"}).json()
    k1 = client.post("/api/knowledge", json={"subject_id": subj["id"], "name": "极限"}).json()
    k2 = client.post("/api/knowledge", json={"subject_id": subj["id"], "name": "导数"}).json()

    r = client.post("/api/knowledge/relations", json={"source_id": k1["id"], "target_id": k2["id"]})
    assert r.status_code == 201

    r = client.get(f"/api/knowledge/graph?subject_id={subj['id']}")
    data = r.json()
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    assert data["edges"][0] == {"source": k1["id"], "target": k2["id"]}


# ---- 笔记 ----
def test_note_create_and_filter(client):
    subj = client.post("/api/subjects", json={"name": "数学分析"}).json()
    kp = client.post("/api/knowledge", json={"subject_id": subj["id"], "name": "极限"}).json()
    r = client.post("/api/notes", json={
        "subject_id": subj["id"], "title": "极限笔记", "content": "关于 $\\varepsilon$ 的讨论",
        "tags": ["极限"], "knowledge_ids": [kp["id"]],
    })
    assert r.status_code == 201, r.text
    note = r.json()
    assert note["tags"] == ["极限"]
    assert note["knowledge_ids"] == [kp["id"]]

    r = client.get(f"/api/notes?knowledge_id={kp['id']}")
    assert r.json()["total"] == 1


# ---- 题目与刷题（计算/证明，自评对错） ----
def test_question_and_quiz_flow(client):
    subj = client.post("/api/subjects", json={"name": "数学分析"}).json()
    kp = client.post("/api/knowledge", json={"subject_id": subj["id"], "name": "极限"}).json()
    r = client.post("/api/questions", json={
        "subject_id": subj["id"], "qtype": "calculation", "content": "计算 $\\int_0^1 x\\,dx$。",
        "answer": "$1/2$", "explanation": "", "difficulty": 3, "number": "6.2.2", "knowledge_ids": [kp["id"]],
    })
    assert r.status_code == 201, r.text
    q = r.json()
    qid = q["id"]
    # 编号 → 章/节解析
    assert q["chapter"] == 6 and q["section"] == 2 and q["number"] == "6.2.2"

    r = client.post("/api/quiz/sessions", json={"subject_id": subj["id"], "count": 5})
    assert r.status_code == 201, r.text
    session = r.json()
    assert session["questions"][0]["question"]["id"] == qid

    sess_id = session["session_id"]
    # 计算题用自评对错
    r = client.post(f"/api/quiz/sessions/{sess_id}/answers", json={"question_id": qid, "user_answer": "我算出来了", "self_correct": True})
    assert r.status_code == 200
    assert r.json()["is_correct"] is True
    r = client.post(f"/api/quiz/sessions/{sess_id}/answers", json={"question_id": qid, "user_answer": "", "self_correct": False})
    assert r.json()["is_correct"] is False

    r = client.get("/api/quiz/wrong")
    assert r.json()["total"] == 1


def test_question_chapter_filter(client):
    subj = client.post("/api/subjects", json={"name": "高等代数"}).json()
    for num, content in [("3.1.1", "特征值计算"), ("6.2", "正交化"), ("5", "行列式")]:
        client.post("/api/questions", json={"subject_id": subj["id"], "qtype": "calculation", "content": content, "answer": "x", "number": num})
    r = client.get("/api/questions", params={"chapter": 6})
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["chapter"] == 6 and data["items"][0]["section"] == 2


# ---- 卡片与复习 ----
def test_card_review_sm2(client):
    subj = client.post("/api/subjects", json={"name": "数学分析"}).json()
    r = client.post("/api/cards", json={"subject_id": subj["id"], "front": "什么是极限？", "back": "$\u03b5-\u03b4$ 语言"})
    assert r.status_code == 201, r.text
    card_id = r.json()["id"]

    # 新卡片 due 为现在，应出现在复习队列
    r = client.get("/api/cards/review/queue")
    assert any(c["id"] == card_id for c in r.json()["items"])

    r = client.post(f"/api/cards/{card_id}/review", json={"rating": "good"})
    assert r.status_code == 200
    after = r.json()["card"]
    assert after["repetitions"] == 1
    assert after["interval"] == 1
    assert after["status"] == "reviewing"


# ---- 检索 ----
def test_search(client):
    subj = client.post("/api/subjects", json={"name": "数学分析"}).json()
    client.post("/api/notes", json={"subject_id": subj["id"], "title": "柯西收敛准则", "content": "关于柯西的准则"})
    r = client.get("/api/search", params={"q": "柯西"})
    assert r.status_code == 200
    assert len(r.json()["notes"]) == 1


# ---- 图片提取核心思路/步骤 ----
def test_question_extracted_fields(client):
    subj = client.post("/api/subjects", json={"name": "数学分析"}).json()
    r = client.post("/api/questions", json={
        "subject_id": subj["id"], "qtype": "calculation",
        "content": "求极限。", "answer": "1", "number": "5.1",
        "core_idea": "用夹逼准则或等价无穷小替换。",
        "steps": ["先判断类型", "选择等价替换", "算出结果"],
        "image_path": "uploads/abc.png", "source": "image",
    })
    assert r.status_code == 201, r.text
    q = r.json()
    assert q["core_idea"] == "用夹逼准则或等价无穷小替换。"
    assert q["steps"] == ["先判断类型", "选择等价替换", "算出结果"]
    assert q["image_path"] == "uploads/abc.png"
    assert q["source"] == "image"
    assert q["chapter"] == 5 and q["section"] == 1


def test_upload_image(client):
    r = client.post("/api/questions/upload-image", files={"file": ("题目.png", b"\x89PNG\r\n\x1a\nfakepng", "image/png")})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["path"].startswith("uploads/")
    assert data["url"].startswith("/uploads/")


def test_extract_without_llm_returns_400(client, monkeypatch):
    # 强制清空 key，验证未配置时的降级（ERR_LLM_NOT_CONFIGURED），而不是 500 / 真调
    monkeypatch.setattr(settings, "llm_api_key", "")
    r = client.post("/api/questions/extract", files={"file": ("题目.png", b"fakepngbytes", "image/png")})
    assert r.status_code == 400
    assert r.json()["code"] == "ERR_LLM_NOT_CONFIGURED"
