"""SM-2 算法单元测试。对应文档 07 §3、文档 06 T-5.2。"""
from app.services.sm2 import sm2_update


def test_good_first_review():
    reps, interval, ef, status, due = sm2_update(0, 0, 2.5, "good")
    assert reps == 1
    assert interval == 1
    assert ef >= 2.5
    assert status == "reviewing"


def test_again_resets_repetitions():
    reps, interval, ef, status, _ = sm2_update(3, 20, 2.6, "again")
    assert reps == 0
    assert interval == 1
    assert status == "learning"
    assert ef < 2.6


def test_second_good_interval_six_days():
    reps, interval, ef, _, _ = sm2_update(1, 1, 2.5, "good")
    assert reps == 2
    assert interval == 6


def test_interval_grows_with_ef():
    reps, interval, ef, _, _ = sm2_update(2, 6, 2.6, "good")
    assert reps == 3
    assert interval == round(6 * ef)


def test_easy_increases_ef_more():
    _, _, ef_good, _, _ = sm2_update(0, 0, 2.5, "good")
    _, _, ef_easy, _, _ = sm2_update(0, 0, 2.5, "easy")
    assert ef_easy >= ef_good


def test_ef_floor():
    _, _, ef, _, _ = sm2_update(0, 0, 1.0, "again")
    assert ef >= 1.3
