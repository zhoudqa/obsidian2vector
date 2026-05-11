# Obsidian2Vector

将 Obsidian 笔记库转换为向量数据库，支持 Milvus/Chroma，并提供 MCP Server 接口。

## 功能特性

- 📄 **Obsidian 解析** - 解析 Vault 中的 Markdown 文件，提取 frontmatter、tags、wiki links
- 🔢 **向量嵌入** - 支持多种嵌入模型 (BGE, Qwen3-Embedding)
- 🗄️ **多数据库支持** - Milvus / Chroma 向量数据库
- 🌐 **REST API** - FastAPI 搜索接口
- 🤖 **MCP Server** - Model Context Protocol 服务器，支持 AI 助手直接调用

## 支持的嵌入模型

| 模型 | 向量维度 | 说明 |
|------|---------|------|
| `BAAI/bge-small-zh-v1.5` | 512 | 默认，轻量快速 |
| `BAAI/bge-base-zh-v1.5` | 768 | 中等精度 |
| `BAAI/bge-large-zh-v1.5` | 1024 | 高精度 |
| `Qwen/Qwen3-Embedding-0.6B` | 1024 | 阿里 Qwen 系列 |
| `Qwen/Qwen3-Embedding-1.8B` | 1024 | 阿里 Qwen 系列 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.py` 或使用环境变量:

```bash
export VAULT_PATH="~/ai-proj/PaperBell"        # Obsidian Vault 路径
export EMBEDDING_MODEL="BAAI/bge-small-zh-v1.5" # 嵌入模型
export DB_TYPE="chroma"                         # 数据库类型: milvus / chroma
```

### 3. 索引笔记

**Milvus 版本:**
```bash
python3 indexer.py
```

**Chroma 版本:**
```bash
python3 indexer_chroma.py
```

### 4. 启动搜索 API

**Milvus:**
```bash
python3 search.py
```

**Chroma:**
```bash
python3 search_chroma.py
```

API 地址: http://localhost:8000

## API 接口

### 搜索笔记

```bash
curl -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "论文", "top_k": 5}'
```

**参数:**
- `query`: 搜索文本
- `top_k`: 返回结果数量
- `tags`: 按标签过滤 (可选)
- `links`: 按 wiki 链接过滤 (可选)

### 获取所有标签

```bash
curl http://localhost:8000/tags
```

### 获取所有链接

```bash
curl http://localhost:8000/links
```

## MCP Server

支持作为 MCP Server 运行，供 Claude Desktop 等 AI 助手直接调用。

### 启动 MCP Server

```bash
python3 mcp_server.py
```

### Claude Desktop 配置

在 `~/.config/Claude/claude_desktop_config.json` 中添加:

```json
{
  "mcpServers": {
    "obsidian-search": {
      "command": "python3",
      "args": ["mcp_server.py"],
      "env": {"PYTHONPATH": "项目路径"}
    }
  }
}
```

### MCP 工具

| 工具 | 功能 |
|------|------|
| `search_obsidian` | 向量搜索，支持 tag/link 过滤 |
| `list_all_tags` | 列出所有标签 |
| `list_all_links` | 列出所有 wiki 链接 |
| `get_note_by_path` | 按路径获取笔记 |

## 项目结构

```
obsidian2milvus-mvp/
├── config.py           # 配置 (模型、数据库)
├── parser.py           # Obsidian 解析器
├── embedder.py         # 嵌入模型加载
├── indexer.py         # Milvus 索引
├── indexer_chroma.py  # Chroma 索引
├── search.py          # Milvus 搜索 API
├── search_chroma.py   # Chroma 搜索 API
├── mcp_server.py      # MCP Server
├── mcp_test.py        # MCP 测试客户端
└── requirements.txt   # 依赖
```

## Docker 部署 (可选)

```yaml
# docker-compose.yml
version: '3'
services:
  milvus:
    image: milvusdb/milvus:v2.4.0
    ports:
      - "19530:19530"
    volumes:
      - milvus_data:/var/lib/milvus
```

## 示例查询

```python
from pymilvus import connections, Collection

connections.connect(host="localhost", port="19530")
collection = Collection("obsidian_notes")
collection.load()

# 搜索
results = collection.search(
    data=[[0.1, 0.2, ...]],  # 查询向量
    anns_field="vector",
    param={"metric_type": "L2", "params": {"nprobe": 10}},
    limit=5,
    output_fields=["title", "content", "tags"]
)
```

## 许可证

MIT