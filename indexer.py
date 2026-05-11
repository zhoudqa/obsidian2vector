import os
import sys
import json
from pathlib import Path

import config
from parser import parse_vault
from embedder import Embedder

def get_milvus_client():
    from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
    connections.connect(host=config.MILVUS_HOST, port=config.MILVUS_PORT)
    return "milvus"

def get_chroma_client():
    import chromadb
    from chromadb.config import Settings
    os.makedirs(config.CHROMA_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=config.CHROMA_PATH)
    return "chroma", client

def index_to_milvus(notes, embedder):
    from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

    print(f"\n🗄️ 连接 Milvus ({config.MILVUS_HOST}:{config.MILVUS_PORT})...")
    connections.connect(host=config.MILVUS_HOST, port=config.MILVUS_PORT)

    col_name = config.MILVUS_COLLECTION
    if utility.has_collection(col_name):
        print(f"   删除旧 collection: {col_name}")
        utility.drop_collection(col_name)

    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=500, is_primary=True),
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=2000),
        FieldSchema(name="links", dtype=DataType.VARCHAR, max_length=4000),
        FieldSchema(name="path", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=embedder.dim)
    ]

    schema = CollectionSchema(fields=fields, description="Obsidian笔记向量库")
    collection = Collection(name=col_name, schema=schema)

    index_params = {"metric_type": "L2", "index_type": "IVF_FLAT", "params": {"nlist": 128}}
    collection.create_index(field_name="vector", index_params=index_params)

    print(f"\n🔢 生成嵌入向量...")
    texts = [n['content'] for n in notes]
    embeddings = embedder.encode(texts)

    print(f"\n📥 插入数据到 Milvus...")
    ids = [n['id'] for n in notes]
    titles = [n['title'] for n in notes]
    contents = [n['content'] for n in notes]
    tags_list = [','.join(n['tags']) for n in notes]
    links_list = [','.join(n['links']) for n in notes]
    paths = [n['path'] for n in notes]
    vectors = embeddings.tolist()

    data = [ids, titles, contents, tags_list, links_list, paths, vectors]
    collection.insert(data)
    collection.load()

    print(f"   ✅ 已索引 {len(notes)} 篇笔记到 Milvus")
    return collection

def index_to_chroma(notes, embedder):
    print(f"\n🗄️ 连接 Chroma: {config.CHROMA_PATH}")
    import chromadb

    os.makedirs(config.CHROMA_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=config.CHROMA_PATH)

    col_name = config.CHROMA_COLLECTION
    try:
        client.delete_collection(col_name)
        print(f"   删除旧 collection: {col_name}")
    except:
        pass

    collection = client.create_collection(name=col_name, metadata={"hnsw:space": "cosine"})

    print(f"\n🔢 生成嵌入向量...")
    texts = [n['content'] for n in notes]
    embeddings = embedder.encode(texts)

    print(f"\n📥 插入数据到 Chroma...")
    ids = [n['id'] for n in notes]
    documents = [n['content'] for n in notes]
    metadatas = [
        {
            "title": n['title'],
            "tags": ','.join(n['tags']),
            "links": ','.join(n['links']),
            "path": n['path']
        }
        for n in notes
    ]

    collection.add(ids=ids, embeddings=embeddings.tolist(), documents=documents, metadatas=metadatas)

    print(f"   ✅ 已索引 {len(notes)} 篇笔记到 Chroma")
    return collection

def main():
    print("=" * 60)
    print("🚀 Obsidian → Vector DB Indexer")
    print("=" * 60)
    print(f"\n📋 配置:")
    print(f"   模型: {config.EMBEDDING_MODEL}")
    print(f"   向量维度: {config.EMBEDDING_DIM}")
    print(f"   数据库: {config.DB_TYPE}")
    print(f"   Vault: {config.VAULT_PATH}")

    embedder = Embedder()

    print(f"\n📂 解析 Obsidian Vault: {config.VAULT_PATH}")
    notes = parse_vault(config.VAULT_PATH)
    print(f"   ✅ 成功解析 {len(notes)} 篇笔记")

    if config.DB_TYPE == "milvus":
        collection = index_to_milvus(notes, embedder)
    elif config.DB_TYPE == "chroma":
        collection = index_to_chroma(notes, embedder)
    else:
        print(f"❌ 不支持的数据库类型: {config.DB_TYPE}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"✅ 索引完成!")
    print(f"   数据库: {config.DB_TYPE}")
    print(f"   笔记数: {len(notes)}")
    print("=" * 60)

if __name__ == "__main__":
    main()