#!/usr/bin/env bash
# 在生产服务器上安装「自动部署」：systemd timer 每 N 分钟跑一次 auto_deploy.sh。
#
# 用法（在仓库根目录执行）：
#   sudo bash scripts/deploy/install_auto_deploy.sh                 # 默认每 2 分钟
#   sudo bash scripts/deploy/install_auto_deploy.sh --interval 300  # 每 5 分钟
#   sudo bash scripts/deploy/install_auto_deploy.sh --user deploy   # 指定跑部署的系统用户
#   bash scripts/deploy/install_auto_deploy.sh --dry-run            # 只打印 unit 内容，不落盘
#   sudo bash scripts/deploy/install_auto_deploy.sh --uninstall     # 卸载
#
# 为什么用 timer 而不是常驻进程：定时器天然「跑完即退」，不占内存、崩了也不影响系统，
# 而且每次都是全新进程，不会像常驻脚本那样把偶发错误带进下一轮。
set -Eeuo pipefail

UNIT_NAME="biliexplosion-auto-deploy"
REPO_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INTERVAL=120
RUN_USER="${SUDO_USER:-$(id -un)}"
DRY_RUN=0
UNINSTALL=0
BRANCH="main"
UNIT_DIR="/etc/systemd/system"

while [ $# -gt 0 ]; do
  case "$1" in
    --path) REPO_PATH="$2"; shift 2 ;;
    --interval) INTERVAL="$2"; shift 2 ;;
    --user) RUN_USER="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "未知参数：$1（--help 看用法）" >&2; exit 2 ;;
  esac
done

SERVICE_FILE="$UNIT_DIR/$UNIT_NAME.service"
TIMER_FILE="$UNIT_DIR/$UNIT_NAME.timer"

if [ "$UNINSTALL" = "1" ]; then
  if [ "$DRY_RUN" = "1" ]; then
    echo "[dry-run] systemctl disable --now $UNIT_NAME.timer && rm -f $SERVICE_FILE $TIMER_FILE"
    exit 0
  fi
  systemctl disable --now "$UNIT_NAME.timer" 2>/dev/null || true
  rm -f "$SERVICE_FILE" "$TIMER_FILE"
  systemctl daemon-reload
  echo "已卸载 $UNIT_NAME（部署日志与状态仍保留在 $REPO_PATH/docker_vol/deploy/）"
  exit 0
fi

render_service() {
  cat <<EOF
[Unit]
Description=BilibiliExplosion 生产自动部署（拉取 origin/$BRANCH 并重启变更服务）
Documentation=file://$REPO_PATH/README.md
After=network-online.target docker.service
Wants=network-online.target
Requires=docker.service

[Service]
Type=oneshot
User=$RUN_USER
WorkingDirectory=$REPO_PATH
# 一定要带上 docker 所在的路径：systemd 的默认 PATH 里通常没有 /usr/local/bin
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=DEPLOY_PATH=$REPO_PATH
Environment=BRANCH=$BRANCH
Environment=RETRY_BACKOFF=1800
ExecStart=/bin/bash $REPO_PATH/scripts/deploy/auto_deploy.sh
TimeoutStartSec=40min
# 失败也已经被脚本内部回滚并记录，这里不重启（timer 下个周期会再试）
Restart=no
EOF
}

render_timer() {
  cat <<EOF
[Unit]
Description=定时触发 BilibiliExplosion 自动部署（每 ${INTERVAL}s）

[Timer]
OnBootSec=3min
OnUnitActiveSec=${INTERVAL}s
# 开机错过的触发不需要补跑：拉一次最新就够了
Persistent=false
AccuracySec=15s
Unit=$UNIT_NAME.service

[Install]
WantedBy=timers.target
EOF
}

if [ "$DRY_RUN" = "1" ]; then
  echo "===== $SERVICE_FILE ====="
  render_service
  echo
  echo "===== $TIMER_FILE ====="
  render_timer
  echo
  echo "[dry-run] systemctl daemon-reload && systemctl enable --now $UNIT_NAME.timer"
  exit 0
fi

if [ "$(id -u)" != "0" ]; then
  echo "需要 root 权限写入 $UNIT_DIR（用 sudo 执行，或加 --dry-run 先看看内容）" >&2
  exit 1
fi

# 部署状态/日志目录：交给实际执行部署的用户，避免 systemd 以 $RUN_USER 跑时写不进去
mkdir -p "$REPO_PATH/docker_vol/deploy"
chown -R "$RUN_USER":"$(id -gn "$RUN_USER")" "$REPO_PATH/docker_vol/deploy" 2>/dev/null || true

render_service >"$SERVICE_FILE"
render_timer >"$TIMER_FILE"
systemctl daemon-reload
systemctl enable --now "$UNIT_NAME.timer"

cat <<EOF

✅ 已安装并启动：
   $SERVICE_FILE
   $TIMER_FILE

常用命令：
   systemctl list-timers $UNIT_NAME.timer          # 下次触发时间
   systemctl start $UNIT_NAME.service             # 立刻跑一次（不等 timer）
   journalctl -u $UNIT_NAME.service -n 100 --no-pager
   tail -f $REPO_PATH/docker_vol/deploy/auto.log  # 部署记录
   bash $REPO_PATH/scripts/deploy/auto_deploy.sh --status
   touch $REPO_PATH/docker_vol/deploy/pause       # 临时暂停自动部署（维护窗口）
   rm -f $REPO_PATH/docker_vol/deploy/pause       # 恢复

前置条件：$RUN_USER 必须能执行 docker（在 docker 组内）且能 git fetch 本仓库及其 submodule。
EOF
