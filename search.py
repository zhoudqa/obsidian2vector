from typing import List
import config
from embedder import Embedder
from parser import parse_vault

embedder = Embedder()

if config.DB_TYPE == "milvus":
    from pymilvus import connections, Collection
    connections.connect(host=config.MILVUS_HOST, port=config.MILVUS_PORT)
    collection = Collection(config.MILVUS_COLLECTION)
    collection.load()
else:
    print("Chroma not yet supported, using Milvus")
    from pymilvus import connections, Collection
    connections.connect(host=config.MILVUS_HOST, port=config.MILVUS_PORT)
    collection = Collection(config.MILVUS_COLLECTION)
    collection.load()

notes = parse_vault(config.VAULT_PATH)

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Obsidian Vector Search API")

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
    query_to_use = req.query if req.query else "笔记"
    query_embedding = embedder.encode([query_to_use]).tolist()

    limit = 100 if (req.tags or req.links) else req.top_k

    if config.DB_TYPE == "milvus":
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
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

            filtered.append((r, tags, links))
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
            for r, tags, links in filtered
        ]
    else:
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=limit,
            include=["metadatas", "documents", "distances"]
        )

        filtered = []
        if not results:
            return []

        r = results[0]
        metadatas = r.get('metadatas', [])
        documents = r.get('documents', [])
        distances = r.get('distances', [])

        if not metadatas:
            return []

        for i, meta in enumerate(metadatas):
            tags = meta.get('tags', '') or ''
            links = meta.get('links', '') or ''

            if req.tags and req.tags not in tags:
                continue
            if req.links and req.links not in links:
                continue

            filtered.append((meta, documents[i] if i < len(documents) else "", distances[i] if i < len(distances) else 0))
            if len(filtered) >= req.top_k:
                break

        return [
            SearchResult(
                id=meta.get('path', ''),
                title=meta.get('title', ''),
                content=doc[:200] + '...',
                tags=meta.get('tags', ''),
                links=meta.get('links', ''),
                path=meta.get('path', ''),
                score=dist
            )
            for meta, doc, dist in filtered
        ]

@app.get("/tags")
def list_tags():
    all_tags = set()
    for n in notes:
        for t in n['tags']:
            all_tags.add(t)
    return {"tags": sorted([t for t in all_tags if t])[:50]}

@app.get("/links")
def list_links():
    all_links = set()
    for n in notes:
        for l in n['links']:
            all_links.add(l)
    return {"links": sorted(list(all_links))[:50]}

@app.get("/")
def root():
    return {
        "status": "ok",
        "db": config.DB_TYPE,
        "model": config.EMBEDDING_MODEL,
        "notes_indexed": len(notes)
    }

@app.get("/health")
def health():
    return {"status": "healthy", "db": config.DB_TYPE}

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print(f"🚀 Search API 启动")
    print(f"   数据库: {config.DB_TYPE}")
    print(f"   模型: {config.EMBEDDING_MODEL}")
    print(f"   API: http://{config.API_HOST}:{config.API_PORT}")
    print("=" * 60)
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)