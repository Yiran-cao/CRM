from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(10), nullable=False, default="dealer")  # admin / dealer
    dealer_name = Column(String(100), nullable=True)  # 经销商名称，admin 可为空
    failed_attempts = Column(Integer, nullable=False, default=0)  # 登录失败次数
    locked_until = Column(DateTime, nullable=True)  # 锁定截止时间

    projects = relationship("Project", back_populates="dealer")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String(100), nullable=False)
    province = Column(String(50), nullable=False)
    city = Column(String(50), nullable=False)
    product = Column(String(100), nullable=False)
    stage = Column(Integer, nullable=False, default=1)  # 1-6：潜在/初步/跟进/成交/忠诚/无效
    budget = Column(Float, nullable=True, default=0)
    department = Column(String(100), nullable=True)  # 主科室（冗余，便于列表展示）
    competitor_info = Column(Text, nullable=True)  # 竞争对手及障碍
    remark = Column(Text, nullable=True)  # 备注
    dealer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    version = Column(Integer, nullable=False, default=0)  # 乐观锁版本号
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    dealer = relationship("User", back_populates="projects")
    decision_makers = relationship("DecisionMaker", back_populates="project", cascade="all, delete-orphan")
    operation_logs = relationship("OperationLog", back_populates="project", cascade="all, delete-orphan")


class DecisionMaker(Base):
    """决策人表：一个项目可关联多个决策人（科室/负责人/联系方式）"""
    __tablename__ = "decision_makers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    department_name = Column(String(100), nullable=False)
    contact_name = Column(String(50), nullable=False)
    contact_info = Column(String(100), nullable=True)

    project = relationship("Project", back_populates="decision_makers")


class OperationLog(Base):
    """操作日志表：用于详情页时间线渲染"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    operator = Column(String(50), nullable=False)  # 操作人姓名
    operation_time = Column(DateTime, default=datetime.now)
    field_name = Column(String(50), nullable=False)  # 变更字段名（中文）
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    project = relationship("Project", back_populates="operation_logs")


class PointsLog(Base):
    __tablename__ = "points_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dealer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    period = Column(String(10), nullable=False)  # 如 2026-Q3
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    points_change = Column(Integer, nullable=False, default=1)
    operation_type = Column(String(20), nullable=False)  # 阶段更新 / 确认无变化
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class TokenBlacklist(Base):
    """JWT 黑名单：登出后使 token 失效"""
    __tablename__ = "token_blacklist"

    jti = Column(String(64), primary_key=True)  # JWT ID
    expires_at = Column(DateTime, nullable=False)  # token 过期时间，过期后可清理
