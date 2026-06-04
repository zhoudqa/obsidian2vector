# REST API Search 对齐 MCP — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 REST API 搜索接口与 MCP 工具对齐：`/search` 去掉 content 字段，新增 `GET /note/{path}` 端点

**Architecture:** 单文件修改，只涉及 `src/obsidian2vector/search.py`。不修改核心库、索引器或 MCP 代码。

**Tech Stack:** Python, FastAPI, pydantic

---

### Task 1: 更新 `/search` — 移除 content 字段

**Files:**
- Modify: `src/obsidian2vector/search.py`

**改动说明：**
- `SearchResult` pydantic 模型移除 `content: str` 字段
- `_search_milvus`: `output_fields` 中去掉 `"content"`，SearchResult 构造中去掉 `content=` 参数
- `_search_chroma`: `include` 中去掉 `"documents"`，SearchResult 构造中去掉 `content=` 参数

- [ ] **Step 1: 修改 SearchResult 模型**

移除 `content` 字段：

```python
class SearchResult(BaseModel):
    id: str
    title: str
    tags: str
    links: str
    path: str
    score: float
```

- [ ] **Step 2: 修改 `_search_milvus`**

在 `output_fields` 中将 `"content"` 去掉：

```python
# 修改前
output_fields=["id", "title", "content", "tags", "links", "path"]

# 修改后
output_fields=["id", "title", "tags", "links", "path"]
```

同时将 return 中的 `SearchResult` 去掉 `content=` 参数。

- [ ] **Step 3: 修改 `_search_chroma`**

在 `collection.query` 的 `include` 中去掉 `"documents"`：

```python
# 修改前
include=["metadatas", "documents", "distances"]

# 修改后
include=["metadatas", "distances"]
```

同时在 `_search_chroma` 的 return 语句中去掉 `content=` 参数。

- [ ] **Step 4: 清理不再使用的变量**

在 `_search_chroma` 的 filtered 构建中去掉 `documents` 相关的变量：

```python
# 修改前
filtered.append((meta, documents[i] if i < len(documents) else "", distances[i] if i < len(distances) else 0))

# 修改后
filtered.append((meta, distances[i] if i < len(distances) else 0))
```

以及对应的 return 语句中解包去掉 `doc`。

- [ ] **Step 5: 验证修改**

```bash
python -c "
from obsidian2vector.search import SearchResult
# 验证 content 字段已不存在
r = SearchResult(id='1', title='t', tags='', links='', path='p', score=0.5)
print(r.model_dump_json())
# 应该输出类似: {\"id\":\"1\",\"title\":\"t\",\"tags\":\"\",\"links\":\"\",\"path\":\"p\",\"score\":0.5}
"
```

### Task 2: 新增 `GET /note/{path:path}` 端点

**Files:**
- Modify: `src/obsidian2vector/search.py`

**说明：** 对标 MCP 的 `get_note_by_path` 工具，按文件路径读取笔记全文。

- [ ] **Step 1: 添加路径导入**

在 `search.py` 顶部已有的 `from typing import List` 旁或附近，确保已引入 `os`（检查是否已有，没有则添加）。已有导入 `from fastapi import FastAPI`，需改为 `from fastapi import FastAPI, HTTPException`。

- [ ] **Step 2: 添加 `get_note` 端点**

在 `list_links` 和 `root` 之间（或文件末尾），添加新端点：

```python
@app.get("/note/{path:path}")
def get_note(path: str):
    """Get a specific note by its file path.

    Args:
        path: Relative path to the note file (e.g., 'Persons/Scholars/example.md')

    Returns:
        Raw file content as text/plain
    """
    # Security: prevent path traversal
    vault_path = os.path.normpath(config.VAULT_PATH)
    requested_path = os.path.normpath(os.path.join(vault_path, path))
    requested_path = os.path.realpath(requested_path)

    if not requested_path.startswith(vault_path):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.isfile(requested_path):
        raise HTTPException(status_code=404, detail=f"Note not found: {path}")

    try:
        with open(requested_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to read note: {e}")

    return content
```

- [ ] **Step 3: 验证端点存在**

```bash
python -c "
from obsidian2vector.search import app
# 列出所有路由
for route in app.routes:
    print(route.path, route.methods)
"
```

预期输出中应包含 `/note/{path:path}` 和 `GET` 方法。

- [ ] **Step 4: 提交**

```bash
git add docs/superpowers/specs/2026-06-04-rest-search-align-mcp-design.md docs/superpowers/plans/2026-06-04-rest-search-align-mcp.md src/obsidian2vector/search.py
git commit -m "feat: align REST search API with MCP — remove content from /search, add GET /note/{path}"
```
