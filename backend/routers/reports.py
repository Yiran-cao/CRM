from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import PointsLog, User
from schemas import PointsLogInfo, SubmitReportRequest
from auth import get_current_user
from utils import get_current_period, get_period_end

router = APIRouter(prefix="/api/reports", tags=["报表"])


@router.get("/status")
def get_report_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前报表状态：积分、周期、截止日期"""
    period = get_current_period()

    # 计算当前周期积分
    points = (
        db.query(PointsLog)
        .filter(
            PointsLog.dealer_id == current_user.id,
            PointsLog.period == period,
        )
        .all()
    )
    total_points = sum(p.points_change for p in points)

    # 检查是否已提交
    submitted = any(p.operation_type == "提交报表" for p in points)

    if submitted:
        status_text = "已提交"
        can_submit = False
    elif total_points >= 5:
        status_text = "正常（可提交）"
        can_submit = True
    else:
        status_text = "积分不足"
        can_submit = False

    return {
        "period": period,
        "total_points": total_points,
        "can_submit": can_submit,
        "submitted": submitted,
        "deadline": get_period_end(period).isoformat(),
        "status": status_text,
    }


@router.get("/history")
def get_points_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取积分历史"""
    logs = (
        db.query(PointsLog)
        .filter(PointsLog.dealer_id == current_user.id)
        .order_by(PointsLog.created_at.desc())
        .all()
    )
    return [PointsLogInfo.model_validate(log) for log in logs]


@router.post("/submit")
def submit_report(
    data: SubmitReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交周期报表"""
    period = get_current_period()

    # 检查是否已提交过本周期
    existing = (
        db.query(PointsLog)
        .filter(
            PointsLog.dealer_id == current_user.id,
            PointsLog.period == period,
            PointsLog.operation_type == "提交报表",
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"周期 {period} 已提交过报表，无需重复提交",
        )

    # 检查积分是否达标
    points = (
        db.query(PointsLog)
        .filter(
            PointsLog.dealer_id == current_user.id,
            PointsLog.period == period,
        )
        .all()
    )
    total_points = sum(p.points_change for p in points)

    if total_points < 5:
        raise HTTPException(
            status_code=400,
            detail=f"当前积分：{total_points} 分，需要至少 5 分才能提交",
        )

    # 创建提交记录
    log = PointsLog(
        dealer_id=current_user.id,
        period=period,
        points_change=0,
        operation_type="提交报表",
        description=f"周期报表提交，当期积分{total_points}分",
    )
    db.add(log)
    db.commit()

    return {
        "message": "报表提交成功",
        "period": period,
        "total_points": total_points,
        "submitted_at": log.created_at.isoformat(),
    }
