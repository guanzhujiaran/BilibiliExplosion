#!/bin/sh
# go-proxy-server 启动引导（IPv6 代理池前置条件自愈）
#
# 背景：本代理每次请求从 eth0 的 /64 前缀里**随机生成源地址**去拨号（日志里的
# `dial ... via [2409:8a1e:...:随机后缀]`）。要让内核接受「绑定不属于本机的源地址」，
# 必须同时满足两件事：
#   1) net.ipv6.ip_nonlocal_bind = 1
#   2) ip -6 route replace local <prefix>::/64 dev lo
#
# 代理程序自己只做第 2 步（启动时 `ip route replace local ... dev lo` + NDP 代答），
# 第 1 步是宿主机内核参数：**宿主机重启后会回落到 0**（sysctl 未持久化时），
# 于是随机源地址 bind 全部失败（errno 99 EADDRNOTAVAIL）→ 每个出口都 502：
#   dial tcp [2409:...:xxx]:0->[...]:443: bind: cannot assign requested address
#
# 本脚本职责：
#   - 启动前补齐 sysctl 与子网路由，等 eth0 拿到公网 IPv6（宿主刚开机时 RA 还没就绪）；
#   - 常驻后台**只读探测**、仅在缺失/前缀变化时才写（写入会发 netlink 变更通知，
#     Chromium 会据此判定网络变更并中断连接 → ERR_NETWORK_CHANGED）；
#   - 然后再 exec 真正的代理二进制（保持原镜像 CMD 的行为）。
#
# 运行要求：容器需 --privileged + --network host（写的是宿主 network namespace 的
# /proc/sys 与路由表）；见 docker-compose.yml 的 go-proxy-server 服务。

set -u

IFACE="${NET_IF:-eth0}"
# 复查周期：探测是只读的（只发查询不发 netlink 变更），间隔可以放宽，减少噪音
CHECK_INTERVAL="${POOL_CHECK_INTERVAL:-300}"
SYSCTL_KEY=/proc/sys/net/ipv6/ip_nonlocal_bind
PREFIX_CACHE=/tmp/go-proxy-pool-prefix

log() { echo "[entrypoint] $*"; }

ensure_nonlocal_bind() {
    if [ "$(cat "$SYSCTL_KEY" 2>/dev/null)" = "1" ]; then
        return 0
    fi
    if echo 1 > "$SYSCTL_KEY" 2>/dev/null; then
        log "已开启 net.ipv6.ip_nonlocal_bind=1"
        return 0
    fi
    log "警告：写 $SYSCTL_KEY 失败（需要 privileged + host 网络），随机源地址将 bind 失败"
    return 1
}

current_prefix() {
    # 取 eth0 上第一个公网 IPv6 的 /64 前缀，例如 2409:8a1e:2e94:84e0
    ip -6 addr show dev "$IFACE" scope global 2>/dev/null \
        | awk '/inet6 (2|3)/ {print $2; exit}' \
        | cut -d/ -f1 \
        | cut -d: -f1-4
}

ensure_subnet_route() {
    prefix="$(current_prefix)"
    if [ -z "$prefix" ]; then
        return 1
    fi
    # ⚠️ 必须先探测再写入：`ip route ... replace` 即使内容完全一致也会发
    # netlink 路由变更通知，Chromium 的 NetworkChangeNotifier 收到后会判定
    # 「网络已变更」并中断所有在途连接（页面报 ERR_NETWORK_CHANGED）。
    # 守护是周期执行的，无条件 replace 等于每隔 N 秒把浏览器网络打断一次。
    # 注意别加 `dev lo` 过滤：`ip -6 route show table local dev lo` 的输出会省略
    # `dev lo`（显示成 `local <prefix>::/64 metric 1024`），拿它 grep 会永远不命中。
    if ip -6 route show table local 2>/dev/null \
        | grep -qF "local ${prefix}::/64"; then
        [ "$(cat "$PREFIX_CACHE" 2>/dev/null)" = "$prefix" ] || echo "$prefix" > "$PREFIX_CACHE"
        return 0
    fi
    if ip -6 route add local "$prefix::/64" dev lo 2>/dev/null; then
        log "补加路由 local $prefix::/64 dev lo（NDP 代答由代理程序负责）"
        echo "$prefix" > "$PREFIX_CACHE"
        return 0
    fi
    # add 失败（并发/已存在但格式不一致）时再 replace 兜底一次
    if ip -6 route replace local "$prefix::/64" dev lo 2>/dev/null; then
        log "重建路由 local $prefix::/64 dev lo"
        echo "$prefix" > "$PREFIX_CACHE"
        return 0
    fi
    log "警告：添加 local $prefix::/64 dev lo 路由失败"
    return 1
}

ensure_all() {
    ensure_nonlocal_bind
    ensure_subnet_route
}

# ---- 启动前：等 eth0 就绪（宿主刚开机时 DHCPv6/RA 可能还没拿到地址）----
i=0
while [ "$i" -lt 60 ]; do
    if ensure_all; then
        break
    fi
    i=$((i + 1))
    sleep 2
done
if [ "$i" -ge 60 ]; then
    log "警告：120s 内未拿到公网 IPv6（$IFACE），先启动代理，由后台守护继续重试"
fi

# ---- 常驻守护：把两件事钉住，谁清掉就补回来（不阻塞主进程）----
(
    while true; do
        sleep "$CHECK_INTERVAL"
        ensure_all
    done
) &

# ---- 启动真正的代理程序（与原镜像 CMD 一致）----
if [ -x /opt/bin/go-proxy-ipv6-pool ]; then
    exec /opt/bin/go-proxy-ipv6-pool
fi
exec /app/go-proxy-ipv6-pool
