# Obsidian2Vector

将 Obsidian 笔记库转换为向量数据库，支持 Milvus/Chroma，并提供 MCP Server 接口。

## 功能特性

- 📄 **Obsidian 解析** - 解析 Vault 中的 Markdown 文件，提取 frontmatter、tags、wiki links
- 🔢 **向量嵌入** - 支持多种嵌入模型 (BGE, Qwen3-Embedding)
- 🗄️ **多数据库支持** - Milvus / Chroma 向量数据库
- 🌐 **REST API** - FastAPI 搜索接口
- 🤖 **MCP Server** - Model Context Protocol 服务器，支持 AI 助手直接调用
- 🇨🇳 **中文优化** - 完美支持中文笔记语义搜索、标签过滤、Wiki链接检索

## 支持的嵌入模型

所有模型均针对中文语义理解优化:

| 模型 | 向量维度 | 说明 |
|------|---------|------|
| `BAAI/bge-small-zh-v1.5` | 512 | ⭐ 默认，轻量快速 |
| `BAAI/bge-base-zh-v1.5` | 768 | 中等精度 |
| `BAAI/bge-large-zh-v1.5` | 1024 | 高精度 |
| `Qwen/Qwen3-Embedding-0.6B` | 1024 | 阿里 Qwen 系列 |
| `Qwen/Qwen3-Embedding-1.8B` | 1024 | 阿里 Qwen 系列 |

## 快速开始

### 1. 安装

```bash
# 核心包（索引 + 搜索 API）
pip install obsidian2vector

# MCP Server（可选，依赖核心包自动安装）
pip install obsidian2vector-mcp
```

### 2. 配置

首次运行时自动在用户目录下生成配置文件：

| 平台 | 路径 |
|------|------|
| macOS / Linux | `~/.obsidian2vector/settings.json` |
| Windows | `C:\Users\<用户名>\.obsidian2vector\settings.json` |

编辑该文件：

```json
{
  "vault_path": "/path/to/your/obsidian/vault",
  "embedding_model": "BAAI/bge-small-zh-v1.5",
  "db_type": "chroma",
  "chroma_path": "~/.obsidian2vector/chroma_db",
  "chroma_collection": "obsidian_notes"
}
```

<details>
<summary>完整配置项</summary>

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `vault_path` | `""` | Obsidian Vault 路径（必填） |
| `embedding_model` | `BAAI/bge-small-zh-v1.5` | 嵌入模型名称 |
| `db_type` | `milvus` | 数据库类型：`milvus` 或 `chroma` |
| `milvus_host` | `localhost` | Milvus 地址 |
| `milvus_port` | `19530` | Milvus 端口 |
| `milvus_collection` | `obsidian_notes` | Milvus Collection 名称 |
| `chroma_path` | `""` | Chroma 本地存储路径（默认 `~/.chroma`） |
| `chroma_collection` | `obsidian_notes` | Chroma Collection 名称 |
| `model_load_mode` | `online` | 模型加载：`online` 或 `offline` |
| `model_local_path` | `""` | 离线模式本地模型路径 |
| `hf_endpoint` | `""` | HuggingFace 镜像地址 |
| `api_host` | `0.0.0.0` | REST API 监听地址 |
| `api_port` | `8000` | REST API 端口 |

</details>

> 环境变量仍可使用，优先级高于 settings.json：`VAULT_PATH`、`DB_TYPE`、`MILVUS_HOST` 等。

### 3. 索引笔记

```bash
obsidian2vector-index
```

根据 `db_type` 配置自动选择 Milvus 或 Chroma。

### 4. 搜索

**REST API：**

```bash
# Milvus
obsidian2vector-search

# Chroma
obsidian2vector-search-chroma
```

API 地址: http://localhost:8000

```bash
curl -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "论文", "top_k": 5}'
```

**参数:** `query`（搜索文本）、`top_k`（结果数）、`tags`（标签过滤，可选）、`links`（链接过滤，可选）

### 获取所有标签 / 链接

```bash
curl http://localhost:8000/tags
curl http://localhost:8000/links
```

## MCP Server

供 Claude Desktop 等 AI 助手直接调用。

### 启动

```bash
obsidian2vector-mcp
```

### Claude Desktop 配置

在 `~/.config/Claude/claude_desktop_config.json` 中添加:

```json
{
  "mcpServers": {
    "obsidian-search": {
      "command": "obsidian2vector-mcp"
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

## Milvus 环境配置

### 1. 安装 Docker Desktop

**macOS (使用 Homebrew):**
```bash
brew install --cask docker
```

启动 Docker Desktop 并确保其运行正常。

### 2. 使用 Docker Compose 启动 Milvus

创建 `docker-compose.yml`:

```yaml
version: '3'
services:
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - ./etcd:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - ./minio:/minio_data
    command: minio server /minio_data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/liveness"]
      interval: 30s
      timeout: 20s
      retries: 3

  milvus:
    image: milvusdb/milvus:v2.4.0
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ./milvus:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - etcd
      - minio
```

启动服务:
```bash
docker compose up -d
```

### 3. 配置

编辑 `~/.obsidian2vector/settings.json`，设置 `db_type` 为 `milvus` 并填写连接信息。

### 4. 常用 Docker 命令

```bash
docker compose logs -f milvus    # 查看日志
docker compose down               # 停止服务
docker compose down -v            # 删除数据(重置)
```

## Chroma 快速开始

Chroma 无需额外服务。在 `settings.json` 中设置 `db_type` 为 `chroma`，然后直接索引即可：

```bash
obsidian2vector-index
```

## 许可证

MIT
