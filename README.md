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
# 基础配置
export VAULT_PATH="~/ai-proj/PaperBell"        # Obsidian Vault 路径
export EMBEDDING_MODEL="BAAI/bge-small-zh-v1.5" # 嵌入模型

# 数据库选择
export DB_TYPE="milvus"  # 或 "chroma"

# Milvus 配置 (DB_TYPE=milvus 时需要)
export MILVUS_HOST="localhost"
export MILVUS_PORT="19530"
export MILVUS_COLLECTION="obsidian_notes"

# Chroma 配置 (DB_TYPE=chroma 时可选)
export CHROMA_PATH="./chroma_db"
export CHROMA_COLLECTION="obsidian_notes"
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

验证服务状态:
```bash
docker compose ps
```

### 3. Milvus 配置参数

编辑 `config.py` 或使用环境变量:

```bash
export DB_TYPE="milvus"
export MILVUS_HOST="localhost"      # Milvus 服务器地址
export MILVUS_PORT="19530"          # Milvus 端口
export MILVUS_COLLECTION="obsidian_notes"  # Collection 名称
```

### 4. 验证 Milvus 连接

```bash
# 检查 Milvus 端口
curl http://localhost:19530/health

# 或通过 Python 测试
python3 -c "
from pymilvus import connections
connections.connect(host='localhost', port='19530')
print('Milvus 连接成功!')
"
```

### 6. 常用 Docker 命令

```bash
# 查看日志
docker compose logs -f milvus

# 停止服务
docker compose down

# 删除数据(重置)
docker compose down -v
```

## Chroma 快速开始

Chroma 无需额外服务，直接使用:

```bash
export DB_TYPE="chroma"
export CHROMA_PATH="./chroma_db"  # 本地存储路径
export CHROMA_COLLECTION="obsidian_notes"

python3 indexer_chroma.py  # 索引
python3 search_chroma.py   # 搜索
```


## 许可证

MIT