# Desktop Delivery

当前仓库已经补入 `Tauri 2` 桌面壳骨架，位置在 `apps/client/src-tauri`。

## 当前目标

- 让前端 React/Vite 工作台具备桌面端外壳
- 保留当前 `FastAPI + uv` 后端作为本地研究服务
- 为 Windows、macOS、Linux 后续打包预留统一入口
- 支持用户双击桌面应用后自动拉起本地 API 服务

## 已补入内容

- `apps/client/src-tauri/Cargo.toml`
- `apps/client/src-tauri/build.rs`
- `apps/client/src-tauri/src/main.rs`
- `apps/client/src-tauri/src/lib.rs`
- `apps/client/src-tauri/tauri.conf.json`
- `apps/client/src-tauri/capabilities/default.json`
- 根目录一键脚本：
  - `pnpm dev:desktop`
  - `pnpm desktop:doctor`
  - `pnpm build:api-sidecar`
  - `pnpm build:desktop`

## 双击即启动（打包版）

当前桌面壳在发布构建中会自动执行以下动作：

1. 打包前执行 `pnpm build:api-sidecar`，把 `apps/api` 构建为单文件可执行程序
2. 把 sidecar 二进制打进桌面应用资源目录（`src-tauri/binaries/*`）
3. 用户双击应用时，桌面壳会先检测 `127.0.0.1:8000`
4. 如果 API 未运行，则自动拉起 sidecar，并等待服务就绪

这意味着最终用户只需要双击桌面应用，不需要再手动启动 `uvicorn`。

## 开发模式

`pnpm dev:desktop` 会做两件事：

1. 在 `apps/api` 下启动 `uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
2. 在 `apps/client` 下启动 `pnpm tauri dev`

前端仍通过 `http://127.0.0.1:8000` 访问研究 API。

## 当前机器的阻塞项

当前机器如果已经安装 Rust，`desktop:doctor` 会继续检查 Linux 侧图形依赖。

如果输出里出现：

- `tauri-prereqs: missing`

通常说明缺少：

- `libwebkit2gtk-4.1-dev`
- `librsvg2-dev`

以及相关 Linux 打包依赖。

可以先运行：

```bash
pnpm desktop:doctor
```

如果输出里 `rustc` / `cargo` 为 `missing`，先安装 Rust 工具链。
如果输出里 `tauri-prereqs: missing`，在 Ubuntu/WSL 下安装：

```bash
sudo apt install libwebkit2gtk-4.1-dev librsvg2-dev build-essential curl wget file libxdo-dev libssl-dev libayatana-appindicator3-dev
```

## 下一步建议

1. 安装 Rust 工具链与 Tauri 平台依赖
2. 在本机执行 `pnpm install`
3. 执行 `pnpm dev:desktop`
4. 确认桌面壳启动、前端加载、后端连通
5. 再推进：
  - sidecar 健康探针与日志上报
  - Windows/macOS/Linux bundle 配置细化（签名、安装参数）
   - Android 壳层与移动端权限

## Windows 构建命令

建议在 Windows 主机本地执行：

```bash
pnpm install
pnpm desktop:doctor
pnpm build:desktop:windows
```

`build:desktop:windows` 会在打包前先构建 API sidecar，然后仅打包 Windows 安装格式：

- `msi`
- `nsis`

产物位于：

- `apps/client/src-tauri/target/release/bundle/`
