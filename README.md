# Houdini MCP + Houdini Skills

Windows x64 / Houdini 22 的可迁移 MCP 安装包，附 5 个 Houdini skills、中文配置说明与 Python 3.12 离线依赖。

**开始使用：[中文安装说明](README_安装说明.md) · [依赖说明](DEPENDENCIES.md) · [验证记录](VALIDATION.json)**

## 包含内容

- Houdini MCP：桥接服务器、Houdini 插件、GUI 自动启动与工具架。
- 5 个 skills：连接排障、项目架构分析、官方手册学习、通用 PCG、城市 PCG。
- VEX 配方、分析脚本、学习模板和 Houdini 专用知识快照。
- 42 个离线 wheels，用于复现 41 个锁定的核心 Python 依赖。
- 安装脚本、Codex / Claude 配置生成、MCP 与文件完整性检查。

## 快速安装

准备 Houdini 22 和 Windows x64 Python 3.12；下载完整仓库到长期保存的目录。
在 Houdini Python Shell 执行 `print(hou.getenv('HOUDINI_USER_PREF_DIR'))`，将输出作为下面的目录参数：

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -HoudiniPrefDir 'C:\Users\你的用户名\Documents\houdini22.0'
```

安装后合并 `config/generated/` 中对应客户端的 Houdini MCP 配置，重启 Houdini 与客户端。

```powershell
& .\houdini-mcp\.venv\Scripts\python.exe .\verify_mcp.py
& .\houdini-mcp\.venv\Scripts\python.exe .\verify_mcp.py --scene
```

默认端口 `127.0.0.1:9877`。安装器默认离线安装依赖，并备份已有同名 skill/package。

## 已验证与范围

基线：Houdini 22.0.368、Houdini Python 3.13、桥接 Python 3.12.13、MCP 1.29.1。
打包时已通过全新环境离线安装、`pip check`、stdio 握手与 25 个工具枚举。
打包时没有运行中的 Houdini GUI，场景往返需在目标机器执行 `--scene` 验证。

19 个核心工具无需外部 API 密钥；6 个 OPUS 工具需要单独配置服务与凭据，未启用及测试。
Houdini 应用、许可证、Python 本体以及第三方课程原始工程未包含。

## 来源

MCP 上游：[capoomgit/houdini-mcp](https://github.com/capoomgit/houdini-mcp)，快照提交 `de4fd93acc207fc57c02b330d421461f5963a945`，保留 [MIT 许可证](source/upstream/LICENSE)。
本机兼容处理包括 Houdini UI 事件回调、FastMCP `instructions` 参数、独立端口，以及此次打包的相对路径与配置生成。
原始 skills 和安装文档位于 `source/`；其中的旧用户名、盘符及 Houdini 21 路径仅供历史追溯。

`SHA256SUMS.txt` 校验原始交付包的文件，仓库入口 README 与 Git 配置文件是额外的仓库说明。
