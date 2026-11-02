#!/bin/sh
# go-proxy-server 启动引导（IPv6 代理池前置条件自愈）
#
# 背景：本代理每次请求从「.env 里 NET_IF 指定的网卡」的 /64 前缀里**随机生成源地址**去拨号（日志里的
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
#   - 启动前补齐 sysctl 与子网路由，等 NET_IF 网卡拿到公网 IPv6（宿主刚开机时 RA 还没就绪）；
#   - 常驻后台**只读探测**、仅在缺失/前缀变化时才写（写入会发 netlink 变更通知，
#     Chromium 会据此判定网络变更并中断连接 → ERR_NETWORK_CHANGED）；
#   - 然后再 exec 真正的代理二进制（保持原镜像 CMD 的行为）。
#
# 运行要求：容器需 --privileged + --network host（写的是宿主 network namespace 的
# /proc/sys 与路由表）；见 docker-compose.yml 的 go-proxy-server 服务。

set -u

# 复查周期：探测是只读的（只发查询不发 netlink 变更），间隔可以放宽，减少噪音
CHECK_INTERVAL="${POOL_CHECK_INTERVAL:-300}"
SYSCTL_KEY=/proc/sys/net/ipv6/ip_nonlocal_bind
PREFIX_CACHE=/tmp/go-proxy-pool-prefix

log() { echo "[entrypoint] $*"; }

# ---- 网卡选择：每台机器网卡名都不同（eth0 / enp2s0 / ens18 …），不写死 ----
# .env 的 NET_IF 只是可选覆盖（填了、且本机真有这块网卡才用），否则自己判断：
#   1) 默认 IPv6 路由的网卡，且带公网 IPv6；
#   2) 任意非虚拟网卡上的公网 IPv6；
#   3) 默认 IPv4 路由的网卡（宿主刚开机、RA 还没下发，先占位，后面每轮重判）。
# 规则与 Go 侧 iface.go 的 detectNetIf 一致；这里只为「启动前预热路由」用，
# 代理进程启动后会自己再判断一次（不靠本脚本 export）。
VIRTUAL_IF_PREFIXES="lo docker br- veth virbr tun tap dummy cni flannel kube zt tailscale wg ifb vnet"

is_virtual_iface() {
    for prefix in $VIRTUAL_IF_PREFIXES; do
        case "$1" in
            "$prefix"*) return 0 ;;
        esac
    done
    return 1
}

has_public_ipv6() {
    ip -6 addr show dev "$1" scope global 2>/dev/null | grep -q 'inet6 [23]'
}

default_route_iface() {
    ip -"$1" route show default 2>/dev/null \
        | awk '{for (i = 1; i < NF; i++) if ($i == "dev") {print $(i + 1); exit}}'
}

detect_iface() {
    name="$(default_route_iface 6)"
    if [ -n "$name" ] && ! is_virtual_iface "$name" && has_public_ipv6 "$name"; then
        echo "$name"
        return 0
    fi
    for name in $(ip -o -6 addr show scope global 2>/dev/null | awk '{print $2}' | cut -d@ -f1 | sort -u); do
        is_virtual_iface "$name" && continue
        if has_public_ipv6 "$name"; then
            echo "$name"
            return 0
        fi
    done
    name="$(default_route_iface 4)"
    if [ -n "$name" ] && ! is_virtual_iface "$name"; then
        echo "$name"
        return 0
    fi
    return 1
}

resolve_iface() {
    if [ -n "${NET_IF:-}" ] && ip link show dev "$NET_IF" >/dev/null 2>&1; then
        echo "$NET_IF"
        return 0
    fi
    detect_iface
}

IFACE="$(resolve_iface)"
if [ -z "$IFACE" ]; then
    log "警告：暂时判断不出网卡（既没有默认路由，也没有带公网 IPv6 的物理网卡），后台会持续重试"
else
    log "使用网卡 $IFACE"
fi

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
    # 每轮重新解析网卡：宿主开机初期可能还没有默认路由 / 公网 IPv6，之后才出现
    iface="$(resolve_iface)"
    if [ -z "$iface" ]; then
        return 1
    fi
    # 取网卡上一个可用公网 IPv6 的 /64 前缀，例如 2409:8a1e:2e93:4fe0。
    # ⚠️ 必须排除 deprecated / tentative / dadfailed：光猫重新拨号换前缀后，旧前缀的
    # 地址会以 deprecated 状态在网卡上残留一段时间，继续拿它当池前缀 → 所有随机出口
    # 都拨不通（i/o timeout）。稳定地址优先，只有临时地址时退回临时地址（前缀一致）。
    ip -6 -o addr show dev "$iface" scope global 2>/dev/null | awk '
        /inet6 [23]/ && $0 !~ /deprecated|tentative|dadfailed/ {
            for (i = 1; i < NF; i++) {
                if ($i == "inet6") { split($(i + 1), a, "/"); addr = a[1]; break }
            }
            if (addr == "") next
            if ($0 !~ /temporary/) { print addr; found = 1; exit }
            if (first == "") first = addr
        }
        END { if (!found && first != "") print first }
    ' | cut -d: -f1-4 | head -1
}

ensure_subnet_route() {
    prefix="$(current_prefix)"
    if [ -z "$prefix" ]; then
        return 1
    fi
    # 前缀变了（光猫重新拨号）就把上一轮记录的前缀路由删掉：
    # 旧 /64 继续声明为本机地址没有任何意义，还会让排障时误判当前前缀。
    old_prefix="$(cat "$PREFIX_CACHE" 2>/dev/null || true)"
    if [ -n "$old_prefix" ] && [ "$old_prefix" != "$prefix" ]; then
        if ip -6 route del local "$old_prefix::/64" dev lo 2>/dev/null; then
            log "删除旧前缀路由 local $old_prefix::/64 dev lo（当前前缀 $prefix）"
        fi
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

# ---- 启动前：等网卡就绪（宿主刚开机时 DHCPv6/RA 可能还没拿到地址）----
i=0
while [ "$i" -lt 60 ]; do
    if ensure_all; then
        break
    fi
    i=$((i + 1))
    sleep 2
done
if [ "$i" -ge 60 ]; then
    IFACE="$(resolve_iface)"
    log "警告：120s 内未拿到公网 IPv6（网卡 ${IFACE:-未确定}），先启动代理，由后台守护继续重试"
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
