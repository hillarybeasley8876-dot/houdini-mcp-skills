# Houdini 22 MCP

安装日期：2026-09-06。已接入 Codex，全局服务器名为 `houdini`。

## 使用

打开 Houdini 22，插件将在界面就绪后自动监听 `127.0.0.1:9877`。首次安装后重启 Codex，以加载新的 MCP 工具。

若在已经启动的 Houdini 中需要手动加载，可在 Windows → Python Shell 执行以下一行：

```python
exec(compile(open(r'C:/Users/nieyi/Documents/houdini22.0/houdini-mcp/start_mcp.py', encoding='utf-8').read(), 'start_mcp.py', 'exec'))
```

工具架定义位于 `toolbar/MCP.shelf`，提供 Start MCP 和 Stop MCP。

## 验证结果

- Houdini FX 22.0.368，内置 Python 3.13。
- 独立 MCP 桥接环境：Python 3.12.13，MCP 1.29.1。
- 实际 GUI 自动启动成功，Houdini UI 事件循环回调成功注册。
- stdio 初始化、25 个工具枚举、场景读取和只读 Python 执行均通过。
- 验证仅使用单独的空白场景进程，完成后退出。
- OPUS 外部资产服务的 6 个工具需要另行配置 RapidAPI；核心 19 个工具不需要。

详细结果：`validation-ui.json`、`validation-mcp.json`。

## 配置位置

- 插件根目录：`C:/Users/nieyi/Documents/houdini22.0/houdini-mcp`
- Houdini 包配置：`C:/Users/nieyi/Documents/houdini22.0/packages/houdinimcp.json`
- 备用用户目录包配置：`C:/Users/nieyi/houdini22.0/packages/houdinimcp.json`
- 启动钩子：`python3.13libs/uiready.py`，可覆盖空白启动与打开已有 HIP 的情况。
- Codex：`C:/Users/nieyi/.codex/config.toml` 中的 `[mcp_servers.houdini]`。
- 桥接命令：`.venv/Scripts/python.exe scripts/python/houdinimcp/houdini_mcp_server.py --port 9877`。
- Blender MCP 保留原端口 9876。

本机 Houdini 安装于 H 盘，SHFS 共享资源实际位于 C 盘。两个用户目录下的 `packages/shfs-location.json` 将 SHFS 指向已有的 `C:/Program Files/Side Effects Software/shfs`，解决启动时的 “SHFS not properly setup” 提示。

## 来源与兼容处理

来源：https://github.com/capoomgit/houdini-mcp

提交：`de4fd93acc207fc57c02b330d421461f5963a945`。未修改的源码保存在 `upstream`。

已将 Qt 定时器改为 Houdini UI 事件回调，将 FastMCP 的 `description` 参数改为 `instructions`，并使用独立端口 9877。完整依赖版本保存在 `requirements.lock.txt`。

参考：https://www.sidefx.com/docs/houdini/hom/locations.html 和 https://www.sidefx.com/docs/houdini/ref/shfs.html 。
