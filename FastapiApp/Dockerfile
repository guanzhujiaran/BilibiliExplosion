FROM python:3.13-trixie

# 安装系统依赖（仅必要项）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/* \
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get install -y nodejs npm
RUN node -v && npm -v

## 安装 Rust（使用 rustup，官方推荐）
#RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
#ENV PATH="/root/.cargo/bin:${PATH}"


LABEL authors="1944637830@qq.com"

WORKDIR /app

# 安装 Node.js 依赖
COPY package.json .
RUN npm install

COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python3 -m pip install --upgrade setuptools && \
    pip install --no-cache-dir -r requirements.txt

# 切回主目录
WORKDIR /app

# 安装 Playwright 浏览器（放在代码复制前更合理）
RUN playwright install

# 复制应用代码（注意：.dockerignore 应排除 GrpcProto/*.py！）
COPY . /app

# 启动 FastAPI 应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "23333"]