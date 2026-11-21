#!/usr/bin/env bash
# =============================================================================
# RPA-Browser host 网络防火墙护栏（幂等）
#
# 背景：rpa-browser 使用 network_mode: host，28000 与 WebRTC 媒体 UDP 端口
#       直接监听宿主机。bridge 网络下由 Docker 做端口映射，host 网络下没有这层
#       隔离，必须用 iptables 自己限制来源。
#
# 规则（自定义链 RPA_HOST_GUARD，挂在 INPUT 第 1 位）：
#   TCP 28000   ：允许 127.0.0.1 / ::1 与 Docker 网段 172.19.0.0/16，其余 DROP
#   UDP 32768:60999：IPv6 全部放行；IPv4 仅 192.168.0.0/16
#   未命中本链的流量 RETURN，继续走 1Panel 等既有 INPUT 规则
#   （1Panel 的 ESTABLISHED 白名单会被保留，否则宿主机自己的 UDP 回包会被误伤）
#
# 用法（root）：
#   ./rpa-host-firewall.sh apply     # 立即应用（默认）
#   ./rpa-host-firewall.sh save      # 应用并 iptables-save 到 /etc/iptables/
#   ./rpa-host-firewall.sh install   # 安装开机自恢复 systemd oneshot（并立即 apply）
#   ./rpa-host-firewall.sh status    # 查看当前链与 INPUT 跳转
#
# 注意：本脚本只追加自己的链，不 flush 1Panel / Docker 的既有规则。
# 在 1Panel 里修改防火墙后，1Panel 可能重建 INPUT 链并丢掉自定义跳转，
# 需要重跑一次 `rpa-host-firewall.sh apply`（或 systemctl restart rpa-host-firewall）。
# =============================================================================
set -euo pipefail

CHAIN="${RPA_FW_CHAIN:-RPA_HOST_GUARD}"
TCP_PORT="${RPA_API_PORT:-28000}"
UDP_RANGE="${RPA_MEDIA_UDP_RANGE:-32768:60999}"
DOCKER_SUBNET="${RPA_DOCKER_SUBNET:-172.19.0.0/16}"
LAN_SUBNET="${RPA_LAN_SUBNET:-192.168.0.0/16}"
IPTABLES="${IPTABLES_BIN:-iptables}"
IP6TABLES="${IP6TABLES_BIN:-ip6tables}"
SELF_PATH="$(readlink -f "$0")"

require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "需要 root 权限（或在 privileged 容器里 chroot 进宿主机执行）" >&2
        exit 1
    fi
}

ensure_chain() {
    local ipt="$1"
    if ! "$ipt" -n -L "$CHAIN" >/dev/null 2>&1; then
        "$ipt" -N "$CHAIN"
    fi
    "$ipt" -F "$CHAIN"
}

ensure_input_jump() {
    local ipt="$1"
    # 已存在跳转就不重复插入；1Panel 重刷 INPUT 后本脚本重跑会补回
    if ! "$ipt" -C INPUT -j "$CHAIN" >/dev/null 2>&1; then
        "$ipt" -I INPUT 1 -j "$CHAIN"
    fi
}

apply_rules() {
    require_root

    # ---- IPv4 ----
    ensure_chain "$IPTABLES"
    "$IPTABLES" -A "$CHAIN" -i lo -j RETURN
    # 宿主机主动发起的 UDP（QUIC / DNS 等）回包目的端口也落在高位段，
    # 放行已建立连接，避免本护栏误伤宿主机自身出站流量
    "$IPTABLES" -A "$CHAIN" -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
    "$IPTABLES" -A "$CHAIN" -p tcp --dport "$TCP_PORT" -s 127.0.0.1 -j ACCEPT
    "$IPTABLES" -A "$CHAIN" -p tcp --dport "$TCP_PORT" -s "$DOCKER_SUBNET" -j ACCEPT
    "$IPTABLES" -A "$CHAIN" -p tcp --dport "$TCP_PORT" -j DROP
    "$IPTABLES" -A "$CHAIN" -p udp --dport "$UDP_RANGE" -s "$LAN_SUBNET" -j ACCEPT
    "$IPTABLES" -A "$CHAIN" -p udp --dport "$UDP_RANGE" -j DROP
    ensure_input_jump "$IPTABLES"

    # ---- IPv6 ----
    ensure_chain "$IP6TABLES"
    "$IP6TABLES" -A "$CHAIN" -i lo -j RETURN
    "$IP6TABLES" -A "$CHAIN" -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
    "$IP6TABLES" -A "$CHAIN" -p tcp --dport "$TCP_PORT" -s ::1 -j ACCEPT
    "$IP6TABLES" -A "$CHAIN" -p tcp --dport "$TCP_PORT" -j DROP
    # 公网手机 IPv6 直连 WebRTC 媒体：整个高位 UDP 段放行
    "$IP6TABLES" -A "$CHAIN" -p udp --dport "$UDP_RANGE" -j ACCEPT
    ensure_input_jump "$IP6TABLES"

    echo "已应用：TCP ${TCP_PORT} 仅 127.0.0.1/${DOCKER_SUBNET}；UDP ${UDP_RANGE} IPv6 全放行、IPv4 仅 ${LAN_SUBNET}"
}

save_rules() {
    apply_rules
    mkdir -p /etc/iptables
    # 快照用于审计 / 手工恢复；开机恢复由 systemd oneshot 重新执行 apply，
    # 避免整体 restore 与 Docker / 1Panel 启动时生成的链互相覆盖。
    "$IPTABLES-save" >/etc/iptables/rules.v4
    "$IP6TABLES-save" >/etc/iptables/rules.v6
    echo "已保存快照：/etc/iptables/rules.v4、/etc/iptables/rules.v6"
}

install_unit() {
    require_root
    install -m 0755 "$SELF_PATH" /usr/local/sbin/rpa-host-firewall
    cat >/etc/systemd/system/rpa-host-firewall.service <<'EOF'
[Unit]
Description=RPA-Browser host-network firewall guard (TCP 28000 + WebRTC UDP)
After=network-online.target docker.service 1panel-core.service 1panel-agent.service
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/rpa-host-firewall apply
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
    mkdir -p /etc/systemd/system/multi-user.target.wants
    ln -sf ../rpa-host-firewall.service /etc/systemd/system/multi-user.target.wants/rpa-host-firewall.service
    # WSL / chroot 场景下 systemd 可能不可用；开机时 systemd 会自行加载该 unit
    systemctl daemon-reload >/dev/null 2>&1 || true
    echo "已安装并启用 rpa-host-firewall.service（重启后自动恢复规则）"
    apply_rules
}

show_status() {
    require_root
    echo "=== iptables ${CHAIN} ==="
    "$IPTABLES" -S "$CHAIN" 2>/dev/null || echo "（未创建）"
    echo "=== ip6tables ${CHAIN} ==="
    "$IP6TABLES" -S "$CHAIN" 2>/dev/null || echo "（未创建）"
    echo "=== INPUT 跳转 ==="
    "$IPTABLES" -S INPUT 2>/dev/null | grep -- "$CHAIN" || echo "（IPv4 未挂载）"
    "$IP6TABLES" -S INPUT 2>/dev/null | grep -- "$CHAIN" || echo "（IPv6 未挂载）"
}

case "${1:-apply}" in
    apply) apply_rules ;;
    save) save_rules ;;
    install) install_unit ;;
    status) show_status ;;
    *)
        echo "用法: $0 [apply|save|install|status]" >&2
        exit 2
        ;;
esac
