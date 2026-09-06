"""数学条目（定理/命题/例题）接口测试。"""
from app.services.llm import _normalize_category, _clean_number
from app.core.config import settings


def test_normalize_category():
    assert _normalize_category("theorem") == "theorem"
    assert _normalize_category("命题") == "example"  # 非合法值兜底
    assert _normalize_category(None) == "example"


def test_clean_number():
    assert _clean_number("（6.2.2）") == "6.2.2"
    assert _clean_number("5.1 ") == "5.1"
    assert _clean_number("  ") == ""
    assert _clean_number(None) == ""


def test_entries_crud_and_filter(client):
    subj = client.post("/api/subjects", json={"name": "数学分析"}).json()
    # 创建三类条目，含编号
    for cat, num, content in [("theorem", "3.1", "柯西收敛准则"),
                              ("proposition", "6.2.2", "狄利克雷积分"),
                              ("example", "5.1", "求极限")]:
        r = client.post("/api/entries", json={"subject_id": subj["id"], "category": cat,
                                              "number": num, "content": content})
        assert r.status_code == 201, r.text
    # 筛选 category=proposition
    r = client.get("/api/entries", params={"category": "proposition"})
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["number"] == "6.2.2"
    # 学科筛选
    r = client.get("/api/entries", params={"subject_id": subj["id"]})
    assert r.json()["total"] == 3


def test_entries_sort_order(client):
    subj = client.post("/api/subjects", json={"name": "高等代数"}).json()
    client.post("/api/entries", json={"subject_id": subj["id"], "category": "example", "number": "10", "content": "例10"})
    client.post("/api/entries", json={"subject_id": subj["id"], "category": "example", "number": "2", "content": "例2"})
    client.post("/api/entries", json={"subject_id": subj["id"], "category": "theorem", "number": "1.1", "content": "定理"})
    r = client.get("/api/entries", params={"subject_id": subj["id"]})
    items = r.json()["items"]
    cats = [i["category"] for i in items]
    assert cats[0] == "theorem"  # 定理排前
    assert cats[-1] == "example"
    # example 内按数字感知排序：2 在 10 前面
    nums = [i["number"] for i in items if i["category"] == "example"]
    assert nums == ["2", "10"]


def test_entries_extract_without_llm_400(client, monkeypatch):
    # 强制清空 key，验证未配置时的降级
    monkeypatch.setattr(settings, "llm_api_key", "")
    r = client.post("/api/entries/extract", files={"file": ("题.png", b"fakepng", "image/png")})
    assert r.status_code == 400
    assert r.json()["code"] == "ERR_LLM_NOT_CONFIGURED"
