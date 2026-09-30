from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Project, PointsLog
from auth import get_current_user, require_admin, hash_password, validate_password_strength
from utils import get_current_period
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["管理员"])


class CreateDealerRequest(BaseModel):
    name: str
    username: str
    password: str
    dealer_name: str


@router.get("/dealers")
def list_dealers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """管理员查看所有经销商列表（含统计）"""
    period = get_current_period()
    dealers = db.query(User).filter(User.role == "dealer").all()
    result = []
    for d in dealers:
        # 项目统计（6阶段：1-5活跃，6无效）
        total = len([p for p in d.projects if p.stage != 6])
        delivered = len([p for p in d.projects if p.stage in [4, 5]])
        lost = len([p for p in d.projects if p.stage == 6])
        # 当前周期积分
        points = (
            db.query(PointsLog)
            .filter(PointsLog.dealer_id == d.id, PointsLog.period == period)
            .all()
        )
        total_points = sum(p.points_change for p in points)
        submitted = any(p.operation_type == "提交报表" for p in points)

        result.append({
            "id": d.id,
            "name": d.name,
            "username": d.username,
            "dealer_name": d.dealer_name,
            "project_count": total,
            "delivered_count": delivered,
            "lost_count": lost,
            "current_points": total_points,
            "period": period,
            "submitted": submitted,
        })
    return result


@router.post("/dealers")
def create_dealer(
    data: CreateDealerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """管理员创建经销商账户"""
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    # 密码复杂度校验
    err = validate_password_strength(data.password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    dealer = User(
        name=data.name,
        username=data.username,
        password_hash=hash_password(data.password),
        role="dealer",
        dealer_name=data.dealer_name,
    )
    db.add(dealer)
    db.commit()
    db.refresh(dealer)
    return {"id": dealer.id, "name": dealer.name, "username": dealer.username, "dealer_name": dealer.dealer_name}


@router.get("/dealer/{dealer_id}/projects")
def get_dealer_projects(
    dealer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """管理员查看指定经销商的项目"""
    projects = (
        db.query(Project)
        .filter(Project.dealer_id == dealer_id)
        .order_by(Project.updated_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "customer_name": p.customer_name,
            "province": p.province,
            "city": p.city,
            "product": p.product,
            "stage": p.stage,
            "budget": p.budget,
            "department": p.department,
            "updated_at": p.updated_at.isoformat(),
        }
        for p in projects
    ]


@router.get("/dealer/{dealer_id}/points")
def get_dealer_points(
    dealer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """管理员查看指定经销商的积分"""
    logs = (
        db.query(PointsLog)
        .filter(PointsLog.dealer_id == dealer_id)
        .order_by(PointsLog.created_at.desc())
        .all()
    )
    return [
        {
            "id": l.id,
            "period": l.period,
            "points_change": l.points_change,
            "operation_type": l.operation_type,
            "description": l.description,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
