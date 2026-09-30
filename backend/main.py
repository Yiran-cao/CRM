import os
from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from database import init_db
from models import User, Project
from auth import hash_password, get_current_user

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="CRM 销售管理系统", version="1.0.0")

# 静态文件 & 模板
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# CORS 跨域配置：默认不开放跨域（本系统前后端同源），生产环境仅在确需分离部署时
# 通过 CORS_ORIGINS 环境变量显式指定允许的前端域名，如 "https://crm.example.com"
cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins if o.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
from routers.auth import router as auth_router
from routers.projects import router as projects_router
from routers.reports import router as reports_router
from routers.admin import router as admin_router
from routers.dashboard import router as dashboard_router

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(reports_router)
app.include_router(admin_router)
app.include_router(dashboard_router)


# ========== 页面路由 ==========

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/projects")
def projects_page(request: Request):
    return templates.TemplateResponse("projects.html", {"request": request})


@app.get("/projects/new")
def project_new_page(request: Request):
    return templates.TemplateResponse("project_edit.html", {"request": request})


@app.get("/projects/{project_id}")
def project_detail_page(project_id: int, request: Request):
    return templates.TemplateResponse("project_detail.html", {"request": request})


@app.get("/projects/{project_id}/edit")
def project_edit_page(project_id: int, request: Request):
    return templates.TemplateResponse("project_edit.html", {"request": request})


@app.get("/reports")
def reports_page(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})


@app.get("/admin/review")
def admin_review_page(request: Request):
    return templates.TemplateResponse("admin_review.html", {"request": request})


@app.get("/")
def root():
    return RedirectResponse(url="/login")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def startup():
    # 生产环境安全校验：密钥/管理员密码不得使用默认值
    if os.getenv("ENVIRONMENT", "").lower() == "production":
        from auth import SECRET_KEY
        if SECRET_KEY == "crm-secret-key-change-in-production":
            raise RuntimeError("生产环境必须通过环境变量设置强 SECRET_KEY")
        if os.getenv("ADMIN_PASSWORD", "admin123") == "admin123":
            raise RuntimeError("生产环境必须通过 ADMIN_PASSWORD 设置非默认管理员密码")

    init_db()
    from database import SessionLocal
    db = SessionLocal()
    try:
        # 管理员账号始终创建，密码通过 ADMIN_PASSWORD 环境变量配置（默认 admin123）
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(
                name="系统管理员", username="admin",
                password_hash=hash_password(admin_password),
                role="admin", dealer_name=None,
            ))
            db.commit()

        # 演示数据默认开启，生产环境可设置 SEED_DEMO_DATA=false 关闭
        if os.getenv("SEED_DEMO_DATA", "true").lower() != "false":
            _seed_demo_data(db)
    finally:
        db.close()


def _seed_demo_data(db):
    """初始化演示经销商和演示项目"""
    if not db.query(User).filter(User.username == "dealer1").first():
        db.add(User(
            name="陈静", username="dealer1",
            password_hash=hash_password("123456"),
            role="dealer", dealer_name="陈静医疗器械有限公司",
        ))
    if not db.query(User).filter(User.username == "dealer2").first():
        db.add(User(
            name="张伟", username="dealer2",
            password_hash=hash_password("123456"),
            role="dealer", dealer_name="伟达医疗科技有限公司",
        ))
    db.commit()

    # 演示项目（仅在无项目时创建）
    if db.query(Project).count() == 0:
        dealer1 = db.query(User).filter(User.username == "dealer1").first()
        dealer2 = db.query(User).filter(User.username == "dealer2").first()
        demo_projects = [
            Project(customer_name="北京协和医院", province="北京", city="东城区", product="CT-128排", stage=4, budget=850, department="影像科", dealer_id=dealer1.id, created_at=datetime(2026,1,15), updated_at=datetime(2026,7,20)),
            Project(customer_name="上海瑞金医院", province="上海", city="黄浦区", product="MRI-3.0T", stage=5, budget=1200, department="影像科", dealer_id=dealer1.id, created_at=datetime(2025,6,10), updated_at=datetime(2026,3,15)),
            Project(customer_name="广东省人民医院", province="广东", city="广州", product="DSA血管造影机", stage=3, budget=680, department="心内科", dealer_id=dealer1.id, created_at=datetime(2026,2,20), updated_at=datetime(2026,8,1)),
            Project(customer_name="杭州第一人民医院", province="浙江", city="杭州", product="超声诊断仪", stage=3, budget=320, department="超声科", dealer_id=dealer1.id, created_at=datetime(2026,4,10), updated_at=datetime(2026,7,28)),
            Project(customer_name="南京鼓楼医院", province="江苏", city="南京", product="DR数字X光机", stage=2, budget=180, department="影像科", dealer_id=dealer1.id, created_at=datetime(2026,5,1), updated_at=datetime(2026,8,5)),
            Project(customer_name="成都华西医院", province="四川", city="成都", product="PET-CT", stage=3, budget=1500, department="核医学科", dealer_id=dealer2.id, created_at=datetime(2026,3,8), updated_at=datetime(2026,7,15)),
            Project(customer_name="武汉同济医院", province="湖北", city="武汉", product="C臂X光机", stage=6, budget=420, department="骨科", dealer_id=dealer2.id, created_at=datetime(2025,8,12), updated_at=datetime(2026,1,20)),
            Project(customer_name="济南齐鲁医院", province="山东", city="济南", product="内窥镜系统", stage=3, budget=560, department="消化科", dealer_id=dealer2.id, created_at=datetime(2026,1,5), updated_at=datetime(2026,8,8)),
            Project(customer_name="长沙湘雅医院", province="湖南", city="长沙", product="监护仪", stage=4, budget=95, department="ICU", dealer_id=dealer2.id, created_at=datetime(2026,6,18), updated_at=datetime(2026,8,10)),
            Project(customer_name="郑州大学一附院", province="河南", city="郑州", product="呼吸机", stage=1, budget=75, department="呼吸科", dealer_id=dealer2.id, created_at=datetime(2026,7,22), updated_at=datetime(2026,8,11)),
        ]
        db.add_all(demo_projects)
        db.commit()
