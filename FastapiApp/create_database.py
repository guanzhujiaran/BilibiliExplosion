"""create_database.py — 用 ORM 模型的 metadata.create_all() 重建数据库并 stamp alembic head

基于 Alembic 官方 recipe:
  https://alembic.sqlalchemy.org/en/latest/cookbook.html#create-recreate-an-entire-database-from-orm-models

用途:
    1. 全新环境部署: 直接用 create_all() 建库，跳过所有历史迁移脚本
    2. 开发环境重置: --rebuild 先 drop_all 再 create_all（⚠ 会清空数据！）
    3. 日常增量迁移: lifespan 里的 run_alembic_migrations 仍负责已有数据库的增量更新

使用:
    python create_database.py                        # 对所有 6 个数据库执行 create_all（不删已有表）
    python create_database.py --rebuild              # 删除所有表后重新创建（⚠ DANGER! 清空全部数据）
    python create_database.py --db dyndetail --rebuild  # 只重建 dyndetail 数据库
    python create_database.py --db dyndetail         # 仅对 dyndetail 执行 create_all
"""
import argparse
import asyncio
import importlib
import os
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中，否则导入 CONFIG / Service 会失败
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from alembic.config import Config as AlembicConfig

from CONFIG import CONFIG as APP_CONFIG


# ---------------------------------------------------------------------------
# 数据库配置：与 alembic/env.py 保持一致（异步 aiomysql）
# ---------------------------------------------------------------------------

def _import_metadata(import_path: str):
    """动态导入指定模块路径中的 Base.metadata 对象。"""
    mod = importlib.import_module(import_path)
    return mod.Base.metadata


DATABASE_CONFIGS: dict[str, dict] = {
    "biliopusdb": {
        "url": APP_CONFIG.database.MYSQL.get_other_lot_URI,
        "base_import": "Service.GetOthersLotDyn.Sql.models",
        "version_dir": "biliopusdb",
        "description": "普通抽奖动态库 (t_lotdyninfo / t_lot_extra_info 等)",
    },
    "bilidb": {
        "url": APP_CONFIG.database.MYSQL.bili_db_URI,
        "base_import": "Service.opus新版官方抽奖.活动抽奖.话题抽奖.db.models",
        "version_dir": "bilidb",
        "description": "话题抽奖库 (t_topic / t_traffic_card 等)",
    },
    "bili_reserve": {
        "url": APP_CONFIG.database.MYSQL.bili_reserve_URI,
        "base_import": "Service.opus新版官方抽奖.预约抽奖.db.models",
        "version_dir": "bili_reserve",
        "description": "预约抽奖库 (t_up_reserve_relation_info 等)",
    },
    "dyndetail": {
        "url": APP_CONFIG.database.MYSQL.dyn_detail_URI,
        "base_import": "Service.GrpcModule.GrpcSrc.SQLObject.models",
        "version_dir": "dyndetail",
        "description": "动态详情库 (bilidyndetail / lotdata 等)",
    },
    "proxy_db": {
        "url": APP_CONFIG.database.MYSQL.proxy_db_URI,
        "base_import": "Utils.代理.数据库操作.SqlAlcheyObj.ProxyModel",
        "version_dir": "proxy_db",
        "description": "代理数据库 (proxy_tab / available_proxy)",
    },
    "samsclub": {
        "url": APP_CONFIG.database.MYSQL.sams_club_URI,
        "base_import": "Service.samsclub.Sql.models",
        "version_dir": "samsclub",
        "description": "山姆会员店数据库 (spu_info 等)",
    },
}


# ---------------------------------------------------------------------------
# 核心逻辑
# ---------------------------------------------------------------------------

def _get_alembic_config(db_name: str, version_dir: str) -> AlembicConfig:
    """获取指定数据库的 Alembic Config，使用 -n <section> 方式指定数据库。"""
    alembic_ini = _project_root / "alembic.ini"
    cfg = AlembicConfig(str(alembic_ini), ini_section=db_name)

    # 每个数据库有自己的 env.py，script_location 通过 alembic.ini 的 section 配置
    # 不需要手动设置 version_locations，env.py 会自动处理

    return cfg


def _stamp_head(db_name: str, version_dir: str):
    """stamp alembic head: 将 alembic_version 表标记为当前 migrations 目录的最新 revision"""
    cfg = _get_alembic_config(db_name, version_dir)
    command.stamp(cfg, "head")
    print(f"  [{db_name}] alembic stamp head 完成")


async def _create_or_drop_all(
    db_name: str,
    engine_url: str,
    metadata,
    rebuild: bool,
) -> None:
    """
    对指定数据库执行 create_all（或 drop_all + create_all）。

    Args:
        db_name: 数据库名称（仅用于日志）
        engine_url: 异步数据库 URL（aiomysql）
        metadata: SQLAlchemy MetaData 对象
        rebuild: 是否先 drop_all 再 create_all
    """
    engine = create_async_engine(engine_url)
    try:
        async with engine.connect() as connection:

            def _sync_inspect(sync_conn):
                return inspect(sync_conn).get_table_names()

            existing_tables = await connection.run_sync(_sync_inspect)

            if rebuild:
                if existing_tables:
                    print(f"  [{db_name}] ⚠ 正在删除 {len(existing_tables)} 张表...")

                    def _drop(sync_conn):
                        metadata.drop_all(sync_conn)

                    await connection.run_sync(_drop)
                    print(f"  [{db_name}] 已删除所有表")
                else:
                    print(f"  [{db_name}] 数据库为空，跳过 drop_all")

            # create_all：只创建不存在的表，不会修改已有表的结构
            print(f"  [{db_name}] 正在根据 ORM 模型创建表...")

            def _create(sync_conn):
                metadata.create_all(sync_conn)

            await connection.run_sync(_create)

            # 验证并报告
            after_tables = await connection.run_sync(_sync_inspect)
            print(f"  [{db_name}] 完成！当前共 {len(after_tables)} 张表:")
            for t in sorted(after_tables):

                def _get_cols(sync_conn, table=t):
                    return [c["name"] for c in inspect(sync_conn).get_columns(table)]

                cols = await connection.run_sync(_get_cols)
                print(f"    - {t} ({len(cols)} 列: {', '.join(cols[:8])}"
                      f"{'...' if len(cols) > 8 else ''})")
    finally:
        await engine.dispose()


async def process_database(db_name: str, db_config: dict, rebuild: bool) -> None:
    """处理单个数据库：create_all + stamp head。"""
    print(f"\n{'=' * 60}")
    print(f"处理数据库: {db_name} ({db_config['description']})")
    print(f"{'=' * 60}")

    url = db_config["url"]
    # 隐藏密码显示
    display_url = url[:url.find("@")] + "@***" if "@" in url else url
    print(f"  URL: {display_url}")

    try:
        # 1. 导入模型的 metadata
        metadata = _import_metadata(db_config["base_import"])

        # 2. create_all（或 drop_all + create_all）（异步）
        await _create_or_drop_all(db_name, url, metadata, rebuild=rebuild)

        # 3. stamp head
        _stamp_head(db_name, db_config["version_dir"])

        print(f"  [{db_name}] ✅ 处理完成")
    except Exception as e:
        print(f"  [{db_name}] ❌ 处理失败: {e}")
        raise


async def async_main(args_db: str | None, rebuild: bool):
    db_names = [args_db] if args_db else list(DATABASE_CONFIGS.keys())
    failed: list[str] = []

    for db_name in db_names:
        try:
            await process_database(db_name, DATABASE_CONFIGS[db_name], rebuild=rebuild)
        except Exception:
            failed.append(db_name)

    print(f"\n{'=' * 60}")
    if failed:
        print(f"❌ 以下数据库处理失败: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("✅ 所有数据库处理完成！")
        print()
        print("提示:")
        print("  - 全新数据库已通过 create_all() 创建完毕")
        print("  - alembic_version 表已 stamp head")
        print("  - 后续修改模型后，使用 make alembic-auto DB=<section> MSG='描述' 生成增量迁移")
        print("  - 或手动：alembic -c alembic.ini -n <section> revision --autogenerate -m '描述'")
        print("  - lifespan 启动时会自动执行 upgrade head 和 schema 一致性校验")


def main():
    parser = argparse.ArgumentParser(
        description="用 ORM 模型的 metadata.create_all() 创建/重建数据库，并 stamp alembic head",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python create_database.py                          # 对所有 DB 执行 create_all（已有表不重复创建）
  python create_database.py --rebuild                # ⚠ DROP ALL TABLES，然后重新 create_all
  python create_database.py --db dyndetail           # 仅处理 dyndetail
  python create_database.py --db dyndetail --rebuild # ⚠ 删除 dyndetail 所有表后重建
        """,
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="⚠ 先 drop_all 删除所有表，再 create_all（会清空数据！）",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        choices=list(DATABASE_CONFIGS.keys()),
        help="仅处理指定数据库（默认处理全部 6 个）",
    )
    args = parser.parse_args()

    if args.rebuild:
        print("=" * 60)
        print("⚠⚠⚠  警告：--rebuild 模式将删除所有表并重新创建！ ⚠⚠⚠")
        print("⚠⚠⚠  所有数据将被清空！                           ⚠⚠⚠")
        print("=" * 60)
        if os.environ.get("CI") or os.environ.get("FORCE"):
            print("  检测到 CI/FORCE 环境变量，自动确认...")
        else:
            confirm = input("  确认继续？输入 'yes' 继续: ")
            if confirm.strip().lower() != "yes":
                print("  已取消")
                return

    asyncio.run(async_main(args.db, args.rebuild))
