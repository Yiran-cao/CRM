from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import get_db
from models import Project, User, PointsLog, DecisionMaker, OperationLog
from schemas import (
    ProjectCreate, ProjectUpdate, ProjectInfo, ProjectDetail,
    DecisionMakerInfo, OperationLogInfo,
)
from auth import get_current_user
from utils import get_current_period

router = APIRouter(prefix="/api/projects", tags=["项目管理"])

# 阶段名称（用于日志格式化）
STAGE_NAMES = {
    1: "潜在客户", 2: "初步接触",
    3: "持续跟进", 4: "成交客户",
    5: "忠诚客户", 6: "无效客户",
}

# 字段中文名映射
FIELD_NAMES = {
    "customer_name": "客户名称",
    "province": "省份",
    "city": "地区",
    "product": "产品",
    "stage": "阶段",
    "budget": "预算(万元)",
    "competitor_info": "竞争对手及障碍",
    "remark": "备注",
}


def format_field_value(field: str, value) -> str:
    """将字段值格式化为日志中的可读文本"""
    if value is None or value == "":
        return "（空）"
    if field == "stage":
        return f"阶段{value}-{STAGE_NAMES.get(value, '未知')}"
    if field == "budget":
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def get_project_or_404(db: Session, project_id: int, user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    if user.role != "admin" and project.dealer_id != user.id:
        raise HTTPException(status_code=403, detail="无权操作此项目")
    return project


def add_points(db: Session, project: Project, operation_type: str, description: str):
    """为项目所属经销商加 1 分"""
    period = get_current_period()
    db.add(PointsLog(
        dealer_id=project.dealer_id,
        period=period,
        project_id=project.id,
        points_change=1,
        operation_type=operation_type,
        description=description,
    ))


def add_operation_log(db: Session, project: Project, operator: str, field_name: str, old_value=None, new_value=None):
    """写入一条操作日志"""
    db.add(OperationLog(
        project_id=project.id,
        operator=operator,
        operation_time=datetime.now(),
        field_name=field_name,
        old_value="" if old_value is None else str(old_value),
        new_value="" if new_value is None else str(new_value),
    ))


def replace_decision_makers(db: Session, project: Project, makers: list):
    """替换项目的决策人列表（先删后增），并更新主科室冗余字段"""
    project.decision_makers.clear()
    for m in makers:
        db.add(DecisionMaker(
            project_id=project.id,
            department_name=m.department_name,
            contact_name=m.contact_name,
            contact_info=m.contact_info or "",
        ))
    project.department = makers[0].department_name if makers else ""


@router.get("")
def list_projects(
    customer_name: Optional[str] = Query(None, description="客户名称模糊搜索"),
    stage: Optional[int] = Query(None, description="阶段筛选"),
    province: Optional[str] = Query(None, description="省份筛选"),
    city: Optional[str] = Query(None, description="地区筛选"),
    year: Optional[int] = Query(None, description="年度筛选"),
    archived: bool = Query(False, description="是否查询往年结单项目"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Project)

    if current_user.role != "admin":
        query = query.filter(Project.dealer_id == current_user.id)

    if archived:
        query = query.filter(Project.stage == 6)
    else:
        query = query.filter(Project.stage != 6)

    if customer_name:
        query = query.filter(Project.customer_name.contains(customer_name))
    if stage is not None:
        query = query.filter(Project.stage == stage)
    if province:
        query = query.filter(Project.province == province)
    if city:
        query = query.filter(Project.city == city)
    if year:
        query = query.filter(
            Project.created_at >= datetime(year, 1, 1),
            Project.created_at < datetime(year + 1, 1, 1),
        )

    projects = query.order_by(Project.updated_at.desc()).all()

    result = []
    for p in projects:
        info = ProjectInfo.model_validate(p)
        info.dealer_name = p.dealer.name if p.dealer else ""
        result.append(info)

    return result


@router.post("", response_model=ProjectInfo)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.budget is not None and data.budget < 0:
        raise HTTPException(status_code=400, detail="预算不能为负数")

    project = Project(
        customer_name=data.customer_name,
        province=data.province,
        city=data.city,
        product=data.product,
        stage=data.stage,
        budget=data.budget or 0,
        competitor_info=data.competitor_info or "",
        remark=data.remark or "",
        dealer_id=current_user.id,
    )
    db.add(project)
    db.flush()  # 获取 project.id

    replace_decision_makers(db, project, data.decision_makers)
    add_operation_log(db, project, current_user.name, "创建", "", "")

    db.commit()
    db.refresh(project)
    info = ProjectInfo.model_validate(project)
    info.dealer_name = current_user.name
    return info


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_or_404(db, project_id, current_user)

    detail = ProjectDetail(
        id=project.id,
        customer_name=project.customer_name,
        province=project.province,
        city=project.city,
        product=project.product,
        stage=project.stage,
        budget=project.budget or 0,
        competitor_info=project.competitor_info or "",
        remark=project.remark or "",
        dealer_id=project.dealer_id,
        dealer_name=project.dealer.name if project.dealer else "",
        version=project.version or 0,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )
    detail.decision_makers = [
        DecisionMakerInfo.model_validate(m) for m in project.decision_makers
    ]
    detail.operation_logs = [
        OperationLogInfo.model_validate(log)
        for log in sorted(project.operation_logs, key=lambda x: x.operation_time)
    ]
    return detail


@router.put("/{project_id}", response_model=ProjectInfo)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 管理员默认只读，避免误改经销商数据
    if current_user.role == "admin":
        raise HTTPException(status_code=403, detail="管理员默认为只读，不可编辑项目")

    project = get_project_or_404(db, project_id, current_user)

    # 预算非负校验
    if data.budget is not None and data.budget < 0:
        raise HTTPException(status_code=400, detail="预算不能为负数")

    # 乐观锁：校验客户端版本号，防止旧数据覆盖新数据
    if data.version is not None and data.version != (project.version or 0):
        raise HTTPException(
            status_code=409,
            detail="数据已被他人修改，请刷新后重新编辑",
        )

    old_values = {
        "customer_name": project.customer_name,
        "province": project.province,
        "city": project.city,
        "product": project.product,
        "stage": project.stage,
        "budget": project.budget or 0,
        "competitor_info": project.competitor_info or "",
        "remark": project.remark or "",
    }

    update_data = data.model_dump(exclude_unset=True)
    changed_fields = []

    scalar_fields = ["customer_name", "province", "city", "product", "stage", "budget", "competitor_info", "remark"]
    for key in scalar_fields:
        if key in update_data and update_data[key] is not None:
            new_val = update_data[key]
            old_val = old_values[key]
            if str(new_val) != str(old_val):
                setattr(project, key, new_val)
                changed_fields.append(key)
                add_operation_log(
                    db, project, current_user.name,
                    FIELD_NAMES[key],
                    format_field_value(key, old_val),
                    format_field_value(key, new_val),
                )

    # 决策人变更
    if data.decision_makers is not None:
        old_makers_str = "；".join(
            f"{m.department_name}/{m.contact_name}/{m.contact_info or ''}"
            for m in project.decision_makers
        ) or "（空）"
        new_makers = data.decision_makers
        new_makers_str = "；".join(
            f"{m.department_name}/{m.contact_name}/{m.contact_info or ''}"
            for m in new_makers
        ) or "（空）"
        if old_makers_str != new_makers_str:
            replace_decision_makers(db, project, new_makers)
            changed_fields.append("decision_makers")
            add_operation_log(
                db, project, current_user.name,
                "决策人", old_makers_str, new_makers_str,
            )

    project.updated_at = datetime.now()
    project.version = (project.version or 0) + 1  # 版本号递增

    if changed_fields:
        desc = "、".join(FIELD_NAMES.get(f, "决策人") for f in changed_fields)
        add_points(db, project, "项目更新", f"更新：{project.customer_name}（{desc}）")

    db.commit()
    db.refresh(project)
    info = ProjectInfo.model_validate(project)
    info.dealer_name = project.dealer.name if project.dealer else ""
    return info


@router.post("/{project_id}/confirm")
def confirm_no_change(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """确认无变化：更新最后更新时间，计入积分并写操作日志"""
    if current_user.role == "admin":
        raise HTTPException(status_code=403, detail="管理员默认为只读，不可操作项目")

    project = get_project_or_404(db, project_id, current_user)
    project.updated_at = datetime.now()

    add_operation_log(db, project, current_user.name, "确认无变化", "", "")
    add_points(db, project, "确认无变化", f"确认无变化：{project.customer_name}")
    db.commit()

    period = get_current_period()
    total = (
        db.query(PointsLog)
        .filter(PointsLog.dealer_id == project.dealer_id, PointsLog.period == period)
        .count()
    )

    return {
        "message": "已确认无变化",
        "project_id": project_id,
        "period": period,
        "points_added": 1,
        "total_points": total,
    }
