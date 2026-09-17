# be-bilibili-crawler 容器热更新计划书（对齐 be-message-service）

> 目标：改 crawler 源码后**重启容器即生效**，不必 `docker compose build` 重建镜像
> 状态：**实施中**（2026-09-17）
> 关联：`Dockerfile.mono`（crawler target）、`docker-compose.yml`、`docs/be-bilibili-crawler-依赖瘦身计划书.md`

---

## 1. 背景

`be-message-service` 的做法是 bind mount 源码 + 入口指向挂载路径：

```yaml
volumes:
  - ./be-message-service/app:/app/app
```
```dockerfile
CMD ["uvicorn", "app.main:app", ...]
```

因此它改完代码 `docker compose restart be-message-service` 即生效。

而 `be-bilibili-crawler` 当前的 compose 里**没有任何源码挂载**，代码来自构建期
`COPY be-bilibili-crawler/ .`；源码改动靠 `develop.watch` 的 `sync+restart` 同步。
问题在于：`Makefile` 的 `make start` / `make restart` 用的是 `docker-compose up -d` /
`docker-compose restart`，**不带 `--watch`**，watch 进程从未运行，于是实际体验退化成
「改一行代码也要 `docker compose build`」。

另外两个结构性约束：

1. crawler 的入口是 `main:app`（`/app/main.py`），业务代码散在十几个顶层目录
   （`ApiRoutes/ controller/ dao/ Models/ models/ Service/ Utils/ scripts/ alembic/`）+ 根目录散文件，
   **没有单一包可挂**，只能整目录挂 `./be-bilibili-crawler:/app`。
2. 整目录挂载会顶掉镜像里 `/app` 下的构建期产物 `/app/node_modules`
   （`jsdom` / `md5`，`Service/zhihu`、`Service/toutiao` 的 execjs 签名要用）。
   宿主机没有这个目录，一挂就没了 → 签名 JS 执行失败。
   （同款历史坑：`/app/.venv` 被顶掉 → `uvicorn: executable file not found in $PATH`，
   venv 迁到 `/opt/venv` 后已消除。）

## 2. 方案选型

| 方案 | 做法 | 结论 |
|---|---|---|
| A | 保持 watch，启动命令改 `docker compose up -d --watch` | 不改结构，但源码是「复制进容器」的单向同步，容器内运行期产物需逐个 ignore/挂卷；与 message 不一致，弃 |
| B | **整目录 bind mount + node_modules 外移出 /app** | 与 message 完全一致，改完 restart 即生效；代价是 `/app/node_modules` 必须搬家，选它 |
| C | 整目录 bind mount + `be-crawler_node_modules:/app/node_modules` 命名卷 | gateway 的既有写法，但命名卷一旦创建会固化内容，`npm install` 变化后不会自动更新，弃 |

## 3. 改动清单

### 3.1 `Dockerfile.mono`（crawler-build / crawler）

| # | 改动 | 理由 |
|---|---|---|
| 1 | npm 依赖装到 `/opt/node`（`--prefix /opt/node`），不再落 `/app/node_modules` | 让 `/app` 可被整目录挂载而不丢 node_modules |
| 2 | 运行阶段 `COPY --from=crawler-build /opt/node/node_modules /opt/node_modules` + `ENV NODE_PATH=/opt/node_modules` | Node 的 `require('jsdom'|'md5')` 走 NODE_PATH 兜底解析（execjs 把 JS 写到临时文件执行，无法靠 cwd 找到包） |
| 3 | `PYTHONPATH=/app:/bili-common` | 挂载 `./bili-common:/bili-common` 后，公共包改动同样即时生效；不挂载时该路径不存在，Python 自动忽略，回落到 venv 内的非 editable 副本 |
| 4 | 运行阶段仍 `COPY --from=crawler-build /app /app` | 镜像自带一份源码兜底（与 message 的 `/app/app` 兜底一致）；被 bind mount 覆盖时不影响 |

### 3.2 `docker-compose.yml`（be-bilibili-crawler）

| # | 改动 | 理由 |
|---|---|---|
| 1 | 新增 `- ./be-bilibili-crawler:/app` | 热更新本体 |
| 2 | 新增 `- ./bili-common:/bili-common` | 配合 §3.1-3 |
| 3 | 保留 `- ./docker_vol/fastapi/log:/app/scripts/log` | 更具体的子路径挂载优先于父路径 `/app`，日志仍落宿主机 |
| 4 | 删除 `action: sync+restart` 规则，保留 `uv.lock` / `pyproject.toml` 的 `action: rebuild` | 源码已挂载，sync 无意义；依赖变更仍需重建镜像（venv 属于镜像） |

### 3.3 依赖裁剪（联动瘦身计划书）

`[dependency-groups].dev` 的 `playwright>=1.55.0` 删除：全仓只用
`from patchright.async_api import ...`（`Service/PlayWright/Operator.py`），
浏览器安装早已改用 `uv run patchright install chromium`。详见
`docs/be-bilibili-crawler-依赖瘦身计划书.md` §3.2 / §4.1。

### 3.4 连带修复（bug）

`Service/toutiao/src/Tools/Enc/ToutiaoDecrypt.py` 里
`execjs.compile(..., cwd=_current_file_dir + '/node_modules')` 指向**不存在的目录**，
`subprocess.Popen(cwd=...)` 会在实例化时抛 `FileNotFoundError`（宿主机/容器同样复现）。
改为 cwd = 脚本所在目录（`__file__` 的 dirname），包解析交给 `NODE_PATH`。

## 4. 风险与回滚

| 风险 | 缓解 |
|---|---|
| `require('jsdom'/'md5')` 在容器里找不到 | 依赖 `NODE_PATH=/opt/node_modules`（Node 仍支持该变量）；验收时容器内跑一次 `execjs` 冒烟 |
| 整目录挂载后宿主机被写入 root 属主文件（`__pycache__`、`Service/PlayWright/user_data/`、`Service/samsclub/api/app_storage.json`） | 仅开发机场景；必要时用 `dev_init_chmod.bash` 同款 chmod 兜底 |
| 宿主机 `.venv` / `package.json` 等一起进了容器 | 均不在 `sys.path` / `NODE_PATH` 解析链上，无副作用（`UV_PROJECT_ENVIRONMENT=/opt/venv`） |
| `bili-common` 源码与 venv 内副本漂移 | 挂载时以源码为准（PYTHONPATH 优先于 site-packages）；依赖变更仍需 rebuild |
| 依赖层缓存失效 | `npm install` / `uv sync --locked --no-install-project` / chromium 三层仍排在 `COPY be-bilibili-crawler/ .` 之前，源码改动不影响它们 |

回滚：`git revert` 本提交 + 恢复 `uv.lock`，重新 `docker compose build be-bilibili-crawler`。

## 5. 验收标准

1. `uv lock` 后 `uv sync --locked` 可完成，`uv.lock` 中不再有 `playwright`；
2. `docker compose config` 解析通过，`be-bilibili-crawler` 挂载点含 `/app`、`/bili-common`、`/app/scripts/log`；
3. `docker compose build be-bilibili-crawler` 成功，镜像内：
   - `ls /opt/node_modules | grep -E '^(jsdom|md5)$'` 命中；
   - `ls /app/node_modules` 不存在（已被外移）；
   - `python -c "import patchright"` 成功，`import playwright` 失败；
4. 容器内 execjs 冒烟：
   ```bash
   docker run --rm -e NODE_PATH=/opt/node_modules <img> /opt/venv/bin/python - <<'PY'
   import execjs
   js = execjs.compile("const md5=require('md5'); function f(){return md5('a')}")
   print(js.call("f"))
   PY
   ```
5. 改一个 py 文件后 `docker compose restart be-bilibili-crawler`，容器内 `/app` 读到新内容，日志出现新的 uvicorn 启动行；
6. 改 `bili-common` 后同样只需 restart。
