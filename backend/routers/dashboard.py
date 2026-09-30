"""工作台仪表盘 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Project, User, PointsLog
from auth import get_current_user
from utils import get_current_period

router = APIRouter(prefix="/api/dashboard", tags=["工作台"])


@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取工作台统计数据"""
    now = datetime.now()
    current_year = now.year
    period = get_current_period()

    # 基础查询：经销商只看自己的，管理员看全部
    base_query = db.query(Project)
    if current_user.role != "admin":
        base_query = base_query.filter(Project.dealer_id == current_user.id)

    # 1. 我的项目（总数，不含终态无效客户）
    total_projects = base_query.filter(Project.stage != 6).count()

    # 2. 预测结单（阶段3-持续跟进）
    predicted = base_query.filter(Project.stage == 3).count()

    # 3. 本年度已成交（阶段4成交客户/5忠诚客户，按年度）
    delivered = base_query.filter(
        Project.stage.in_([4, 5]),
        Project.updated_at >= datetime(current_year, 1, 1),
        Project.updated_at < datetime(current_year + 1, 1, 1),
    ).count()

    # 4. 本年度无效客户（阶段6，按年度）
    lost = base_query.filter(
        Project.stage == 6,
        Project.updated_at >= datetime(current_year, 1, 1),
        Project.updated_at < datetime(current_year + 1, 1, 1),
    ).count()

    # 5. 当期积分
    points_query = db.query(PointsLog).filter(
        PointsLog.dealer_id == current_user.id,
        PointsLog.period == period,
    )
    points = points_query.all()
    total_points = sum(p.points_change for p in points)

    # 6. 账号状态
    submitted = any(p.operation_type == "提交报表" for p in points)
    if submitted:
        account_status = "已提交"
        status_color = "green"
    elif total_points >= 5:
        account_status = "正常"
        status_color = "green"
    elif total_points > 0:
        account_status = "积分不足"
        status_color = "orange"
    else:
        account_status = "待活跃"
        status_color = "gray"

    return {
        "total_projects": total_projects,
        "predicted": predicted,
        "delivered": delivered,
        "lost": lost,
        "total_points": total_points,
        "period": period,
        "account_status": account_status,
        "status_color": status_color,
    }
