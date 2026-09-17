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
| `datasets>=5.0.0` | 5.2M | 全仓 0 引用 | `pyarrow` 156M、`huggingface_hub` 6.8M、`multiprocess`、`dill`、`fsspec` 1.9M（**已实施**：2026-09-17 复核 `uv.lock` / `uv tree --no-dev` 中已无 `datasets` 与 `pyarrow`，见 §7） |
| `modelscope==1.37.1` | 66M | 全仓 0 引用（仅 `"modelscope达摩机器学习"` 字符串出现在 `ApiRoutes/__init__.py` 的枚举注释里）；其 wheel 关联的 `models/*.onnx`（58M）同样无代码引用、且已被 `.gitignore` 排除 | 无独占子依赖（filelock / packaging / requests / tqdm / urllib3 均为公共依赖）（**已实施**：`uv.lock` 中已无 `modelscope`） |
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

## 7. 实施记录（2026-09-17）

### 7.1 已落地的删除

| 依赖 | 落地动作 | 复核结果 |
|---|---|---|
| `datasets` | 从 `[project.dependencies]` 删除 | `uv.lock` 无 `datasets`；`uv tree --no-dev` 顶层 60 包中无此项 |
| `pyarrow` | **不做单独声明**，作为 `datasets` 的独占子依赖连带消失 | `uv.lock` 无 `pyarrow`；`uv tree --package pyarrow --invert` 无输出（无上游） |
| `modelscope` | 从 `[project.dependencies]` 删除 | `uv.lock` 无 `modelscope` |
| `playwright>=1.55.0` | 从 `[dependency-groups].dev` 删除并 `uv lock` | `Removed playwright v1.62.0`；浏览器安装早已切到 `uv run patchright install chromium` |

### 7.2 关键结论：`uv` 下传递依赖只能「断上游」

- `uv` 没有 pip 那种「排除某个传递依赖」的开关：`--no-deps` 只对直接安装的包生效；
  `[tool.uv] override-dependencies` / `constraint-dependencies` 只能改版本或改源，**不能移除包**。
- 因此 `pyarrow` 的正确做法是**删掉引入它的顶层包**（`datasets`），而不是试图在 lock 里剔除它。
- 兜底手段（不推荐，lock 与运行期不一致，必须冒烟）：Dockerfile 里 `uv sync --locked` 之后追加
  `RUN uv pip uninstall -y pyarrow`。

### 7.3 venv 体积现状（`du -sh site-packages/* | sort -rh` 实测，本地 `.venv`）

| 包 | 体积 | 结论 |
|---|---|---|
| `patchright` | 139M | 唯一浏览器驱动，保留 |
| `playwright` | 137M | lock 已删，**残留需 `uv sync --locked` 物理移除** |
| `scipy` + `scipy.libs` | 138M | `scikit-learn` 的子依赖 |
| `pandas` | 72M | 8 处在用，保留 |
| `sklearn` | 50M | `LotteryClassifier.py` 在用，保留 |
| `numpy` + `numpy.libs` | 71M | 公共底座，保留 |
| `curl_cffi` / `bili_ticket_gt_python` / `babel` / `jieba3` | 38M / 37M / 33M / 30M | 核心爬虫 / 风控 / i18n / 词云，保留 |
| `langchain_community` | 24M | 见 §7.4 候选① |
| `zstandard` | 23M | 上游已变成 `langsmith`（`uv tree --package zstandard --invert`），不再是 `datasets` |
| `sqlalchemy` / `openai` | 23M / 20M | 在用，保留 |

### 7.4 下一步候选（**待评估，实施前需在本计划书登记并 grep 复核零引用**）

| 候选 | 依据 | 预期收益 |
|---|---|---|
| ① 删 `langchain`（顶层）与 `langchain-community` | 项目代码（排除 `.venv` / `test/`）对 `langchain_community`、`from langchain.*`、`import langchain.*` **零引用**；实际只用 `langchain_core` + `langchain_openai`（`Service/llm_service/*`、`Service/LangChainCompo/chains.py`） | `langchain_community` 24M + `langchain` 1.4M + `langchain-classic` + `langgraph` 3.4M，并连带断掉 `langsmith` → `zstandard` 23M / `xxhash` |
| ② 删 `langchain-ollama` | 若线上只走 OpenAI 兼容 API（`llm_apis` + `llama_cpp`），可评估 | 232K（收益小，主要收益是依赖树变干净） |
| ③ `browserforge[all]` → `browserforge` | 代码只用 `browserforge.fingerprints.FingerprintGenerator`（`Utils/加密/utils.py`） | 取决于 extras 多装的子依赖，需 `uv tree --package browserforge` 复核 |
| ④ 不动 | `scikit-learn` / `scipy` / `pandas` / `numpy` / `fastapi[all]` | 均在用或收益不成比例（计划书 §3.4） |

> 注意：venv 属于**镜像层**（`UV_PROJECT_ENVIRONMENT=/opt/venv`），本地 `uv sync` 或改 `uv.lock`
> 都不会让运行中的容器生效，必须 `docker compose build be-bilibili-crawler`；
> 源码改动则不需要（已改为 bind mount，见 `docs/be-bilibili-crawler-容器热更新计划书.md`）。

### 7.5 依赖版本回归修复：`strawberry-sqlalchemy-mapper` pin 0.8.0

| 项 | 内容 |
|---|---|
| 现象 | 容器与本地 `uv run` 均报 `TypeError: SpuPriceInfoType fields cannot be resolved. Unexpected type 'strawberry_sqlalchemy_mapper.scalars.BigInt'`（`main.py` 导入 `Service/samsclub/Sql/SdlHelper.py` 即崩，容器反复重启） |
| 根因 | `strawberry-sqlalchemy-mapper 0.9.0` 的 `scalars.py` 把 `BigInt` 定义成 `NewType("BigInt", int)`，`strawberry-graphql 0.327.7` 不再把它解析为 GraphQL 标量；0.8.0 无此问题 |
| 修复 | `pyproject.toml` 将 `strawberry-sqlalchemy-mapper>=0.7.0` 改为 `==0.8.0`（保留 `strawberry-graphql[fastapi]>=0.284.1`，当前 0.327.7），随后 `uv lock` |
| 验证 | 本地 `.venv` 降至 0.8.0 后 `import Service.samsclub.Sql.SdlHelper` → `IMPORT OK`；容器重建后 uvicorn 正常启动 |
| 回滚 | 若上游修复该回归，解除 pin 并重新 `uv lock` |
