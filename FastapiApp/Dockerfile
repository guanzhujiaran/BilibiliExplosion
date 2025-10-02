FROM cimg/python:3.12.11-slim-bookworm
# 1. 更新系统并安装必要工具
RUN apt-get update -y && apt-get install -y curl

# 2. 安装Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# 3. 验证安装
RUN node -v && npm -v

LABEL authors="1944637830@qq.com"


WORKDIR /app

# 安装Node.js依赖
COPY package.json .
RUN npm install

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install

# 复制应用代码
COPY . /app

# 启动FastAPI应用
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","23333"]