#!/bin/bash
# =============================================================================
# 创建查询服务专用的只读账号（随 MySQL 容器自动初始化）
#
# 执行时机：**仅当数据目录为空、MySQL 首次初始化时**由
# /docker-entrypoint-initdb.d 自动执行一次。
#
#   全新环境（新建 docker_vol/mysql_data/data）→ 自动建号，无需手工干预
#   已有数据的库（当前开发库 / 生产库）        → 不会执行
#
# 已有环境请用幂等脚本补：
#   uv run python -m scripts.database.create_read_only_account.create_read_only_account \
#       --db-host <地址> --db-port 3306 --readonly-user bili_ro
# （两个入口授权范围一致，重复执行都安全）
#
# 密码从容器环境变量注入，不落在仓库里：
#   RO_USER      默认 bili_ro
#   RO_PASSWORD  必填，compose 里由 ${CRAWLER_QUERY_MYSQL_PASSWORD} 提供
# =============================================================================
set -euo pipefail

# 未显式提供时回退到 root 密码：绝不能因为缺一个变量就让 MySQL 首次初始化中断
if [ -z "${RO_PASSWORD:-}" ]; then
  RO_PASSWORD="${MYSQL_ROOT_PASSWORD}"
  echo "[init] 未提供 RO_PASSWORD，本次回退为 MYSQL_ROOT_PASSWORD"
fi

RO_USER="${RO_USER:-bili_ro}"
# 用户已存在时 IF NOT EXISTS 不会改密码，所以跟一条 ALTER USER 保证密码一致
mysql --protocol=socket -uroot -p"${MYSQL_ROOT_PASSWORD}" <<SQL
CREATE USER IF NOT EXISTS '${RO_USER}'@'%' IDENTIFIED BY '${RO_PASSWORD}';
ALTER USER '${RO_USER}'@'%' IDENTIFIED BY '${RO_PASSWORD}';
GRANT SELECT ON bilidb.*       TO '${RO_USER}'@'%';
GRANT SELECT ON bili_reserve.* TO '${RO_USER}'@'%';
GRANT SELECT ON biliopusdb.*   TO '${RO_USER}'@'%';
GRANT SELECT ON dyndetail.*    TO '${RO_USER}'@'%';
SQL

echo "[init] 只读账号 ${RO_USER} 已创建（仅 SELECT：bilidb / bili_reserve / biliopusdb / dyndetail）"
