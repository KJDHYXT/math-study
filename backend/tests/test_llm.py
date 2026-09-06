"""LLM 提取服务的请求体/解析测试。

验证：请求体符合 DeepSeek-V4-Flash-Vision-Exp 官方「图像理解」契约
（base64 内联 image_url、图片仅放 user 消息、模型名正确），以及响应解析。
"""
from app.services.llm import build_chat_url, build_payload, _parse_draft


def test_chat_url_normal():
    assert build_chat_url("https://api.deepseek.com") == "https://api.deepseek.com/chat/completions"
    assert build_chat_url("https://api.deepseek.com/") == "https://api.deepseek.com/chat/completions"


def test_chat_url_already_full():
    assert build_chat_url("https://api.deepseek.com/chat/completions") == "https://api.deepseek.com/chat/completions"


def test_payload_matches_deepseek_vision_contract():
    payload = build_payload("data:image/png;base64,AAAA", "deepseek-v4-flash-vision-exp")
    assert payload["model"] == "deepseek-v4-flash-vision-exp"
    assert len(payload["messages"]) == 1
    msg = payload["messages"][0]
    assert msg["role"] == "user"  # 图片只能在 user 消息，system/assistant 放图会 400
    content = msg["content"]
    assert isinstance(content, list)
    assert content[0] == {"type": "text", "text": content[0]["text"]}
    # 第二块是 image_url，携带 base64 data URL
    img = content[1]
    assert img["type"] == "image_url"
    assert img["image_url"]["url"] == "data:image/png;base64,AAAA"


def test_parse_draft_json_and_fenced():
    draft = _parse_draft('```json\n{"core_idea":"夹逼准则","steps":["判类型","代换","得结果"],"answer":"1","category":"proposition","number":"6.2.2"}\n```')
    assert draft["core_idea"] == "夹逼准则"
    assert draft["steps"] == ["判类型", "代换", "得结果"]
    assert draft["answer"] == "1"
    assert draft["category"] == "proposition"
    assert draft["number"] == "6.2.2"


def test_parse_draft_category_defaults_to_example():
    # 未标注定理/命题 → 兜底 example；编号需清洗
    draft = _parse_draft('{"core_idea":"x","steps":[],"category":"例题","number":"（5.1）"}')
    assert draft["category"] == "example"
    assert draft["number"] == "5.1"


def test_parse_draft_category_whitelist():
    # 未知/大写类别也归一为合法值或 example
    assert _parse_draft('{"steps":[],"category":"Theorem"}')["category"] == "theorem"
    assert _parse_draft('{"steps":[],"category":"weird"}')["category"] == "example"


def test_parse_draft_solve_type():
    assert _parse_draft('{"steps":[],"solve_type":"proof"}')["solve_type"] == "proof"
    assert _parse_draft('{"steps":[],"solve_type":"calculation"}')["solve_type"] == "calculation"
    # 未识别/非法 → 默认 calculation
    assert _parse_draft('{"steps":[],"solve_type":"判断"}')["solve_type"] == "calculation"
    assert _parse_draft('{"steps":[]}')["solve_type"] == "calculation"


def test_parse_chapter_section():
    from app.services.numbering import parse_chapter_section
    assert parse_chapter_section("6.2.2") == (6, 2)
    assert parse_chapter_section("5.1") == (5, 1)
    assert parse_chapter_section("例 5.1") == (5, 1)
    assert parse_chapter_section("5") == (5, None)
    assert parse_chapter_section("abc") == (None, None)
    assert parse_chapter_section("") == (None, None)
    assert parse_chapter_section(None) == (None, None)


def test_parse_draft_steps_as_text():
    draft = _parse_draft('{"steps":"第一步\\n第二步","core_idea":"x"}')
    assert draft["steps"] == ["第一步", "第二步"]


def test_parse_draft_plain_json():
    draft = _parse_draft('{"core_idea":"a","steps":[]}')
    assert draft["core_idea"] == "a"
    assert draft["steps"] == []
