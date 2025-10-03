FROM python:3.14.0rc3

# 1. 更新系统并安装必要工具
RUN apt-get update -y && apt-get install -y curl

# 2. 安装Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs rustc

# 3. 验证安装
RUN node -v && npm -v

LABEL authors="1944637830@qq.com"


WORKDIR /app

# 安装Node.js依赖
COPY package.json .
RUN npm install

RUN mkdir -p /pip_cache
ENV PIP_CACHE_DIR=/pip_cache

# 安装Python依赖
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN python3 -m pip install --upgrade setuptools
RUN pip install --no-cache-dir  -r requirements.txt

RUN playwright install

# 复制应用代码
COPY . /app

# 启动FastAPI应用
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","23333"]
