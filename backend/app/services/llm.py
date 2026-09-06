"""从题目图片提取「核心思路 + 简明操作步骤」的初稿。

调用一个 OpenAI 兼容的 chat completions 接口（支持 image_url 内容块）。已按
DeepSeek-V4-Flash-Vision-Exp 官方「图像理解」契约实现：base64 内联图片只放在
user 消息（system/assistant 放图会返回 400），model 必须是支持图片的视觉模型。

若未配置 LLM_API_KEY，则抛出可读的 400（ERR_LLM_NOT_CONFIGURED），提示用户配置或手动填写。
对应目标功能「图片提取初稿」。
"""
import base64
import json
import re

import httpx
from fastapi import UploadFile

from ..core.config import settings
from ..core.errors import AppError

_PROMPT = (
    "你是数学学硕备考的教学助手。请阅读这道数学题（图片），提取：\n"
    "1) core_idea：这道题的核心思路（一句话，说明考什么、用什么方法）。\n"
    "2) steps：简明操作步骤（有序列表，3~6 步，逐步清晰）。\n"
    "3) content：把题目转成可读的文本题干（含 LaTeX 用 $...$）。\n"
    "4) answer：最终答案（若是判断题填 对/错；单选/多选填选项字母如 B；主观题给参考答案）。\n"
    "5) explanation：简要解析。\n"
    "6) category：判断这内容的类别——标注为「定理」填 theorem，标注为「命题」填 proposition，"
    "否则（包括「例题」或没有任何标注）填 example。\n"
    "7) number：标注里的编号（如 6.2.2、5.1、3.1），没有编号则填空字符串。\n"
    "8) solve_type：判断这题属于「计算」还是「证明」——需要算出数值/表达式结果为 calculation，"
    "需要推导/逻辑论证为 proof。只填 calculation 或 proof。\n"
    "只输出 JSON，格式：{\"content\":\"...\",\"core_idea\":\"...\",\"steps\":[\"...\"],"
    "\"answer\":\"...\",\"explanation\":\"...\",\"category\":\"example\",\"number\":\"\","
    "\"solve_type\":\"calculation\"}"
)


def _data_url(image: UploadFile) -> str:
    data = image.file.read()
    mime = image.content_type or "image/png"
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def build_chat_url(base_url: str) -> str:
    """构造 chat completions 地址；兼容 base 已带 /chat/completions 的情况。"""
    base = (base_url or settings.llm_base_url).rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return base + "/chat/completions"


def build_payload(b64_data_url: str, model: str, prompt: str = _PROMPT) -> dict:
    """构造符合 OpenAI/DeepSeek 视觉契约的请求体。图片仅放入 user 消息。"""
    return {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": b64_data_url}},
                ],
            }
        ],
    }


def _clean_step(s: str) -> str:
    """去掉模型输出步骤开头的编号（如 '1. '、'2、'、'3：'），避免与前端列表编号重复。"""
    return re.sub(r"^\s*\d+[.、)）:：]\s*", "", s).strip()


def _clean_number(s: object) -> str:
    """清洗编号：去空白、去外层成对括号（如 （6.2.2）、[5.1]）、去尾部冒号。"""
    if not s:
        return ""
    text = str(s).strip()
    text = text.strip("[]()（）【】")
    text = text.strip(" :：")
    return text


def _normalize_category(cat: object) -> str:
    """归类兜底：仅接受 theorem/proposition/example，否则一律归 example（无标注归例题）。"""
    text = str(cat or "").strip().lower()
    return text if text in ("theorem", "proposition", "example") else "example"


def _normalize_solve_type(v: object) -> str:
    """题型兜底：仅接受 calculation/proof，否则默认 calculation（计算）。"""
    text = str(v or "calculation").strip().lower()
    return text if text in ("calculation", "proof") else "calculation"


def _parse_draft(text: str) -> dict:
    """从 LLM 文本中尽量解析出 JSON 初稿。"""
    text = text.strip()
    # 剥离可能的 ```json ... ```
    if "```" in text:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
        if m:
            text = m.group(1)
    # 找到第一个 { 到最后一个 }
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end + 1]
    data = json.loads(text)
    steps = data.get("steps") or []
    if isinstance(steps, str):
        steps = [s.strip() for s in steps.splitlines() if s.strip()]
    steps = [_clean_step(s) for s in steps]
    return {
        "content": data.get("content"),
        "core_idea": data.get("core_idea", ""),
        "steps": steps,
        "answer": data.get("answer"),
        "explanation": data.get("explanation"),
        "category": _normalize_category(data.get("category")),
        "number": _clean_number(data.get("number")),
        "solve_type": _normalize_solve_type(data.get("solve_type")),
    }


async def extract_from_image(image: UploadFile) -> dict:
    """调用视觉接口，返回初稿 {core_idea, steps, content, answer, explanation}。"""
    if not settings.llm_api_key:
        raise AppError(
            400,
            "尚未配置 LLM_API_KEY（后端 .env）。未启用自动提取，可先手动填写，"
            "或配置后重试（用 DeepSeek 视觉模型请设 LLM_MODEL=deepseek-v4-flash-vision-exp）。",
            code="ERR_LLM_NOT_CONFIGURED",
        )
    url = build_chat_url(settings.llm_base_url)
    payload = build_payload(_data_url(image), settings.llm_model)
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        raise AppError(
            502,
            f"AI 提取失败（HTTP {resp.status_code}）：{resp.text[:300]}",
            code="ERR_LLM_FAILED",
        )
    data = resp.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise AppError(502, "AI 返回格式异常", code="ERR_LLM_FAILED")
    return _parse_draft(text)
