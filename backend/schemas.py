from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ===== 用户相关 =====
class UserLogin(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    id: int
    name: str
    username: str
    role: str
    dealer_name: Optional[str] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


# ===== 决策人 =====
class DecisionMakerInfo(BaseModel):
    id: Optional[int] = None
    department_name: str
    contact_name: str
    contact_info: Optional[str] = ""

    class Config:
        from_attributes = True


# ===== 操作日志 =====
class OperationLogInfo(BaseModel):
    id: int
    operator: str
    operation_time: datetime
    field_name: str
    old_value: Optional[str] = ""
    new_value: Optional[str] = ""

    class Config:
        from_attributes = True


# ===== 项目相关 =====
class ProjectCreate(BaseModel):
    customer_name: str
    province: str
    city: str
    product: str
    stage: int = 1
    budget: Optional[float] = 0
    competitor_info: Optional[str] = ""
    remark: Optional[str] = ""
    decision_makers: List[DecisionMakerInfo] = []


class ProjectUpdate(BaseModel):
    customer_name: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    product: Optional[str] = None
    stage: Optional[int] = None
    budget: Optional[float] = None
    competitor_info: Optional[str] = None
    remark: Optional[str] = None
    decision_makers: Optional[List[DecisionMakerInfo]] = None
    version: Optional[int] = None  # 乐观锁：客户端加载时的版本号


class ProjectInfo(BaseModel):
    id: int
    customer_name: str
    province: str
    city: str
    product: str
    stage: int
    budget: Optional[float] = 0
    competitor_info: Optional[str] = ""
    remark: Optional[str] = ""
    dealer_id: int
    dealer_name: Optional[str] = ""
    version: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectDetail(ProjectInfo):
    decision_makers: List[DecisionMakerInfo] = []
    operation_logs: List[OperationLogInfo] = []


# ===== 积分相关 =====
class PointsLogInfo(BaseModel):
    id: int
    dealer_id: int
    period: str
    project_id: Optional[int] = None
    points_change: int
    operation_type: str
    description: Optional[str] = ""
    created_at: datetime

    class Config:
        from_attributes = True


class SubmitReportRequest(BaseModel):
    pass  # 提交报表无需额外参数，由后端根据当前周期自动处理
