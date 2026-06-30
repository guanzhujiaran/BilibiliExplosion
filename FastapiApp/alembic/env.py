"""
Alembic 多数据库版本管理 env.py

通过 -x db=xxx 参数指定目标数据库:
    alembic -x db=biliopusdb  upgrade head
    alembic -x db=biliopusdb  revision --autogenerate -m "add grand_prize_flag"
    alembic -x db=bilidb      upgrade head
    alembic -x db=bilidb      revision --autogenerate -m "xxx"
    alembic -x db=bili_reserve upgrade head
    alembic -x db=dyndetail   upgrade head
    alembic -x db=proxy_db    upgrade head
    alembic -x db=samsclub    upgrade head

不指定 -x db=xxx 时默认使用 biliopusdb。
"""

from sqlalchemy import engine_from_config, pool

from alembic import context

# ---------------------------------------------------------------------------
# 多数据库映射：每个数据库有一套 (URL, Base metadata, version_location)
# ---------------------------------------------------------------------------
from CONFIG import CONFIG as APP_CONFIG


def _aiomysql_to_pymysql(url: str) -> str:
    """将 aiomysql 驱动 URL 转为 pymysql，供同步 alembic 使用。"""
    return url.replace("mysql+aiomysql://", "mysql+pymysql://")


# 每个数据库的 Base 使用懒加载，避免一次性导入所有模块（减少循环导入风险）
def _import_base(import_path: str):
    """动态导入指定模块路径中的 Base 对象。"""
    import importlib
    mod = importlib.import_module(import_path)
    return mod.Base


DATABASE_CONFIGS = {
    "biliopusdb": {
        "url": _aiomysql_to_pymysql(APP_CONFIG.database.MYSQL.get_other_lot_URI),
        "base_import": "Service.GetOthersLotDyn.Sql.models",
        "version_dir": "biliopusdb",
        "description": "普通抽奖动态库 (t_lotdyninfo / t_lot_grand_prize_flag 等)",
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
# 解析 -x db=xxx 参数，选择目标数据库
# ---------------------------------------------------------------------------
# 例如: alembic -x db=biliopusdb upgrade head

# 尝试从命令行 -x db=xxx 获取目标数据库名称
_x_args = context.get_x_argument(as_dictionary=True)
_db_name = _x_args.get("db", "biliopusdb")

if _db_name not in DATABASE_CONFIGS:
    available = ", ".join(DATABASE_CONFIGS.keys())
    raise ValueError(
        f"未知的数据库名称: {_db_name}\n"
        f"可用的数据库: {available}\n"
        f"请通过 -x db=xxx 指定，例如: alembic -x db=biliopusdb upgrade head"
    )

_db_config = DATABASE_CONFIGS[_db_name]

# 设置目标数据库 URL 和版本目录
config = context.config
config.set_main_option("sqlalchemy.url", _db_config["url"])

# 动态设置 version_locations 为当前数据库对应的版本目录
# 这样 revision --autogenerate 会自动将新文件放入正确的子目录
_db_version_dir = _db_config["version_dir"]
import os as _os
_version_path = _os.path.join(
    _os.path.dirname(_os.path.abspath(__file__)), "versions", _db_version_dir
)
config.set_main_option("version_locations", _version_path)

# 导入对应数据库的 Base metadata
target_metadata = _import_base(_db_config["base_import"]).metadata

print(f"[alembic] 目标数据库: {_db_name} ({_db_config['description']})")
print(f"[alembic] URL: {_db_config['url'][:_db_config['url'].find('@')]}@***")
print(f"[alembic] 版本目录: versions/{_db_version_dir}/")


# ---------------------------------------------------------------------------
# 标准 migrate 逻辑
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def _include_object(object, name, type_, reflected, compare_to):
    """排除旧的 alembic_version 表（无后缀），避免 autogenerate 误将其
    检测为 "数据库中多余的表" 而生成 DROP TABLE 语句。
    """
    if type_ == "table" and name == "alembic_version":
        return False
    return True


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # 每个数据库使用独立的 version_table，避免多个数据库共享同一 MySQL 实例时冲突
            version_table=f"alembic_version_{_db_name}",
            # 过滤旧版 alembic_version 表，防止 autogenerate 生成 DROP TABLE
            include_object=_include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
