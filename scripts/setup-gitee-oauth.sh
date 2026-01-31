#!/bin/bash

# Gitee OAuth 配置脚本
# 使用方法: bash scripts/setup-gitee-oauth.sh YOUR_GITEE_CLIENT_SECRET

set -e

echo "=========================================="
echo "  Gitee OAuth 配置脚本"
echo "=========================================="
echo ""

# 检查参数
if [ -z "$1" ]; then
    echo "❌ 错误: 请提供 Gitee Client Secret"
    echo ""
    echo "使用方法: bash $0 YOUR_GITEE_CLIENT_SECRET"
    echo ""
    echo "获取步骤:"
    echo "1. 登录 Gitee: https://gitee.com"
    echo "2. 进入: 设置 → 第三方应用 → 创建应用"
    echo "3. 应用名称: Bilibili Explosion SSO"
    echo "4. 应用主页: http://localhost:10011"
    echo "5. 应用回调地址: http://localhost:10011/callback"
    echo "6. 权限: user_info, emails"
    echo "7. 复制 Client Secret"
    echo ""
    exit 1
fi

GITEE_CLIENT_SECRET=$1
GITEE_CLIENT_ID="98fc6eb8faaed3b2cd44a1992887be84e7ae3488884fcd6edac3251c9a39fdd2"
CASDOOR_CONFIG_FILE="./docker_vol/casdoor/conf/app.conf"
BACKUP_CONFIG_FILE="./docker_vol/casdoor/conf/app.conf.backup"

echo "📋 配置信息:"
echo "   Gitee Client ID: $GITEE_CLIENT_ID"
echo "   Gitee Client Secret: ${GITEE_CLIENT_SECRET:0:10}..."
echo "   配置文件: $CASDOOR_CONFIG_FILE"
echo ""

# 检查配置文件是否存在
if [ ! -f "$CASDOOR_CONFIG_FILE" ]; then
    echo "❌ 错误: 配置文件不存在: $CASDOOR_CONFIG_FILE"
    exit 1
fi

# 备份原始配置
echo "📦 备份原始配置..."
cp "$CASDOOR_CONFIG_FILE" "$BACKUP_CONFIG_FILE"
echo "✅ 备份完成: $BACKUP_CONFIG_FILE"
echo ""

# 更新配置
echo "🔧 更新 Casdoor 配置..."

# 检查是否已存在 gitee 配置
if grep -q "^\[gitee\]" "$CASDOOR_CONFIG_FILE"; then
    echo "📝 更新现有 gitee 配置..."
    sed -i "s/^ClientSecret = .*/ClientSecret = $GITEE_CLIENT_SECRET/" "$CASDOOR_CONFIG_FILE"
else
    echo "📝 添加新的 gitee 配置..."
    cat >> "$CASDOOR_CONFIG_FILE" << EOF

[gitee]
ClientId = $GITEE_CLIENT_ID
ClientSecret = $GITEE_CLIENT_SECRET
Endpoint = https://gitee.com
EOF
fi

echo "✅ 配置更新完成"
echo ""

# 显示配置
echo "📄 当前 Gitee 配置:"
grep -A 3 "^\[gitee\]" "$CASDOOR_CONFIG_FILE"
echo ""

# 询问是否重启
read -p "是否重启 Casdoor 容器? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 重启 Casdoor 容器..."
    docker-compose restart casdoor
    echo "✅ Casdoor 已重启"
    echo ""
    echo "🌐 访问 Casdoor: http://localhost:10011"
    echo "🔑 默认账号: admin / 123"
else
    echo "⏸️  跳过重启"
    echo ""
    echo "手动重启命令:"
    echo "  docker-compose restart casdoor"
fi

echo ""
echo "=========================================="
echo "  配置完成!"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 访问 Casdoor 管理后台: http://localhost:10011"
echo "2. 登录后进入: Organization → Provider"
echo "3. 确认 Gitee Provider 已启用"
echo "4. 测试 Gitee 登录功能"
echo ""
