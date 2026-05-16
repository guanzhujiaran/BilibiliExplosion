FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
ENV RUSTUP_UPDATE_ROOT=https://mirrors.aliyun.com/rustup/rustup
ENV RUSTUP_DIST_SERVER=https://mirrors.aliyun.com/rustup
WORKDIR /app

# 配置 Debian 阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装构建工具、Node.js 和其他依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    g++ \
    gcc \
    make \
    nodejs \
    npm \
    curl \
    pkg-config \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*
    
# 安装 Node.js 依赖
COPY package.json .
RUN npm config set registry https://registry.npmmirror.com && \
    npm install

COPY pyproject.toml .python-version uv.lock ./

RUN uv sync -v
# ENV PLAYWRIGHT_DOWNLOAD_HOST=https://registry.npmmirror.com/-/binary/playwright
RUN uv run playwright install chromium

COPY . .

EXPOSE 23333
# 启动 FastAPI 应用
CMD ["uv","run","uvicorn","main:app","--host","0.0.0.0","--port","23333"]