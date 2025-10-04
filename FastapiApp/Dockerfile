FROM nikolaik/python-nodejs:python3.13-nodejs24-slim

LABEL authors="1944637830@qq.com"

WORKDIR /app

# 安装 Node.js 依赖
COPY package.json .
RUN npm install

COPY requirements.txt .
RUN python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ --upgrade pip && \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ --upgrade setuptools && \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir -r requirements.txt

# 切回主目录
WORKDIR /app

# 安装 Playwright 浏览器（放在代码复制前更合理）
# 使用国内镜像加速，不然慢的要死，被这东西恶心一整天了
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://registry.npmmirror.com/-/binary/playwright
RUN playwright install chromium


COPY . /app

# 启动 FastAPI 应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "23333"]