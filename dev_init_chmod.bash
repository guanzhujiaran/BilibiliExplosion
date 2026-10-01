#!/usr/bin/env bash
# WSL 开发环境下 docker_vol 里的文件属主/权限会漂移：容器内进程 uid 与 bind mount
# 看到的属主对不上，数据库/中间件就会「读不到自己写的文件」。典型现象：
#   - postgres: FATAL: could not open file "global/pg_filenode.map": Permission denied
#   - rabbitmq: 声明队列时 reply_code=541 INTERNAL_ERROR（mnesia 写不动）
#   - mysql:    无法加载对应的库
# 所以每次启动容器前把权限摊平。
#
# 重要：postgres / rabbitmq 镜像内的用户是 70 / 999，数据目录是 700，当前用户不是属主，
# 无权限的路径普通 chmod 进不去，脚本会自动对失败路径用 sudo 重试（会提示输密码）。
#
# 必须在容器全部停止时执行，否则数据库运行期会重新把权限改回 700。
set -uo pipefail

cd "$(dirname "$0")" || exit 1

# 需要摊平权限的路径（数据库数据 + 消息中间件 mnesia）
PATHS=(
  ./docker_vol/mysql_data/data
  ./docker_vol/postgres
  ./docker_vol/rabbitmq
  ./docker_vol/redis
)

# 用当前用户 chmod；失败（属主不匹配 / 无权限）再用 sudo 重试
fix_perm() {
  local path="$1"

  if [ ! -e "$path" ]; then
    echo "[skip] 不存在: $path"
    return 0
  fi

  if chmod -R 777 "$path" 2>/dev/null; then
    echo "[ok] $path"
  elif sudo chmod -R 777 "$path"; then
    echo "[ok via sudo] $path"
  else
    echo "[fail] 无法修正权限: $path" >&2
    return 1
  fi
}

rc=0
for path in "${PATHS[@]}"; do
  fix_perm "$path" || rc=1
done

exit "$rc"
