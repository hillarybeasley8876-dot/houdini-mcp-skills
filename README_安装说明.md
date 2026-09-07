# Houdini MCP + 5 个 Houdini Skills

本包来自你在 2026-09-08 的本机安装，目标环境为 **Windows x64、Houdini 22（Python 3.13）、独立 Python 3.12**。保留本机已修复的 UI 事件循环与 FastMCP 兼容处理，默认端口 **9877**。

## 包内内容

| 目录或文件 | 内容 |
|---|---|
| `houdini-mcp/` | 可迁移的 MCP 桥接、Houdini 插件、自动启动钩子、工具架 |
| `skills/` | 5 个完整 skill，含脚本、模板与参考文档 |
| `knowledge/` | Houdini 专用学习记忆与手册学习进度快照 |
| `dependencies/wheels-win64-py312/` | 核心桥接依赖的离线 wheel 文件 |
| `install.ps1`、`install.py` | 创建环境、安装 skill、注册 Houdini package、生成客户端配置 |
| `verify_mcp.py` | MCP 握手、25 个工具枚举、可选只读场景检查 |
| `source/` | 原版 skills、未改动上游源码及原机器安装说明，仅供追溯 |
| `DEPENDENCIES.md` | 必需与可选依赖、版本、限制 |
| `SHA256SUMS.txt` | 包内文件校验清单 |

5 个 skill：`houdini-mcp`、`houdini-architect-analysis`、`houdini-manual-deepdive`、`houdini-pcg-practitioner`、`houdini-pcg-city-pipeline`。

## 1. 准备环境

1. 安装并能够正常启动 Houdini 22 GUI。原机器基线为 22.0.368；Houdini 程序、许可证不在本包内。
2. 安装 **Windows x64 Python 3.12**，包含 `venv`/`ensurepip`。桥接不使用 Houdini 自带 Python，也不要使用 Python 3.10/3.13 创建本包的桥接环境。
3. 将整个压缩包解压到长期保存的目录，例如 `D:\Tools\Houdini-MCP-Skills-20260908`。安装后不要移动它；如需移动，重新创建 `.venv` 并重新生成配置。
4. 在 Houdini 的 Python Shell 运行以下只读命令，记录实际用户偏好目录：

```python
print(hou.getenv('HOUDINI_USER_PREF_DIR'))
```

使用 GUI 返回的目录。它可能在 `Documents\houdini22.0`，也可能在用户目录下；不要直接复制原机器路径。

## 2. 安装

在解压目录打开 PowerShell，将下面的偏好目录替换成上一步输出：

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -HoudiniPrefDir 'C:\Users\你的用户名\Documents\houdini22.0'
```

默认通过 `py -3.12` 调用 Python；找不到 Python Launcher 时指定 Python 3.12 的完整路径：

```powershell
.\install.ps1 -HoudiniPrefDir 'D:\HoudiniPrefs\houdini22.0' -PythonExe 'D:\Python312\python.exe'
```

安装器默认使用包内离线 wheels，不访问软件包索引。若需要联网重新安装依赖，加 `-Online`。默认把 5 个 skill 安装到 `$env:USERPROFILE\.agents\skills`；可用 `-SkillsDir` 指定其它客户端的 skill 目录，或 `-SkipSkills` 跳过。原同名 skill 和 Houdini package 会先复制到包内 `backups/`，再更新；不会改写用户的整个 MCP 客户端配置。

端口冲突时加 `-Port 9878` 等参数。Houdini package 和生成的桥接参数会同时采用新端口；验证命令也要加 `--port 9878`。

## 3. 配置 MCP 客户端

安装后在 `config/generated/` 找到使用本机真实路径生成的配置。

**Codex**：将 `codex.houdini.toml` 中的 `[mcp_servers.houdini]` 节合并到 `$env:USERPROFILE\.codex\config.toml`。已有同名节时替换该节，不能重复添加，也不要覆盖其他 MCP 配置。保存后重启 Codex。

**Claude Desktop**：把 `claude-desktop.mcp.json` 的 `mcpServers.houdini` 项合并到 Desktop 的 MCP 配置文件，然后重启客户端。

**Claude Code 或其他客户端**：`claude-code.houdini.json` 提供标准 stdio server 的 `type`、`command` 和 `args`；按客户端支持的导入方式使用。注册 MCP 与安装 skills 是两件事，skill 搜索目录也需指向实际安装位置。若需要 Claude skills，可另行用 `-SkillsDir "$env:USERPROFILE\.claude\skills"` 安装，保留 Codex 中已有的副本。

所有客户端必须使用 `houdini-mcp\.venv\Scripts\python.exe` 运行桥接脚本，参数包含 `--port 9877`（或自定义端口）。无需单独保持一个桥接终端运行。

## 4. 启动与检查

重启 Houdini GUI，UI 就绪后应自动监听 `127.0.0.1:9877`。状态记录在 `houdini-mcp/last-start.json`；工具架 `MCP` 提供 Start MCP / Stop MCP。

先做不依赖 Houdini 场景的握手检查：

```powershell
& .\houdini-mcp\.venv\Scripts\python.exe .\verify_mcp.py
```

应输出 `handshake: PASS`、`tools: 25`。这只能说明桥接可用。打开 Houdini 后再做真实往返检查：

```powershell
& .\houdini-mcp\.venv\Scripts\python.exe .\verify_mcp.py --scene
```

应出现 `scene: PASS`；此检查只读取场景。手动启动插件可在已载入 package 的 Houdini Python Shell 执行：

```python
import os, runpy; runpy.run_path(os.path.join(os.environ['HOUDINI_MCP_ROOT'], 'start_mcp.py'))
```

若没有 `HOUDINI_MCP_ROOT`，通常是 package 目录错误或尚未重启。检查 `$HOUDINI_USER_PREF_DIR/packages/houdinimcp.json`、Houdini 控制台与端口是否被占用。

## 5. 可选 OPUS

核心 19 个工具无需 API 密钥。6 个 `opus_*` 工具需要外部服务配置，原环境也未启用。

将 `houdini-mcp/scripts/python/houdinimcp/urls.env.example` 复制为同目录 `urls.env`，填写自己的 `RAPIDAPI_KEY`、`RAPIDAPI_HOST`、`RAPIDAPI_HOST_URL`。服务地址与授权应以自己的账户配置为准。`langchain-classic` 可改善参数格式说明，但未纳入本机核心依赖锁定与离线包；详见依赖说明。

## 6. 学习资料与历史路径

安装用 `skills/` 已调整 MCP 配置说明和手册知识库路径。手册进度安装到 `houdini-manual-deepdive/knowledge/houdini_manual/`，Houdini 记忆安装到 `houdini-mcp/references/memory/`。这两个位置可由 agent 继续读写，`knowledge/` 则是打包时快照。

原文中的 `C:\Users\nieyi`、`C:\Users\Administrator`、H 盘、Houdini 21 路径只代表历史来源，不是新机器配置。记忆中提及的外部 `.hip` 项目、`houdini_study` 目录与第三方原始课程素材未随包迁移；内嵌的 VEX 配方、模板和总结已包含。旧 MCP 修复步骤不可覆盖本版实现。

## 7. 备份、移除与校验

运行 `py -3.12 .\verify_integrity.py` 可核对原始文件；安装生成的 `.venv`、配置与日志不参与校验。修改原始 skill 后校验提示改变是正常现象。

移除时先在客户端删去 `houdini` MCP 项，再移除对应 Houdini package；如需恢复，使用 `backups/` 中的原文件。技能可单独保留。确认不再被配置引用后再删除解压目录。

本包没有用户密钥、登录配置、会话历史或原机器虚拟环境。上游 MIT 许可证位于 `source/upstream/LICENSE`，各 wheel 自带其许可证元数据；原 skill 的来源与原文保留在 `source/original-skills/`。
