---
name: houdini-mcp
description: Set up, connect, verify and troubleshoot Houdini 22 MCP on Windows. Use for Houdini MCP installation, restart, reconnection and live control diagnostics.
---

# Houdini MCP（可迁移版）

当前打包基线：Houdini 22.0.368 / 内置 Python 3.13，独立桥接 Python 3.12，MCP 1.29.1。
默认监听 `127.0.0.1:9877`。9876 在原机器用于 Blender；不要沿用旧笔记中的 9876。

## 配置与启动

安装包根目录的 README_安装说明.md 与 DEPENDENCIES.md 是本版配置依据。
由 install.ps1 生成 Houdini package、MCP 配置片段和独立 .venv。
在目标机器先查实际 MCP 配置中的 command/args，确定插件根目录及端口，不能假定原作者用户名或盘符。
Houdini package 设置 HOUDINI_MCP_ROOT 与 HOUDINI_MCP_PORT。
Houdini 22 UI 就绪后 python3.13libs/uiready.py 使用 runpy 调用 start_mcp.py。
已在运行的 GUI 中可执行一行：
`import os, runpy; runpy.run_path(os.path.join(os.environ['HOUDINI_MCP_ROOT'], 'start_mcp.py'))`
环境变量只会在载入 package 后存在；首次安装须重启 Houdini。

## 排障顺序

1. 检查 Houdini GUI 进程及实际 HOUDINI_USER_PREF_DIR，hython 的偏好目录不能替代 GUI 结果。
2. 核对 package hpath、HOUDINI_MCP_PORT 与桥接 --port 相同。
3. 检查 localhost 端口监听以及插件目录 last-start.json。
4. 用包内 verify_mcp.py 完成 stdio 握手和工具枚举；再加 --scene 进行只读往返验证。
5. 故障时检查 Houdini 控制台。插件需 initialize_plugin() 后 start_server(host='127.0.0.1', port=实际端口)。

实现使用 hou.ui.addEventLoopCallback、server_socket 字段和 FastMCP instructions 参数；
不要复制旧笔记中的 QTimer、socket 字段或导入即自动启动的修复片段。
协议为 4 字节大端长度 + UTF-8 JSON。GUI 操作必须在 Houdini UI 进程执行。

## 功能与依赖

19 个核心工具不需要外部 API 密钥；6 个 OPUS 工具依赖用户自己的 RapidAPI/OPUS 配置。
桥接进程由 MCP 客户端启动；Houdini 负责场景、hou、Qt、numpy 及渲染。
不能通过 pip 安装 hou 来代替 Houdini。

## 配套知识

Houdini 专用记忆在 references/memory/；原始文档保留历史路径与旧版记录，使用前按本版配置校正。
PCG 建造参见 houdini-pcg-practitioner、houdini-pcg-city-pipeline；项目分析参见 houdini-architect-analysis；手册学习参见 houdini-manual-deepdive。
