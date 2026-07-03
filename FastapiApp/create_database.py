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
import importlib
import os
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中，否则导入 CONFIG / Service 会失败
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from alembic import command
from alembic.config import Config as AlembicConfig

from CONFIG import CONFIG as APP_CONFIG


# ---------------------------------------------------------------------------
# 数据库配置：与 alembic/env.py 的 DATABASE_CONFIGS 保持一致
# ---------------------------------------------------------------------------

def _aiomysql_to_pymysql(url: str) -> str:
    """将 aiomysql 驱动 URL 转为 pymysql，供同步 create_all / stamp 使用。"""
    return url.replace("mysql+aiomysql://", "mysql+pymysql://")


def _import_metadata(import_path: str):
    """动态导入指定模块路径中的 Base.metadata 对象。"""
    mod = importlib.import_module(import_path)
    return mod.Base.metadata


DATABASE_CONFIGS: dict[str, dict] = {
    "biliopusdb": {
        "url": _aiomysql_to_pymysql(APP_CONFIG.database.MYSQL.get_other_lot_URI),
        "base_import": "Service.GetOthersLotDyn.Sql.models",
        "version_dir": "biliopusdb",
        "description": "普通抽奖动态库 (t_lotdyninfo / t_lot_extra_info 等)",
    },
    "bilidb": {
        "url": _aiomysql_to_pymysql(APP_CONFIG.database.MYSQL.bili_db_URI),
        "base_import": "Service.opus新版官方抽奖.活动抽奖.话题抽奖.db.models",
        "version_dir": "bilidb",
        "description": "话题抽奖库 (t_topic / t_traffic_card 等)",
    },
    "bili_reserve": {
        "url": _aiomysql_to_pymysql(APP_CONFIG.database.MYSQL.bili_reserve_URI),
        "base_import": "Service.opus新版官方抽奖.预约抽奖.db.models",
        "version_dir": "bili_reserve",
        "description": "预约抽奖库 (t_up_reserve_relation_info 等)",
    },
    "dyndetail": {
        "url": _aiomysql_to_pymysql(APP_CONFIG.database.MYSQL.dyn_detail_URI),
        "base_import": "Service.GrpcModule.GrpcSrc.SQLObject.models",
        "version_dir": "dyndetail",
        "description": "动态详情库 (bilidyndetail / lotdata 等)",
    },
    "proxy_db": {
        "url": _aiomysql_to_pymysql(APP_CONFIG.database.MYSQL.proxy_db_URI),
        "base_import": "Utils.代理.数据库操作.SqlAlcheyObj.ProxyModel",
        "version_dir": "proxy_db",
        "description": "代理数据库 (proxy_tab / available_proxy)",
    },
    "samsclub": {
        "url": _aiomysql_to_pymysql(APP_CONFIG.database.MYSQL.sams_club_URI),
        "base_import": "Service.samsclub.Sql.models",
        "version_dir": "samsclub",
        "description": "山姆会员店数据库 (spu_info 等)",
    },
}


# ---------------------------------------------------------------------------
# 核心逻辑
# ---------------------------------------------------------------------------

def _get_alembic_config(db_name: str, version_dir: str) -> AlembicConfig:
    """获取指定数据库的 Alembic Config，设置好 version_locations 和 -x db=xxx。"""
    alembic_ini = _project_root / "alembic.ini"
    cfg = AlembicConfig(str(alembic_ini))

    # 设置每个数据库独立的 version_locations
    version_path = str(_project_root / "alembic" / "versions" / version_dir)
    cfg.set_main_option("version_locations", version_path)

    # 通过 -x db=xxx 传递给 env.py
    from argparse import Namespace
    cfg.cmd_opts = Namespace(x=[f"db={db_name}"])

    return cfg


def _create_or_drop_all(
    db_name: str,
    engine: Engine,
    metadata,
    rebuild: bool,
) -> None:
    """
    对指定数据库执行 create_all（或 drop_all + create_all）。

    Args:
        db_name: 数据库名称（仅用于日志）
        engine: SQLAlchemy 同步 Engine
        metadata: SQLAlchemy MetaData 对象
        rebuild: 是否先 drop_all 再 create_all
    """
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    model_tables = metadata.tables.keys()

    if rebuild:
        if existing_tables:
            print(f"  [{db_name}] ⚠ 正在删除 {len(existing_tables)} 张表...")
            metadata.drop_all(engine)
            print(f"  [{db_name}] 已删除所有表")
        else:
            print(f"  [{db_name}] 数据库为空，跳过 drop_all")

    # create_all：只创建不存在的表，不会修改已有表的结构
    print(f"  [{db_name}] 正在根据 ORM 模型创建表...")
    metadata.create_all(engine)

    # 验证并报告
    inspector = inspect(engine)
    after_tables = inspector.get_table_names()
    print(f"  [{db_name}] 完成！当前共 {len(after_tables)} 张表:")
    for t in sorted(after_tables):
        cols = [c["name"] for c in inspector.get_columns(t)]
        print(f"    - {t} ({len(cols)} 列: {', '.join(cols[:8])}"
              f"{'...' if len(cols) > 8 else ''})")


def _stamp_head(db_name: str, version_dir: str) -> None:
    """
    对指定数据库执行 alembic stamp head，将 version_table 标记为最新版本。

    前提：该数据库的 versions/{db_name}/ 目录中已有迁移文件（至少一个 revision）。
    """
    alembic_cfg = _get_alembic_config(db_name, version_dir)

    # 验证是否有可用的 revision
    from alembic.script import ScriptDirectory
    script = ScriptDirectory.from_config(alembic_cfg)
    head_rev = script.get_current_head()

    if head_rev is None:
        print(f"  [{db_name}] ⚠ 没有迁移文件，跳过 stamp（不影响 create_all 结果）")
        return

    print(f"  [{db_name}] stamp head -> {head_rev}")
    command.stamp(alembic_cfg, "head")
    print(f"  [{db_name}] stamp 完成")


def process_database(db_name: str, db_config: dict, rebuild: bool) -> None:
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

        # 2. 创建同步引擎
        engine = create_engine(url, echo=False)

        try:
            # 3. create_all（或 drop_all + create_all）
            _create_or_drop_all(db_name, engine, metadata, rebuild=rebuild)

            # 4. stamp head
            _stamp_head(db_name, db_config["version_dir"])
        finally:
            engine.dispose()

        print(f"  [{db_name}] ✅ 处理完成")
    except Exception as e:
        print(f"  [{db_name}] ❌ 处理失败: {e}")
        raise


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

    db_names = [args.db] if args.db else list(DATABASE_CONFIGS.keys())
    failed: list[str] = []

    for db_name in db_names:
        try:
            process_database(db_name, DATABASE_CONFIGS[db_name], rebuild=args.rebuild)
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
        print("  - 后续修改模型后，使用 alembic -x db=xxx revision --autogenerate 生成增量迁移")
        print("  - lifespan 启动时会自动执行 upgrade head 和 autogenerate 检测")


if __name__ == "__main__":
    main()
