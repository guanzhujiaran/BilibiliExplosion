#!/usr/bin/env bash
# 生产服务器上的发布脚本：拉代码 → 需要时重建镜像 → 重启服务 → 健康检查 →（失败）自动回滚。
#
# 为什么是「git pull + restart」而不是「docker compose pull 新镜像」：
#   docker-compose.yml 里所有业务服务的源码都是 **bind mount**（./be-bilibili-crawler:/app 等），
#   镜像只承载依赖层（/opt/venv）。所以代码发布 = 更新工作区 + 重启容器；
#   只有 Dockerfile.mono / uv.lock / compose 文件变了才需要 rebuild。
#
# 入口有两个：
#   1. 服务器上的自动部署（systemd timer → auto_deploy.sh → 本脚本，见 install_auto_deploy.sh）；
#   2. 人工在服务器上执行。
#   DEPLOY_PATH=/opt/BilibiliExplosion ./scripts/deploy/remote_deploy.sh
#   DRY_RUN=1 ...            # 只打印将要做什么（绝对不改工作区）
#   SERVICES="be-bilibili-crawler" ...   # 只发布指定服务
set -Eeuo pipefail

DEPLOY_PATH="${DEPLOY_PATH:?必须设置 DEPLOY_PATH（服务器上的仓库根目录）}"
BRANCH="${BRANCH:-main}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
# 默认发布「源码常变 + 有 HTTP 健康检查」的服务；gateway / 基础设施不在这里动
SERVICES="${SERVICES:-be-bilibili-crawler be-bilibili-crawler-query be-message-service rpa-browser}"
# 格式：service:容器内端口:健康路径（用 docker compose port 反查宿主机端口）
HEALTH_CHECKS="${HEALTH_CHECKS:-be-bilibili-crawler:23333:/health be-bilibili-crawler-query:23336:/health be-message-service:18739:/health}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-180}"
DRY_RUN="${DRY_RUN:-0}"
FORCE="${FORCE:-0}"
# 强制重建镜像（依赖层判定可能不准，如子模块锁文件未变但系统依赖变了）
REBUILD="${REBUILD:-0}"

PREV_SHA=""
ROLLED_BACK=0

log() { printf '\n[deploy %s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
run() {
  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] $*"
    return 0
  fi
  "$@"
}

compose() {
  if docker compose version >/dev/null 2>&1; then
    run docker compose -f "$COMPOSE_FILE" "$@"
  else
    run docker-compose -f "$COMPOSE_FILE" "$@"
  fi
}

compose_capture() {
  if docker compose version >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" "$@"
  else
    docker-compose -f "$COMPOSE_FILE" "$@"
  fi
}

# ---------------------------------------------------------------- 回滚
rollback() {
  local exit_code=$?
  [ "$ROLLED_BACK" = "0" ] || exit "$exit_code"
  ROLLED_BACK=1
  if [ -z "$PREV_SHA" ]; then
    log "❌ 发布失败（exit=$exit_code），且没有可回滚的版本（首次部署？）"
    exit "$exit_code"
  fi
  log "❌ 发布失败（exit=$exit_code），回滚到 $PREV_SHA"
  if [ "$DRY_RUN" = "1" ]; then
    # dry-run 绝对不能改工作区：只报告将要执行的回滚动作
    log "[dry-run] 跳过 git reset --hard $PREV_SHA 与重启"
    exit "$exit_code"
  fi
  git reset --hard "$PREV_SHA" || true
  git submodule update --init --recursive || true
  compose up -d --build $SERVICES || true
  log "已回滚到 $PREV_SHA（请检查日志：docker compose logs --tail=200）"
  exit "$exit_code"
}
trap rollback ERR

# ---------------------------------------------------------------- 0. 互斥锁
# 自动部署（timer / --daemon）与手工发布可能同时触发：谁先拿到锁谁跑，
# 另一个直接退出（auto_deploy 会在下个周期重试），避免两套流程交叉 reset + 重启。
# auto_deploy.sh 已经持有锁时会导出 DEPLOY_LOCK_HELD=1，这里跳过，避免自己锁死自己。
cd "$DEPLOY_PATH"
LOCK_FILE="${LOCK_FILE:-$DEPLOY_PATH/docker_vol/deploy/deploy.lock}"
if [ "${DEPLOY_LOCK_HELD:-0}" != "1" ]; then
  mkdir -p "$(dirname "$LOCK_FILE")"
  exec 9>"$LOCK_FILE"
  if ! flock -n 9; then
    log "另一个发布正在进行（$LOCK_FILE 被占用），本次跳过"
    exit 0
  fi
  export DEPLOY_LOCK_HELD=1
fi

# ---------------------------------------------------------------- 1. 准备
command -v git >/dev/null || { log "缺少 git"; exit 1; }

if [ "$FORCE" != "1" ] && [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  log "工作区有未提交改动，拒绝发布（确认可以覆盖时用 FORCE=1）"
  git status --short
  exit 2
fi

PREV_SHA="$(git rev-parse HEAD)"
log "当前版本 $PREV_SHA，目标分支 $BRANCH"

# ---------------------------------------------------------------- 2. 拉代码
log "拉取 $BRANCH"
run git fetch --prune origin "$BRANCH"
run git checkout -q "$BRANCH"
run git reset --hard "origin/$BRANCH"
NEW_SHA="$(git rev-parse HEAD 2>/dev/null || echo "$PREV_SHA")"
if [ "$DRY_RUN" != "1" ] && [ "$PREV_SHA" = "$NEW_SHA" ]; then
  log "版本未变化（$NEW_SHA），仍继续重启以确保进程加载的是最新工作区"
fi

# submodule 跟根仓库的**锁定提交**（不用 --remote：发布必须可复现）
log "同步 submodule"
run git submodule sync --recursive
run git submodule update --init --recursive

# ---------------------------------------------------------------- 3. 判断是否需要重建镜像
NEED_BUILD=0
if [ "$DRY_RUN" != "1" ] && [ "$PREV_SHA" != "$NEW_SHA" ]; then
  changed="$(git diff --name-only "$PREV_SHA" "$NEW_SHA" || true)"
  if printf '%s\n' "$changed" | grep -Eq '(^|/)Dockerfile\.mono$|(^|/)uv\.lock$|^docker-compose(\.[a-z]+)?\.yml$|(^|/)package-lock\.json$'; then
    NEED_BUILD=1
  fi
elif [ "$PREV_SHA" = "$NEW_SHA" ]; then
  NEED_BUILD=0
else
  NEED_BUILD=1
fi

if [ "$REBUILD" = "1" ]; then
  log "REBUILD=1：强制重建镜像"
  NEED_BUILD=1
fi

if [ "$NEED_BUILD" = "1" ]; then
  log "检测到依赖/构建文件变化，重建镜像（$SERVICES）"
  compose build $SERVICES
else
  log "仅代码变更，跳过镜像重建（依赖层未变）"
fi

# ---------------------------------------------------------------- 4. 重启
log "重启服务：$SERVICES"
if [ "$NEED_BUILD" = "1" ]; then
  compose up -d $SERVICES
else
  compose up -d --no-build $SERVICES
fi

# ---------------------------------------------------------------- 5. 健康检查
log "健康检查（最长 ${HEALTH_TIMEOUT}s）"
deadline=$(( $(date +%s) + HEALTH_TIMEOUT ))
for entry in $HEALTH_CHECKS; do
  service="${entry%%:*}"
  rest="${entry#*:}"
  port="${rest%%:*}"
  path="${rest#*:}"
  [ -n "$path" ] || path="/health"

  host_port="$(compose_capture port "$service" "$port" 2>/dev/null | tail -1 | sed 's/.*://')"
  if [ -z "$host_port" ]; then
    log "⚠️  $service 没有发布 ${port} 端口（容器内没有该服务？），跳过 HTTP 检查"
    continue
  fi

  ok=0
  while [ "$(date +%s)" -lt "$deadline" ]; do
    code="$(curl -s -o /dev/null -m 5 -w '%{http_code}' "http://127.0.0.1:${host_port}${path}" || true)"
    if [ "$code" = "200" ]; then
      log "✅ $service ${path} -> 200（宿主机端口 ${host_port}）"
      ok=1
      break
    fi
    sleep 3
  done
  if [ "$ok" != "1" ]; then
    log "❌ $service ${path} 未在 ${HEALTH_TIMEOUT}s 内返回 200（最后状态码：${code:-无响应}）"
    compose_capture logs --tail=80 "$service" || true
    false # 触发 ERR → rollback
  fi
done

# 容器状态兜底：重启后处于 Exited / Restarting 一律视为失败
# （awk 'NR>1 && NF' 去掉表头与空行，否则一个空行就会被误判成「有异常容器」）
bad="$(compose_capture ps --status exited --status restarting 2>/dev/null | awk 'NR>1 && NF' || true)"
if [ -n "$bad" ]; then
  log "❌ 存在未正常运行的容器："
  printf '%s\n' "$bad"
  false
fi

# ---------------------------------------------------------------- 6. 记录
if [ "$DRY_RUN" != "1" ]; then
  mkdir -p docker_vol/deploy
  printf '%s %s prev=%s services="%s"\n' \
    "$(date '+%Y-%m-%d %H:%M:%S')" "$NEW_SHA" "$PREV_SHA" "$SERVICES" \
    >> docker_vol/deploy/history.log
fi
trap - ERR
log "🎉 发布完成：$PREV_SHA -> $NEW_SHA"
