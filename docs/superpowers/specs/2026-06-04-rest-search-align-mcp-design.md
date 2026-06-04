# REST API Search 对齐 MCP 设计

## 背景

项目提供了两套搜索接口：MCP Server（通过 `obsidian2vector-mcp`）和 REST API（通过 `obsidian2vector-search`）。两者存在字段和行为不一致的问题。

## 目标

将 REST API 的 search 端点与 MCP `search_obsidian` 工具对齐，使得：

- 两套接口返回相同的字段集
- REST API 提供与 MCP `get_note_by_path` 等价的端点

## 改动范围

### 文件

只修改 `src/obsidian2vector/search.py`，不涉及核心库、索引器或 MCP 代码。

### 1. `/search` — 移除 content 字段

**MCP 行为**：`search_obsidian` 只返回 title, path, tags, links, score，不返回正文片段。

**改动**：
- `SearchResult` 模型移除 `content` 字段
- `_search_milvus` 的 `output_fields` 中去掉 `"content"`
- `_search_chroma` 的查询中去掉 `"documents"` include
- `SearchResult` 构造时不再传入 `content`

### 2. `GET /note/{path:path}` — 新增全文获取端点

**MCP 行为**：`get_note_by_path(path)` 读取文件并返回原始内容。

**改动**：
- 新增 `GET /note/{path:path}` 端点
- 路径参数：文件的相对路径（相对于 `config.VAULT_PATH`）
- 文件存在时返回原始文件内容（`text/plain`）
- 文件不存在时返回 404
- 读取失败时返回 500
- 使用 `os.path.normpath` 和 `os.path.commonpath` 防止目录遍历攻击

### 不做的事

- 不改变输出格式（REST 继续保持 JSON，MCP 保持 Markdown）
- 不修改核心库、索引器、MCP 代码
- 不改动现有 `/tags`、`/links`、`/`、`/health` 端点

## 安全考量

`/note/{path}` 端点需要防止路径遍历攻击。实现方式：
- 将用户提供的 path 与 `config.VAULT_PATH` 拼接后，用 `os.path.realpath` 规范化
- 验证结果路径必须以 `config.VAULT_PATH` 为前缀
- 如果不符合则返回 403 Forbidden
