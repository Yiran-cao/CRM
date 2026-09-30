"""周期判断测试"""
from datetime import datetime
from utils import get_current_period, get_period_end


def test_current_period_format():
    """周期格式应为 YYYY-Qn"""
    period = get_current_period()
    parts = period.split("-Q")
    assert len(parts) == 2
    year, quarter = int(parts[0]), int(parts[1])
    assert 1 <= quarter <= 4
    assert 2020 <= year <= 2100


def test_current_period_matches_now():
    """周期应与当前年月对应"""
    now = datetime.now()
    period = get_current_period()
    expected_q = (now.month - 1) // 3 + 1
    assert period == f"{now.year}-Q{expected_q}"


def test_period_end_q1():
    """2026-Q1 截止应为 3月31日 23:59:59"""
    end = get_period_end("2026-Q1")
    assert end == datetime(2026, 3, 31, 23, 59, 59)


def test_period_end_q3():
    """2026-Q3 截止应为 9月30日 23:59:59"""
    end = get_period_end("2026-Q3")
    assert end == datetime(2026, 9, 30, 23, 59, 59)


def test_period_end_q4():
    """2026-Q4 截止应为 12月31日 23:59:59"""
    end = get_period_end("2026-Q4")
    assert end == datetime(2026, 12, 31, 23, 59, 59)


def test_period_end_q2_leap_year():
    """2024-Q2（闰年）截止应为 6月30日"""
    end = get_period_end("2024-Q2")
    assert end == datetime(2024, 6, 30, 23, 59, 59)
