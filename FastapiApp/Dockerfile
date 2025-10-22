FROM nikolaik/python-nodejs:python3.13-nodejs24-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
LABEL authors="1944637830@qq.com"

WORKDIR /app

# 安装 Node.js 依赖
COPY package.json .
RUN npm install

COPY pyproject.toml .python-version uv.lock ./

RUN uv sync --locked

ENV PLAYWRIGHT_DOWNLOAD_HOST=https://registry.npmmirror.com/-/binary/playwright
RUN uv run playwright install chromium

COPY . .

EXPOSE 23333
# 启动 FastAPI 应用
CMD ["uv","run","uvicorn","main:app","--host","0.0.0.0","--port","23333"]