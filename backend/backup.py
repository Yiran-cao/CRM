"""数据库备份脚本

用法：
    python backup.py            # 手动执行一次备份
    python backup.py --keep 30  # 指定保留最近 30 份备份（默认 30）

生产环境建议配置每日定时任务：
    - Linux:  crontab -e  添加  0 2 * * * cd /path/to/backend && python backup.py
    - Windows: 任务计划程序 → 新建任务 → 每日触发，程序填 python.exe，参数填 backup.py

备份文件存放在 backend/backups/ 目录，SQLite 为 .db 文件，PostgreSQL 为 .sql 文件。
"""
import os
import sys
import glob
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "backups"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./crm.db")


def backup_sqlite(keep: int):
    """SQLite：直接复制数据库文件"""
    # 数据库文件路径（相对 backend 目录）
    db_path = None
    if DATABASE_URL.startswith("sqlite:///"):
        rel = DATABASE_URL.replace("sqlite:///", "")
        db_path = BASE_DIR / rel
    if not db_path or not db_path.exists():
        print(f"[错误] 找不到 SQLite 数据库文件: {db_path}")
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"crm_{ts}.db"
    shutil.copy2(db_path, dest)
    print(f"[成功] SQLite 备份完成: {dest}")


def backup_postgres(keep: int):
    """PostgreSQL：使用 pg_dump 导出"""
    import subprocess
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"crm_{ts}.sql"
    # 从 DATABASE_URL 解析连接参数，用环境变量传递给 pg_dump
    env = os.environ.copy()
    result = subprocess.run(
        ["pg_dump", DATABASE_URL, "-f", str(dest)],
        env=env, capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"[成功] PostgreSQL 备份完成: {dest}")
    else:
        print(f"[错误] pg_dump 失败: {result.stderr}")


def cleanup_old(keep: int):
    """删除过期备份，仅保留最近 keep 份"""
    files = sorted(glob.glob(str(BACKUP_DIR / "crm_*")), reverse=True)
    for f in files[keep:]:
        os.remove(f)
        print(f"[清理] 删除旧备份: {f}")


def main():
    keep = 30
    if "--keep" in sys.argv:
        try:
            keep = int(sys.argv[sys.argv.index("--keep") + 1])
        except (IndexError, ValueError):
            pass

    BACKUP_DIR.mkdir(exist_ok=True)

    if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
        backup_postgres(keep)
    else:
        backup_sqlite(keep)

    cleanup_old(keep)


if __name__ == "__main__":
    main()
