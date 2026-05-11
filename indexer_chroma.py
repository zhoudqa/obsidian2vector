import os
import config
from parser import parse_vault
from embedder import Embedder
import chromadb

def index_to_chroma(notes, embedder):
    print(f"\n🗄️ 连接 Chroma: {config.CHROMA_PATH}")
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
    print("🚀 Obsidian → Chroma Indexer")
    print("=" * 60)
    print(f"\n📋 配置:")
    print(f"   模型: {config.EMBEDDING_MODEL}")
    print(f"   向量维度: {config.EMBEDDING_DIM}")
    print(f"   Chroma: {config.CHROMA_PATH}")
    print(f"   Vault: {config.VAULT_PATH}")

    embedder = Embedder()
    notes = parse_vault(config.VAULT_PATH)
    print(f"   ✅ 成功解析 {len(notes)} 篇笔记")

    collection = index_to_chroma(notes, embedder)

    print("\n" + "=" * 60)
    print(f"✅ 索引完成!")
    print(f"   数据库: chroma")
    print(f"   笔记数: {len(notes)}")
    print("=" * 60)

if __name__ == "__main__":
    main()