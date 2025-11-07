#!/bin/bash
set -e

echo "🚀 Starting custom init script..."

# Step 1: 启动原始 daemon（后台运行）
/app/daemon-run.sh &
DAEMON_PID=$!

# Step 2: 等待 LM Studio API 就绪
echo "⏳ Waiting for LM Studio API to be ready..."
while ! curl -sf http://localhost:1234/v1/models >/dev/null 2>&1; do
    echo "   Still waiting... (checking http://localhost:1234/v1/models)"
    sleep 3
done

# Step 3: 下载并预加载模型
echo "📥 Downloading and loading model: multilingual-e5-base-gguf"
lms get -y multilingual-e5-base-gguf@Q8_0
lms load -y multilingual-e5-base-gguf

echo "✅ Model loaded successfully. Container is ready!"

# Step 4: 等待原始 daemon 进程结束（防止容器退出）
wait $DAEMON_PID