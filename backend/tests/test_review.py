"""快速复习接口测试。"""


def test_review_items_filter(client):
    subj = client.post("/api/subjects", json={"name": "数学分析"}).json()
    client.post("/api/entries", json={"subject_id": subj["id"], "category": "theorem", "number": "3.1", "content": "柯西收敛准则", "traps": ["条件易漏"]})
    client.post("/api/questions", json={"subject_id": subj["id"], "qtype": "calculation", "content": "求积分", "answer": "x", "number": "6.2.2"})
    # type=entry → 见数学条目
    r = client.get("/api/review/items", params={"type": "entry"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["item_type"] == "entry"
    assert data["items"][0]["traps"] == ["条件易漏"]
    # type=mixed → 见两者
    r = client.get("/api/review/items", params={"type": "mixed"})
    assert r.json()["total"] == 2


def test_review_submit_and_stats(client):
    subj = client.post("/api/subjects", json={"name": "数学分析"}).json()
    e = client.post("/api/entries", json={"subject_id": subj["id"], "category": "example", "number": "5.1", "content": "求极限"}).json()
    q = client.post("/api/questions", json={"subject_id": subj["id"], "qtype": "proof", "content": "证明", "answer": "ok"}).json()

    # 提交自评
    r = client.post("/api/review/submit", json={"item_type": "entry", "item_id": e["id"], "mastery": "hazy"})
    assert r.status_code == 200, r.text
    assert r.json()["review_count"] == 1
    r = client.post("/api/review/submit", json={"item_type": "question", "item_id": q["id"], "mastery": "familiar"})
    assert r.status_code == 200

    stats = client.get("/api/review/stats").json()
    assert stats["today_count"] >= 2
    assert stats["streak"] >= 1
    assert stats["distribution"]["hazy"] == 1
    assert stats["distribution"]["familiar"] == 1
    assert len(stats["weak_chapters"]) >= 1  # hazy 项聚合到章
