"""刷题判分逻辑。对应文档 04 §7、文档 07 TC-QUIZ。
题型改为 计算/证明 后，不再自动判分：由用户自评「我答对/我答错」（self_correct）。
"""
from ..models import Question


def judge(q: Question, user_answer: str | None, self_correct: bool | None = None) -> bool:
    """计算/证明题由用户自评对错；无自评则保守返回 False。"""
    return bool(self_correct)
