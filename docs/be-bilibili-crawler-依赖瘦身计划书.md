# be-bilibili-crawler 镜像依赖瘦身计划书

> 目标：把 crawler 镜像 4.4G 里**纯粹由无用 Python 依赖贡献**的那部分删掉
> 状态：**实施中**（2026-09-17）
> 关联：`Dockerfile.mono`（多阶段改造已实施，见本文 §3.1）

---

## 1. 背景

crawler 镜像 4.4G，其中 `/opt/venv` 实测 **1.4G**。逐包 `du` 后发现若干依赖**在代码中零引用**，
只是历史遗留留在 `pyproject.toml` 里。

同时发现：crawler 的 `.dockerignore`（`be-bilibili-crawler/.dockerignore`）在**根上下文**构建时
不会被 docker 读取（docker 只认 context 根目录的那份），因此 `models/*.onnx`（68MB）、`test/`、
`scripts/log/`、`Service/PlayWright/user_data/` 一直被打进镜像。

## 2. 瘦身手段与预期收益

| # | 手段 | 预计收益 |
|---|---|---|
| A | 多阶段构建 + apt 只留运行库（已实施） | ~700MB |
| B | 删除零引用依赖（本计划书） | ~400MB |
| C | `.dockerignore` 平移 crawler 自带的忽略清单（已实施） | ~70MB |
| D | 该措施之外：`playwright`/`patchright` 浏览器、node_modules 保留 | — |

## 3. 依赖裁剪清单

### 3.1 判定口径

「可删」= 全仓（排除 `.venv` / `node_modules` / `test/` / 生成的 `GrpcProto/`）grep
`(import|from) <pkg>` 命中数为 **0**，且没有其他包依赖它。动态导入（`importlib.import_module`）
已单独核查<｜hy_place▁holder▁no▁813｜>点（`Utils/FastAPI/alembic_manager.py`、`create_database.py`），二者只加载**本项目内部模块**。

### 3.2 删除项

| 依赖 | venv 体积 | 删除理由 | 连带删除 |
|---|---|---|---|
| `datasets>=5.0.0` | 5.2M | 全仓 0 引用 | `pyarrow` 156M、`zstandard` 23M、`huggingface_hub` 6.8M、`xxhash`、`multiprocess`、`dill`、`fsspec` 1.9M |
| `modelscope==1.37.1` | 66M | 全仓 0 引用（仅 `"modelscope达摩机器学习"` 字符串出现在 `ApiRoutes/__init__.py` 的枚举注释里）；其 wheel 关联的 `models/*.onnx`（58M）同样无代码引用、且已被 `.gitignore` 排除 | 无独占子依赖（filelock / packaging / requests / tqdm / urllib3 均为公共依赖） |
| `playwright>=1.55.0` | 137M | **代码只用 `from patchright.async_api import ...`**（`Service/PlayWright/Operator.py`）；`patchright` 不依赖 `playwright`（lock 中其依赖仅 `greenlet` / `pyee`），可独立工作。镜像里唯一用到它的是浏览器安装 CLI | 无（**已实施**：2026-09-17 从 dev 组删除并重新 `uv lock`，浏览器安装已切到 patchright CLI，见 §4.1 / §7） |

### 3.3 迁移项

| 依赖 | 处理 | 理由 |
|---|---|---|
| `grpcio-tools==1.82.0rc2`（7.9M） | 由 `[project.dependencies]` 移入 `[dependency-groups].dev` | 仅用于生成 `*_pb2.py` / `*_pb2_grpc.py`；运行期只需 `grpcio`。Docker 构建设了 `UV_NO_DEV=1`，dev 组不进镜像，本地仍能重新生成 stub |

### 3.4 明确保留

- `scikit-learn` → `LotteryClassifier.py` 实打实在用（`CountVectorizer` / `SVC` / `MultinomialNB`），连带保留 `scipy` 108M、`numpy`。
- `pandas` → 8 个模块在用（抽奖数据整理、词云）。
- `patchright`（139M）→ 唯一浏览器驱动，不可替代。
- `strawberry-graphql` / `strawberry-sqlalchemy-mapper` → `Service/samsclub/Sql/SdlHelper.py` 在用。
- `google`（= protobuf 命名空间）→ gRPC 生成代码大量 `from google.protobuf import ...`，不可删。
- `openai` / `langchain-openai` / `langchain-community` / `pymilvus` / `jieba3` / `opencc` / `curl-cffi` / `bili-ticket-gt-python` → 均有引用。
- `fastapi[all]` → 保留。`[all]` 相对 `[standard]` 多出的 `orjson`/`ujson`/`jinja2`/`email_validator`/`itsdangerous` 合计不足 5MB，收益不成比例，不值得为此改 runtime 行为。

## 4. 连带改动

### 4.1 浏览器安装 CLI

`playwright` 移出后，`uv run playwright install chromium` 不再可用，改为 patchright 自带的 CLI：

```dockerfile
RUN uv run patchright install chromium
```

patchright 自带 console script（`.venv/bin/patchright`），且遵循同样的
`PLAYWRIGHT_BROWSERS_PATH` 环境变量与 `ms-playwright` 目录约定，
因此浏览器仍落在 `/opt/playwright-browsers`，运行阶段 `COPY` 路径不变。

## 5. 风险与回滚

| 风险 | 缓解 |
|---|---|
| 删除后运行期 `ModuleNotFoundError` | 构建后容器内逐个 `import` 冒烟（见 §6.3）；判定口径已排除 test/生成代码，且 main 入口依赖链已核过（burn-in 见 §6.4） |
| `uv sync --locked` 因 lock 过期失败 | 改完 `pyproject.toml` 立刻 `uv lock`，并把 `uv.lock` 一并提交 |
| `uv run patchright install chromium` 与 patchright 运行时版本不匹配 | patchright CLI 与 SDK 同属一个 wheel，版本天然一致；安装后构建日志会打印 browser revision |

回滚：`git revert` 本提交 + 恢复 `uv.lock`，重新 `docker compose build` 即可。

## 6. 验收标准

1. `uv lock` 后 `uv sync --locked` 可完成，无冲突；
2. `/opt/venv` 体积由 1.4G 降到 ≤1.05G；
3. 容器内冒烟全部通过：
   ```bash
   docker run --rm <img> /opt/venv/bin/python - <<'PY'
   import patchright, sklearn, pandas, grpc, strawberry, langchain_openai, pymilvus, bili_ticket_gt_python
   for m in ("datasets", "modelscope", "playwright", "grpc_tools"):
       try:
           __import__(m); print(f"!! {m} 仍存在")
       except ModuleNotFoundError:
           print(f"OK {m} 已移除")
   print("import smoke OK")
   PY
   ```
4. `uvicorn main:app` 能完成 `main.py` 导入（本次构建复核 ` bili_ticket_gt_python` 在 glibc 2.38+ 下的 `ImportError`）；
5. 镜像总体积对比构建前后的 `docker images` SIZE。
