# 依赖与兼容范围

本清单依据本机源码、`requirements.lock.txt` 和打包测试，不代表其他软件版本已获验证。

| 层次 | 依赖 | 是否包含 |
|---|---|---|
| 系统 | Windows x64 | 目标平台 |
| Houdini GUI | 本机基线 Houdini FX 22.0.368、Python 3.13 | 程序与许可证需自行安装 |
| Houdini 内部模块 | `hou`、PySide6（代码保留 PySide2 回退）、`numpy`、`requests` | 由 Houdini 环境提供，需检查 |
| stdio 桥接 Python | Python 3.12 x64；本机 3.12.13 | 需自行安装，附创建 venv 脚本 |
| 核心直接依赖 | `mcp[cli]==1.29.1`、`requests==2.34.2`、`python-dotenv==1.2.3` | 已包含离线 wheels |
| 核心传递依赖 | 锁定文件中的 41 个包 | 已包含对应 wheels；另含解析器下载的条件依赖 exceptiongroup |
| HIP 静态分析脚本 | Python 标准库（pathlib/re/sys/os） | 脚本已包含，不需第三方 pip 包 |
| 手册学习 | 可访问官方手册的网络/浏览工具 | 历史笔记和模板已包含，手册网站未离线镜像 |
| 城市 PCG 扩展 | 根据任务选用 JOSM/Java、OSM 数据、SideFX Labs、UE5/Houdini Engine、资产库 | 可选、未包含，核心 MCP 不依赖这些 |
| OPUS 6 个工具 | 用户自己的 RapidAPI/OPUS 服务配置 | 未启用、未测试，只有空配置模板 |
| OPUS 参数解析辅助 | `langchain-classic>=1.0.0`（源码也尝试旧 langchain 解析器） | 可选、未锁定、未提供离线 wheels |

## 复现核心环境

`houdini-mcp/requirements.lock.txt` 是原机器的完整核心环境锁定快照；`requirements.in` 标明直接依赖。安装器默认仅从离线目录装锁定版本，随后运行 `pip check`。

离线 wheels 专用于 Windows x64 / CPython 3.12。不能将原机器 `.venv` 直接复制到新路径，也不能将这些二进制 wheels 装进 Houdini Python 3.13。其他操作系统和 Python 次版本需要重新获取兼容包，本包不承诺可直接使用。

## Houdini 内部依赖检查

在 Houdini GUI 的 Python Shell 运行：

```python
import hou, numpy, requests; from PySide6 import QtCore; print(hou.applicationVersionString(), numpy.__version__, requests.__version__)
```

`hou` 与 Qt 应由 Houdini 提供，不要在桥接 venv 中安装同名替代包。若仅缺少 requests，可使用你自己的兼容 Python 包源补入该 Houdini 版本的 Python 搜索路径；本包离线桥接 wheels 的 cp312 文件不适用于 Houdini 3.13。请先核实 Houdini 内置环境，避免覆盖自带 numpy/Qt。

## OPUS 与上游 pyproject 的区别

原始 pyproject.toml 列有 langchain/langchain-classic，但本机运行环境没有它们；源码捕获 ImportError，核心 19 个工具可正常工作。为复现实际环境，安装器使用锁定清单，不使用 `pip install .` 引入这部分可选依赖。

如确实需要 OPUS 参数格式辅助，可在独立桥接 venv 中联网安装 `langchain-classic>=1.0.0`，然后执行 `pip check` 和 `verify_mcp.py` 重新验证。这会改变本包的核心锁定环境，应另外导出新的 freeze 清单。填写 OPUS 凭据后仍需验证外部服务可达性，本包没有进行外部付费调用。

## 旧版本与机器特有配置

Houdini 21 的记录仅保留用于追溯。本版 UI hook 在 `python3.13libs/`，其他 Houdini/Python 版本需调整钩子目录并重新验证。原机器的 `shfs-location.json` 用于 H/C 盘混合安装修复，不是 MCP 依赖，因此没有安装到目标机器；遇到 SHFS 问题请依据目标 Houdini 实际安装位置处理。
