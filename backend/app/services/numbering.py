"""编号 → 章节(章/节) 解析。对应「题目分章节」功能。

示例：
- "6.2.2"   → (6, 2)   第6章 第2节（第3段为题目序号，忽略）
- "5.1"     → (5, 1)   第5章 第1节
- "5"       → (5, None) 第5章（无节）
- "例 5.1"  → (5, 1)   提取首个数字串
- 无法解析   → (None, None) 归「未分章」
"""
import re


def parse_chapter_section(number: str | None) -> tuple[int | None, int | None]:
    """从编号尽力解析出 (章, 节)。不能解析时返回 (None, None)。"""
    if not number:
        return None, None
    text = str(number).strip()
    m = re.search(r"(\d+)\s*[.\u3001、-]\s*(\d+)", text)
    if m:
        return int(m.group(1)), int(m.group(2))
    m2 = re.search(r"(\d+)", text)
    if m2:
        return int(m2.group(1)), None
    return None, None
