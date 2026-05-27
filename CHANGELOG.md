# Changelog

## [0.0.4] - 2025-05-27

### Changed

- **合并搜索入口**: `search.py` 和 `search_chroma.py` 合并为统一的 `obsidian2vector-search` 命令，根据 `db_type` 配置自动选择 Milvus 或 Chroma 后端
- 添加 `main()` 函数以支持 `pyproject.toml` 入口点调用
- **MCP Server 异步加载**: 将嵌入模型、DB 连接、Vault 解析移至后台线程，MCP server 先启动返回 schema，避免 agent 超时

### Removed

- 移除 `search_chroma.py`（合并入 `search.py`）
- 移除 `obsidian2vector-search-chroma` 入口点

## [0.0.3] - 2025-05-26

### Fixed

- Remove all non-ASCII characters (Chinese/emoji) from print output to fix Windows GBK encoding crash on MCP server startup

## [0.0.2] - 2025-05-25

### Changed

- **配置方式重构**: 从环境变量改为 `~/.obsidian2vector/settings.json` 文件配置，跨平台支持 (macOS/Linux/Windows)，环境变量仍可用作覆盖
- **MCP Server 独立发布**: 拆分为 `obsidian2vector-mcp` 独立 PyPI 包，依赖 `obsidian2vector` 核心包
- **合并索引器**: `indexer.py` 和 `indexer_chroma.py` 合并为统一的 `obsidian2vector-index` 命令，根据 `db_type` 配置自动选择数据库
- 更新 README 为非源码安装使用方式

### Removed

- 移除 `mcp_server.py`、`mcp_test.py`（迁移至独立包）
- 移除 `indexer_chroma.py`（合并入 `indexer.py`）

## [0.0.1] - 2025-05-20

### Added

- Obsidian Vault Markdown 解析（frontmatter、tags、wiki links）
- 向量嵌入支持 BGE / Qwen3-Embedding 模型
- Milvus / Chroma 向量数据库支持
- FastAPI REST 搜索接口
- MCP Server 支持
- PyPI 打包结构
