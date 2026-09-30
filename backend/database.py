import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 加载 .env（本地开发用），云端环境变量优先
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 数据库连接：默认 SQLite。数据目录可通过 DATA_DIR 环境变量指定，
# 便于 Docker 部署时把数据库文件映射到宿主机持久化目录。
DATA_DIR = os.getenv("DATA_DIR", str(Path(__file__).resolve().parent))
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE = f"sqlite:///{Path(DATA_DIR) / 'crm.db'}"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE)

# 兼容部分平台提供的 postgres:// 前缀（SQLAlchemy 需要 postgresql://）
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("postgresql://"):
    # PostgreSQL：配置连接池
    pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=1800,  # 30分钟回收连接，避免数据库端超时断连
    )
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    # 轻量迁移：为已存在的 projects 表补充新字段（SQLite / PostgreSQL 均兼容）
    _migrate()


def _migrate():
    """为旧库补充新增列，避免重复开发时手动删库"""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "projects" not in tables:
        return
    existing_cols = {c["name"] for c in inspector.get_columns("projects")}
    additions = {
        "competitor_info": "TEXT",
        "remark": "TEXT",
        "version": "INTEGER DEFAULT 0",
    }
    for col, ctype in additions.items():
        if col not in existing_cols:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE projects ADD COLUMN {col} {ctype}"))
    # users 表补充登录锁定字段
    if "users" in tables:
        user_cols = {c["name"] for c in inspector.get_columns("users")}
        user_additions = {
            "failed_attempts": "INTEGER DEFAULT 0",
            "locked_until": "DATETIME",
        }
        for col, ctype in user_additions.items():
            if col not in user_cols:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {ctype}"))
    # 阶段从10级迁移到6级（7→3持续跟进, 8→4成交, 9→5忠诚, 10→6无效）
    stage_map = {7: 3, 8: 4, 9: 5, 10: 6}
    for old_stage, new_stage in stage_map.items():
        with engine.begin() as conn:
            conn.execute(text(f"UPDATE projects SET stage={new_stage} WHERE stage={old_stage}"))
