#!/usr/bin/env python3
"""
Obsidian to Milvus MVP - 快速将 Obsidian 笔记导入 Milvus 向量数据库
使用 bge-small-zh-v1.5 模型进行中文嵌入 (快速MVP版本)
"""

import os
import re
import glob
from pathlib import Path
from typing import List, Dict, Any

# 配置文件
VAULT_PATH = os.path.expanduser("~/ai-proj/PaperBell")
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "obsidian_notes"

# 嵌入模型配置 - 使用轻量级模型快速启动
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
EMBEDDING_DIM = 512

print("=" * 60)
print("🚀 Obsidian → Milvus MVP")
print("=" * 60)

# ============================================================
# 1. 加载嵌入模型
# ============================================================
print("\n📦 加载嵌入模型...")
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(EMBEDDING_MODEL)
print(f"   模型: {EMBEDDING_MODEL}")
print(f"   维度: {EMBEDDING_DIM}")

# ============================================================
# 2. 解析 Obsidian Vault
# ============================================================
print(f"\n📂 解析 Obsidian Vault: {VAULT_PATH}")

def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """解析 YAML frontmatter 和正文"""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter_str = parts[1]
            body = parts[2].strip()
        else:
            frontmatter_str = ""
            body = content
    else:
        frontmatter_str = ""
        body = content.strip()

    # 简单解析 frontmatter
    frontmatter = {}
    for line in frontmatter_str.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip().strip('"')

    return frontmatter, body

def clean_markdown(text: str) -> str:
    """清洗 Markdown 语法"""
    # 移除标题
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # 移除加粗斜体
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # 移除代码块
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    # 移除引用
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    # 移除列表
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
    # 移除图片和链接
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[(.+?)\]\(.*?\)', r'\1', text)
    # 移除 HTML
    text = re.sub(r'<[^>]+>', '', text)
    # 移除多余空白
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

def extract_tags_and_links(content: str, frontmatter: Dict) -> tuple[List[str], List[str]]:
    """提取标签和 Wiki 链接"""
    # 从 frontmatter 提取 tags
    tags = []
    if 'tags' in frontmatter:
        tags_str = frontmatter['tags']
        if isinstance(tags_str, str):
            tags = [t.strip() for t in tags_str.split(',')]
        elif isinstance(tags_str, list):
            tags = tags_str

    # 从正文提取 #标签
    tags += re.findall(r'#([^\s#]+)', content)

    # 提取 [[链接]]
    links = re.findall(r'\[\[(.*?)\]\]', content)

    return list(set(tags)), links

# 收集所有笔记
notes = []
md_files = glob.glob(os.path.join(VAULT_PATH, "**/*.md"), recursive=True)

print(f"   找到 {len(md_files)} 个 Markdown 文件")

for md_file in md_files:
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析 frontmatter
        frontmatter, body = parse_frontmatter(content)

        # 清洗 Markdown
        clean_text = clean_markdown(body)

        # 跳过空文档
        if len(clean_text) < 10:
            continue

        # 提取标签和链接
        tags, links = extract_tags_and_links(content, frontmatter)

        # 获取标题
        title = frontmatter.get('title', Path(md_file).stem)
        if not title:
            # 使用文件名作为标题
            title = Path(md_file).stem

        # 相对路径
        rel_path = os.path.relpath(md_file, VAULT_PATH)

        notes.append({
            'id': rel_path,
            'title': title,
            'content': clean_text,
            'tags': tags,
            'links': links,
            'path': rel_path
        })

    except Exception as e:
        print(f"   ⚠️ 跳过 {md_file}: {e}")

print(f"   ✅ 成功解析 {len(notes)} 篇笔记")

# ============================================================
# 3. 生成嵌入向量
# ============================================================
print("\n🔢 生成嵌入向量...")

texts = [n['content'] for n in notes]
embeddings = model.encode(texts, show_progress_bar=True)

print(f"   生成 {len(embeddings)} 个向量, 维度 {embeddings.shape[1]}")

# ============================================================
# 4. 连接 Milvus 并创建 Collection
# ============================================================
print(f"\n🗄️ 连接 Milvus ({MILVUS_HOST}:{MILVUS_PORT})...")

from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

# 连接
connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)

# 检查并删除已存在的 collection
if utility.has_collection(COLLECTION_NAME):
    print(f"   删除旧 collection: {COLLECTION_NAME}")
    utility.drop_collection(COLLECTION_NAME)

# 定义 Schema
fields = [
    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=500, is_primary=True),
    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=2000),
    FieldSchema(name="links", dtype=DataType.VARCHAR, max_length=4000),
    FieldSchema(name="path", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
]

schema = CollectionSchema(fields=fields, description="Obsidian笔记向量库")
collection = Collection(name=COLLECTION_NAME, schema=schema)

# 创建索引
index_params = {
    "metric_type": "L2",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128}
}
collection.create_index(field_name="vector", index_params=index_params)

print(f"   ✅ Collection '{COLLECTION_NAME}' 已创建")

# ============================================================
# 5. 插入数据
# ============================================================
print("\n📥 插入数据到 Milvus...")

# 准备数据
ids = [n['id'] for n in notes]
titles = [n['title'] for n in notes]
contents = [n['content'] for n in notes]
tags_list = [','.join(n['tags']) for n in notes]
links_list = [','.join(n['links']) for n in notes]
paths = [n['path'] for n in notes]
vectors = embeddings.tolist()

# 插入
data = [ids, titles, contents, tags_list, links_list, paths, vectors]
collection.insert(data)

# 加载 Collection
collection.load()

print(f"   ✅ 已索引 {len(notes)} 篇笔记")

# ============================================================
# 6. 测试搜索
# ============================================================
print("\n🔍 测试搜索...")

def search(query: str, top_k: int = 5):
    """搜索笔记"""
    query_embedding = model.encode([query]).tolist()

    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

    results = collection.search(
        data=query_embedding,
        anns_field="vector",
        param=search_params,
        limit=top_k,
        output_fields=["id", "title", "content", "tags", "path"]
    )

    return results[0]

# 测试查询
test_queries = ["论文", "科研", "工具"]
for q in test_queries:
    results = search(q, top_k=3)
    print(f"\n   查询: '{q}'")
    for r in results:
        print(f"   - {r.entity.get('title', 'N/A')} (score: {r.distance:.3f})")

# ============================================================
# 7. 启动 API 服务
# ============================================================
print("\n🌐 启动 FastAPI 服务...")

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Obsidian → Milvus API")

class SearchRequest(BaseModel):
    query: str = ""
    top_k: int = 5
    tags: str = ""
    links: str = ""

class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    tags: str
    links: str
    path: str
    score: float

@app.post("/search", response_model=List[SearchResult])
def search_api(req: SearchRequest):
    """搜索笔记 API - 支持向量搜索 + Tag过滤 + Link过滤"""
    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

    query_to_use = req.query if req.query else "笔记"
    query_embedding = model.encode([query_to_use]).tolist()

    limit = 100 if (req.tags or req.links) else req.top_k

    results = collection.search(
        data=query_embedding,
        anns_field="vector",
        param=search_params,
        limit=limit,
        output_fields=["id", "title", "content", "tags", "links", "path"]
    )

    filtered = []
    for r in results[0]:
        tags = r.entity.get('tags', '') or ''
        links = r.entity.get('links', '') or ''

        if req.tags and req.tags not in tags:
            continue
        if req.links and req.links not in links:
            continue

        filtered.append(r)
        if len(filtered) >= req.top_k:
            break

    return [
        SearchResult(
            id=r.entity.get('id', ''),
            title=r.entity.get('title', ''),
            content=r.entity.get('content', '')[:200] + '...',
            tags=tags,
            links=links,
            path=r.entity.get('path', ''),
            score=r.distance
        )
        for r in filtered
    ]

@app.get("/tags")
def list_tags():
    """获取所有标签"""
    all_tags = set()
    for n in notes:
        for t in n['tags']:
            all_tags.add(t)
    return {"tags": sorted(list(all_tags))}

@app.get("/links")
def list_links():
    """获取所有链接"""
    all_links = set()
    for n in notes:
        for l in n['links']:
            all_links.add(l)
    return {"links": sorted(list(all_links))}

@app.get("/")
def root():
    return {"status": "ok", "notes_indexed": len(notes), "collection": COLLECTION_NAME}

@app.get("/health")
def health():
    return {"status": "healthy", "milvus_connected": True}

print("=" * 60)
print(f"✅ MVP 启动成功!")
print(f"   📊 已索引: {len(notes)} 篇笔记")
print(f"   📁 Collection: {COLLECTION_NAME}")
print(f"   🌐 API: http://localhost:8000")
print(f"   🔍 测试: curl -X POST http://localhost:8000/search -H 'Content-Type: application/json' -d '{{\"query\": \"论文\", \"top_k\": 3}}'")
print("=" * 60)

# 启动服务
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)