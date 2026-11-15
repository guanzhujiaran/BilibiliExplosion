#!/usr/bin/env bash
# 生产服务器上的**自动部署**：轮询 origin/<branch>，发现新提交就调 remote_deploy.sh。
#
# 整套部署只依赖 bash + git + docker compose，不引入 Jenkins / GitHub Actions 之类的外部编排：
#   - 生产机通常在内网，外部 CI 回连不进来，也不需要把私钥寄存在第三方；
#   - 发布逻辑（依赖层判定、健康检查、回滚）只有一份，就在服务器上，审计路径最短；
#   - 断网 / 远端故障都不会留下「部署到一半」的状态：拉不到就什么都不做。
#
# 两种运行方式（见 install_auto_deploy.sh）：
#   1) systemd timer（推荐）：每 2 分钟跑一次本脚本，跑完即退；
#   2) 常驻：DEPLOY_PATH=... ./auto_deploy.sh --daemon（内部 sleep 轮询）
#
# 安全相关的保护：
#   - 与手工发布共用同一把 flock，永远不会并发部署；
#   - Pause 开关：touch docker_vol/deploy/pause 后自动部署停止（维护窗口用）；
#   - 失败退避：同一个目标 SHA 部署失败后，30 分钟内不再重试（避免回滚 → 重试 → 回滚的死循环）；
#   - 工作区脏（remote_deploy 退出码 2）时按失败退避处理，并在日志里点名人工处理。
set -Eeuo pipefail

DEPLOY_PATH="${DEPLOY_PATH:?必须设置 DEPLOY_PATH（服务器上的仓库根目录）}"
BRANCH="${BRANCH:-main}"
POLL_SECONDS="${POLL_SECONDS:-120}"
# 同一个目标版本失败后的冷却时间
RETRY_BACKOFF="${RETRY_BACKOFF:-1800}"
# 日志超过该字节数就轮转一份 .1（无 logrotate 依赖）
LOG_MAX_BYTES="${LOG_MAX_BYTES:-5242880}"
DRY_RUN="${DRY_RUN:-0}"
# 演练/调试用：跳过 git fetch（配合 DRY_RUN=1 做全链路彩排，不碰网络）
SKIP_FETCH="${SKIP_FETCH:-0}"

STATE_DIR="$DEPLOY_PATH/docker_vol/deploy"
LOG_FILE="$STATE_DIR/auto.log"
STATE_FILE="$STATE_DIR/auto.state"
PAUSE_FILE="$STATE_DIR/pause"
LOCK_FILE="$STATE_DIR/deploy.lock"

mkdir -p "$STATE_DIR"

rotate_log() {
  [ -f "$LOG_FILE" ] || return 0
  local size
  size=$(wc -c <"$LOG_FILE" 2>/dev/null || echo 0)
  if [ "$size" -gt "$LOG_MAX_BYTES" ]; then
    mv -f "$LOG_FILE" "$LOG_FILE.1"
  fi
}

log() {
  local line
  line="[auto $(date '+%Y-%m-%d %H:%M:%S')] $*"
  printf '%s\n' "$line"
  printf '%s\n' "$line" >>"$LOG_FILE"
}

# state 文件：两行 KEY=VALUE，避免引入 jq / sqlite 之类依赖
state_get() {
  local key="$1"
  [ -f "$STATE_FILE" ] || return 0
  awk -F= -v k="$key" '$1==k {sub($1"=","",$0); print; exit}' "$STATE_FILE"
}
state_set() {
  local key="$1" value="$2" tmp
  tmp="$(mktemp)"
  if [ -f "$STATE_FILE" ]; then
    grep -v "^$key=" "$STATE_FILE" >"$tmp" || true
  fi
  printf '%s=%s\n' "$key" "$value" >>"$tmp"
  mv -f "$tmp" "$STATE_FILE"
}

# 演练（DRY_RUN=1）时不能落状态：否则一次彩排就会把「失败退避 / 上次成功」写脏，
# 反过来影响真实发布。
state_persist() {
  [ "$DRY_RUN" = "1" ] && return 0
  state_set "$@"
}

# 真正干活的部分（调用方已持有 flock）
deploy_locked() {
  cd "$DEPLOY_PATH"

  if [ "$SKIP_FETCH" != "1" ]; then
    if ! git fetch --prune origin "$BRANCH" >>"$LOG_FILE" 2>&1; then
      log "git fetch 失败（网络/GitHub 异常），本轮跳过"
      return 0
    fi
  fi

  local remote_sha local_sha
  remote_sha="$(git rev-parse "origin/$BRANCH" 2>/dev/null || true)"
  local_sha="$(git rev-parse HEAD)"
  if [ -z "$remote_sha" ]; then
    log "拿不到 origin/$BRANCH（远端分支不存在或 fetch 不完整），本轮跳过"
    return 0
  fi

  if [ "$remote_sha" = "$local_sha" ]; then
    # 版本一致时不写日志（每 2 分钟一条会淹掉真正的发布记录）
    return 0
  fi

  local failed_sha failed_ts now
  failed_sha="$(state_get failed_sha)"
  failed_ts="$(state_get failed_ts)"
  now="$(date +%s)"
  if [ "$remote_sha" = "$failed_sha" ] && [ -n "$failed_ts" ] &&
    [ $((now - failed_ts)) -lt "$RETRY_BACKOFF" ]; then
    log "目标版本 ${remote_sha:0:8} 上次部署失败，退避中（约 $(((RETRY_BACKOFF - (now - failed_ts)) / 60)) 分钟后重试）"
    return 0
  fi

  log "发现新版本：${local_sha:0:8} -> ${remote_sha:0:8}，开始部署"
  local rc=0
  set +e
  DEPLOY_PATH="$DEPLOY_PATH" BRANCH="$BRANCH" DEPLOY_LOCK_HELD=1 DRY_RUN="$DRY_RUN" \
    bash "$DEPLOY_PATH/scripts/deploy/remote_deploy.sh" >>"$LOG_FILE" 2>&1
  rc=$?
  set -e

  if [ "$rc" -eq 0 ]; then
    state_persist failed_sha ""
    state_persist failed_ts ""
    state_persist last_success "$(date '+%s') $remote_sha"
    log "✅ 部署成功：$remote_sha"
    # 只清 dangling 镜像（不带 -a，不会动正在被容器引用的层，回滚走 git reset + rebuild）。
    # dry-run 时绝不能做任何写操作（演练也会走到这里）。
    if [ "$DRY_RUN" != "1" ]; then
      docker image prune -f >>"$LOG_FILE" 2>&1 || true
    fi
  elif [ "$rc" -eq 2 ]; then
    state_persist failed_sha "$remote_sha"
    state_persist failed_ts "$now"
    log "❌ 目标版本 ${remote_sha:0:8} 未部署：服务器工作区有未提交改动（remote_deploy 退出码 2），请人工处理后等下一轮"
  else
    state_persist failed_sha "$remote_sha"
    state_persist failed_ts "$now"
    log "❌ 部署失败（退出码 $rc），已尝试回滚；$((RETRY_BACKOFF / 60)) 分钟内不再重试同一版本，详见 $LOG_FILE"
  fi
}

deploy_once() {
  if [ -f "$PAUSE_FILE" ]; then
    log "检测到暂停开关 $PAUSE_FILE，跳过本轮（删除该文件即恢复自动部署）"
    return 0
  fi

  # 与手工发布共用同一把锁：拿不到就说明有人正在部署，等下一轮再说。
  # 注意：flock 绑定在 fd 上，**必须在函数结尾显式释放**，
  # 否则常驻（--daemon）模式下第一轮之后锁就一直被自己占着。
  exec 9>"$LOCK_FILE"
  if ! flock -n 9; then
    log "另一个部署正在进行，跳过本轮"
    exec 9>&-
    return 0
  fi
  export DEPLOY_LOCK_HELD=1

  local rc=0
  set +e
  deploy_locked
  rc=$?
  set -e

  flock -u 9 2>/dev/null || true
  exec 9>&-
  unset DEPLOY_LOCK_HELD
  return "$rc"
}

main() {
  rotate_log
  if [ "${1:-}" = "--daemon" ]; then
    log "常驻模式启动：每 ${POLL_SECONDS}s 轮询 origin/$BRANCH（DEPLOY_PATH=$DEPLOY_PATH）"
    trap 'log "收到退出信号，退出常驻模式"; exit 0' INT TERM
    while true; do
      deploy_once || log "本轮异常（已忽略，继续下一轮）"
      sleep "$POLL_SECONDS"
    done
  fi
  if [ "${1:-}" = "--status" ]; then
    echo "DEPLOY_PATH=$DEPLOY_PATH"
    echo "本地 HEAD  = $(cd "$DEPLOY_PATH" && git rev-parse HEAD 2>/dev/null)"
    echo "origin/$BRANCH = $(cd "$DEPLOY_PATH" && git rev-parse "origin/$BRANCH" 2>/dev/null)"
    echo "last_success = $(state_get last_success)"
    echo "failed_sha   = $(state_get failed_sha)"
    echo "failed_ts    = $(state_get failed_ts)"
    echo "pause        = $([ -f "$PAUSE_FILE" ] && echo 有 || echo 无)"
    echo "最近 10 行日志："
    tail -n 10 "$LOG_FILE" 2>/dev/null || true
    return 0
  fi
  deploy_once
}

main "${1:-}"
