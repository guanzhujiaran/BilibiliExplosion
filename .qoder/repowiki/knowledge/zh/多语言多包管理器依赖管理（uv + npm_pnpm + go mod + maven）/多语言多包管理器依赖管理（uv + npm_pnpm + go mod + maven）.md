---
kind: dependency_management
name: 多语言多包管理器依赖管理（uv + npm/pnpm + go mod + maven）
category: dependency_management
scope:
    - '**'
source_files:
    - RPA-Browser/pyproject.toml
    - RPA-Browser/uv.lock
    - be-bilibili-crawler/pyproject.toml
    - be-bilibili-crawler/uv.lock
    - be-message-service/pyproject.toml
    - bili-common/pyproject.toml
    - Vue3FrontEndDemoExercise/package.json
    - Vue3FrontEndDemoExercise/package-lock.json
    - be-gateway/package.json
    - be-gateway/package-lock.json
    - go-proxy-ipv6-pool-auto/go-proxy-ipv6-pool/go.mod
    - go-proxy-ipv6-pool-auto/go-proxy-ipv6-pool/go.sum
    - unidbgSpringBoot/pom.xml
    - unidbgSpringBoot/.mvn/wrapper/maven-wrapper.properties
---

## 1. 使用的系统与工具

仓库是一个多语言微服务聚合项目，每个子模块使用各自生态的标准包管理器进行依赖声明与锁定：
- Python 服务（RPA-Browser、be-bilibili-crawler、be-message-service、bili-common）统一使用 **uv**（`pyproject.toml` + `uv.lock`），并通过 `[[tool.uv.index]]` 配置多个国内 PyPI 镜像源。
- Vue3 前端（Vue3FrontEndDemoExercise）使用 **pnpm**（`package.json` 中声明 `packageManager: "pnpm@11.14.0"`），并生成 `package-lock.json` 锁定依赖。
- Express 网关（be-gateway）使用 **npm**，通过 `package.json` + `package-lock.json` 管理。
- Go IPv6 代理池（go-proxy-ipv6-pool-auto/go-proxy-ipv6-pool）使用标准 **go mod**（`go.mod` + `go.sum`）。
- unidbg Spring Boot 服务使用 **Maven**（`pom.xml` + `.mvn/wrapper/maven-wrapper.properties`），通过 Maven Wrapper 固定构建工具版本。

## 2. 关键文件

- Python 层：`RPA-Browser/pyproject.toml`、`RPA-Browser/uv.lock`；`be-bilibili-crawler/pyproject.toml`、`be-bilibili-crawler/uv.lock`；`be-message-service/pyproject.toml`、`be-message-service/uv.lock`；`bili-common/pyproject.toml`。
- 前端层：`Vue3FrontEndDemoExercise/package.json`、`Vue3FrontEndDemoExercise/package-lock.json`；`be-gateway/package.json`、`be-gateway/package-lock.json`。
- Go 层：`go-proxy-ipv6-pool-auto/go-proxy-ipv6-pool/go.mod`、`go.sum`。
- Java 层：`unidbgSpringBoot/pom.xml`、`unidbgSpringBoot/.mvn/wrapper/maven-wrapper.properties`。
- 根级编排：`docker-compose.yml`、`dc-dev.yml` 将各服务容器化后组合运行。

## 3. 架构与约定

### 3.1 内部公共包 bili-common
`bili-common` 作为仓库内共享的 Python 包，被 RPA-Browser、be-bilibili-crawler、be-message-service 三个服务通过 `[[tool.uv.sources]]` 中的 `path = "../bili-common", editable = true` 引用。注释明确说明：本地开发以 editable 方式安装以便即时修改生效；Docker 构建时通过 `UV_NO_EDITABLE=1` 环境变量强制按非 editable 安装，使 `bili-common` 被复制进 site-packages，保证静态分析工具（ty）可解析且不依赖宿主机绝对路径。

### 3.2 PyPI 镜像与索引策略
所有 Python 子项目均在 `pyproject.toml` 中声明了 `python-install-mirror = "https://registry.npmmirror.com/-/binary/python-build-standalone/"` 用于加速 Python 解释器下载，并通过 `[[tool.uv.index]]` 配置阿里云为默认源，同时追加腾讯云、清华 tuna、中科大 USTC、北服 bfsu、火山引擎、华为云等多个国内镜像源。be-bilibili-crawler 还设置了 `index-strategy = "unsafe-best-match"`，允许 uv 在冲突时选择最优匹配而非严格一致。

### 3.3 前端依赖锁定
Vue3 前端使用 pnpm 但依然保留 `package-lock.json`（lockfileVersion 3），be-gateway 也使用 npm 的 `package-lock.json`，两者均通过锁文件确保依赖树可重现。

### 3.4 Go 与 Java 依赖
Go 模块 `go.mod` 直接声明 `require` 列表及 `go 1.25.1` 版本，`go.sum` 提供校验和。Java 模块通过 `pom.xml` 声明 Spring Boot parent 3.5.5 与 unidbg 0.9.8，并在 `repositories` 中额外添加 Spring Milestones/Snapshots 仓库以获取预发布构件；Maven Wrapper 固定使用 3.9.9 版本。

### 3.5 二进制/外部依赖
RPA-Browser 的 `app/chrome/` 下直接存放多个版本的 `ungoogled-chromium-*.AppImage` 二进制文件，由 `scripts/initd/install_ungoogled_chromium.py` 脚本在安装阶段处理；`botright/modules/geetest.torchscript` 等模型文件也以源码形式随仓库提交。这些不属于包管理器管理的依赖，而是以文件形式 vendored。

## 4. 约定与约束

- **Python 子项目必须使用 pyproject.toml + uv.lock 双文件**：所有 Python 服务都遵循该模式，新增 Python 服务应沿用此约定。
- **内部包 bili-common 必须以 path 方式引用**：通过 `[[tool.uv.sources]]` 的相对路径引用，禁止将其发布到 PyPI 后再引入，以保证多服务共享同一份源码。
- **PyPI 访问必须走配置的国内镜像**：`pyproject.toml` 中已集中声明阿里云为主源，新增依赖时应保持镜像源一致，避免直连 pypi.org。
- **前端依赖必须提交锁文件**：pnpm 项目仍保留 `package-lock.json`，npm 项目同样提交锁文件，变更依赖需更新锁文件。
- **Go/Java 依赖通过标准 lock 文件锁定**：`go.sum` 与 `pom.xml` 中显式版本号是构建可重现性的依据，升级时需同步更新对应文件。
- **二进制/模型类资源不纳入包管理器**：Chromium AppImage、torchscript 模型、GeoIP mmdb 等以文件形式随仓库或挂载卷分发，不在 `pyproject.toml`/`package.json` 中声明。
- **Docker 构建对 bili-common 的隔离**：通过 `UV_NO_EDITABLE=1` 环境变量切换安装模式，确保生产镜像不依赖源码目录结构。