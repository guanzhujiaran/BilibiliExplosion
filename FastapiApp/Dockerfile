FROM cimg/python:3.13.7-node

LABEL authors="1944637830@qq.com"


WORKDIR /app

# 安装Node.js依赖
COPY package.json .
RUN npm install

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . /app
COPY ../.env.fastapi.prod /app/.env.fastapi.prod

# 启动FastAPI应用
CMD [
 "uvicorn",
 "app.main:app",
 "--host",
 "0.0.0.0",
 "--port",
 "23333"
 ]