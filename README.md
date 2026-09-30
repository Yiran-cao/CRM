# CRM 销售管理系统

面向医疗器械销售场景的客户关系管理系统，支持**管理员**与**经销商**两种角色，实现项目管理、季度积分考核、报表提交与全局考核管理。

## 技术栈

- **后端**：Python 3.9+ / FastAPI / SQLAlchemy
- **数据库**：SQLite（本地开发）/ PostgreSQL（云端部署）
- **前端**：Jinja2 模板 + 原生 JavaScript + CSS（无需 Node.js）
- **认证**：JWT Token
- **部署**：Docker / Render / Railway / 国内云服务器

## 目录结构与文件说明

```
d:\CRM\
├── CRM系统需求文档.md          # 原始需求文档
├── README.md                   # 本文件
├── 部署指南.md                 # 云端部署说明
├── render.yaml                 # Render 平台一键部署蓝图
├── .gitignore                  # Git 忽略配置
└── backend/                    # 后端应用根目录
    ├── main.py                 # 应用入口：页面路由 + 启动初始化（含演示数据种子）
    ├── database.py             # 数据库连接、建表、轻量迁移
    ├── models.py               # ORM 数据模型（用户/项目/决策人/操作日志/积分）
    ├── schemas.py              # Pydantic 请求/响应校验模型
    ├── auth.py                 # JWT 认证 + 密码哈希
    ├── utils.py                # 季度周期计算工具
    ├── requirements.txt        # Python 依赖清单
    ├── Dockerfile              # Docker 镜像构建文件
    ├── Procfile                # Railway/Heroku 启动命令
    ├── .dockerignore           # Docker 构建忽略清单
    ├── .env.example            # 环境变量模板
    ├── routers/                # API 路由层
    │   ├── auth.py             #   登录认证接口
    │   ├── projects.py         #   项目管理接口（增删改查/确认无变化/操作日志）
    │   ├── reports.py          #   报表提交与积分接口
    │   ├── dashboard.py        #   工作台统计接口
    │   └── admin.py            #   管理员接口（经销商管理/考核）
    ├── templates/              # Jinja2 页面模板
    │   ├── base.html           #   基础布局框架
    │   ├── sidebar.html        #   侧边栏导航组件
    │   ├── login.html          #   登录页
    │   ├── dashboard.html      #   工作台
    │   ├── projects.html       #   项目列表页
    │   ├── project_edit.html   #   项目新建/编辑页
    │   ├── project_detail.html #   项目详情页（含时间线）
    │   ├── reports.html        #   提交报表页
    │   └── admin_review.html   #   考核管理页（管理员）
    └── static/                 # 静态资源
        ├── css/style.css       #   全局样式
        └── js/
            ├── app.js          #   公共工具（请求/认证/阶段标签）
            ├── dashboard.js    #   工作台逻辑
            ├── projects.js     #   项目列表逻辑
            ├── project_edit.js #   编辑页逻辑
            ├── project_detail.js#  详情页逻辑
            ├── reports.js      #   报表逻辑
            └── admin.js        #   管理员逻辑
```

## 快速启动（本地开发）

> 注意：Windows 下如 `python` / `pip` 命令不可用，请改用 `py` 启动器（即 `py -3`）。

```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖（二选一）
py -3 -m pip install -r requirements.txt
# 或（若 python 命令可用）
# python -m pip install -r requirements.txt

# 3. 启动服务（二选一）
py -3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
# 或
# python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

访问 `http://127.0.0.1:8000` 即可打开登录页。

### 常见问题：无法访问网站

1. **`python` 命令提示找不到**：改用 `py -3`（Windows Python 启动器），例如 `py -3 -m uvicorn ...`
2. **`pip` 命令提示找不到**：改用 `py -3 -m pip install ...`
3. **服务未启动**：确认终端窗口保持运行（看到 `Uvicorn running on http://127.0.0.1:8000` 字样才算成功），关闭终端即停止服务
4. **端口被占用**：换一个端口，如 `--port 8001`，然后访问 `http://127.0.0.1:8001`
5. **找不到 uvicorn 模块**：先执行安装依赖命令（第 2 步）

## 使用说明

### 演示账号

| 角色 | 用户名 | 密码 | 说明 |
|---|---|---|---|
| 管理员 | `admin` | `admin123` | 查看全局项目、考核管理、创建经销商 |
| 经销商 | `dealer1` | `123456` | 陈静，管理自己的项目 |
| 经销商 | `dealer2` | `123456` | 张伟，管理自己的项目 |

> 首次部署后请立即修改管理员密码（通过 `ADMIN_PASSWORD` 环境变量或重建账号）。

### 功能导航

- **📋 工作台**：统计卡片（项目数/预测结单/已成交/无效客户/积分/周期/账号状态）
- **📁 项目管理**：项目列表、筛选、新建、编辑、详情、确认无变化
- **📝 提交报表**：积分状态、周期报表提交（积分 ≥ 5 才可提交）、积分历史
- **🔍 考核管理**（管理员）：经销商列表、查看各经销商项目与积分、新建经销商

### 6 个阶段定义

| 阶段 | 名称 | 颜色标签 |
|---|---|---|
| 1 | 潜在客户 | 蓝色 |
| 2 | 初步接触 | 蓝色 |
| 3 | 持续跟进 | 绿色 |
| 4 | 成交客户 | 绿色 |
| 5 | 忠诚客户 | 绿色 |
| 6 | 无效客户 | 红色 |

- 详情页状态标签：阶段 1-3 显示「跟进中」，4-5 显示「已成交」，6 显示「无效客户」
- 阶段 6（无效客户）为终态，自动归档到「往年结单项目」标签页

### 积分与周期规则

- 周期按季度自动计算，格式 `YYYY-Qn`（如 `2026-Q3`）
- 项目每完成一次**编辑保存**或**确认无变化**操作，积分 +1
- 一个周期内积分 **≥ 5 分** 才能提交该周期报表
- 积分不足时提交按钮置灰并提示

## 云端部署

详细步骤见 [部署指南.md](./部署指南.md)。核心要点：

1. 代码已支持 `DATABASE_URL` 环境变量（云端用 PostgreSQL，本地用 SQLite）
2. 通过 `Dockerfile` 一键构建，`render.yaml` 支持 Render 平台一键部署
3. 生产环境请设置环境变量：`SECRET_KEY`、`ADMIN_PASSWORD`、`DATABASE_URL`

## 环境变量

| 变量名 | 必填 | 说明 | 默认值 |
|---|---|---|---|
| `DATABASE_URL` | 云端必填 | 数据库连接串 | `sqlite:///./crm.db` |
| `SECRET_KEY` | 推荐 | JWT 签名密钥 | 开发默认值 |
| `ADMIN_PASSWORD` | 推荐 | 管理员初始密码 | `admin123` |
| `SEED_DEMO_DATA` | 可选 | 是否初始化演示数据 | `true` |
| `CORS_ORIGINS` | 可选 | 允许跨域域名 | `*` |
| `ACCESS_TOKEN_EXPIRE_HOURS` | 可选 | Token 有效期（小时） | `24` |
