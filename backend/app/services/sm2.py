"""SM-2 间隔重复算法。对应文档 03 §4.3、文档 07 §3。

简化版 SM-2：评分 rating ∈ {again, hard, good, easy}。
返回更新后的 (repetitions, interval, ease_factor, status, due_date)。
"""
from datetime import datetime, timedelta, timezone

# 各评分对应的质量因子（SM-2 的 q，0~5）
_RATING_Q = {"again": 1, "hard": 3, "good": 4, "easy": 5}

_EASY_BONUS = 1.3  # easy 提升 EF 的额外系数


def sm2_update(repetitions: int, interval_days: int, ease_factor: float, rating: str) -> tuple[int, int, float, str, datetime]:
    """根据评分更新卡片调度状态。

    返回 (new_repetitions, new_interval, new_ease_factor, new_status, new_due_date)。
    输入 assume 为 UTC 时间语义，date 计算基于当前 UTC。
    """
    q = _RATING_Q.get(rating, 4)
    now = datetime.now(timezone.utc)

    # 1) 更新 ease factor（SM-2 公式）
    # EF' = EF + (0.1 - (5-q)*(0.08+(5-q)*0.02)); 下限 1.3
    ef = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    if rating == "easy":
        ef += _EASY_BONUS - 0.1  # 简单略放大
    ef = max(1.3, ef)

    # 2) 更新重复次数与间隔
    if q < 3:  # again / hard 算作失败
        repetitions = 0
        interval_days = 1
        status = "learning"
    else:
        repetitions += 1
        if repetitions == 1:
            interval_days = 1
        elif repetitions == 2:
            interval_days = 6
        else:
            interval_days = round(interval_days * ef)
        status = "reviewing"

    due = now + timedelta(days=interval_days)
    return repetitions, interval_days, round(ef, 2), status, due
