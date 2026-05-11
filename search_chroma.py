from typing import List
import config
from embedder import Embedder
from parser import parse_vault
import chromadb

embedder = Embedder()

print(f"\n🗄️ 连接 Chroma: {config.CHROMA_PATH}")
client = chromadb.PersistentClient(path=config.CHROMA_PATH)
collection = client.get_collection(name=config.CHROMA_COLLECTION)

notes = parse_vault(config.VAULT_PATH)

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Obsidian Vector Search API (Chroma)")

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

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=limit,
        include=["metadatas", "documents", "distances"]
    )

    if not results or 'metadatas' not in results or not results['metadatas']:
        return []

    metadatas = results.get('metadatas', [[]])[0]
    documents = results.get('documents', [[]])[0]
    distances = results.get('distances', [[]])[0]

    filtered = []
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
        "db": "chroma",
        "model": config.EMBEDDING_MODEL,
        "notes_indexed": len(notes)
    }

@app.get("/health")
def health():
    return {"status": "healthy", "db": "chroma"}

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print(f"🚀 Search API (Chroma) 启动")
    print(f"   模型: {config.EMBEDDING_MODEL}")
    print(f"   API: http://{config.API_HOST}:{config.API_PORT}")
    print("=" * 60)
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)