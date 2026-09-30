"""共享工具函数"""
from datetime import datetime
import calendar


def get_current_period() -> str:
    """根据当前日期计算所属周期，如 2026-Q3"""
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    return f"{now.year}-Q{quarter}"


def get_period_end(period: str) -> datetime:
    """获取周期截止日期（最后一天 23:59:59）"""
    year_str, q_str = period.split("-Q")
    year, quarter = int(year_str), int(q_str)
    last_month = quarter * 3
    last_day = calendar.monthrange(year, last_month)[1]
    return datetime(year, last_month, last_day, 23, 59, 59)
