#!/usr/bin/env python3
import os
import threading

from mcp.server.fastmcp import FastMCP
from obsidian2vector import config

mcp = FastMCP("Obsidian Search")

_state = {
    "embedder": None,
    "collection": None,
    "ready": False,
    "error": None,
}
_ready_event = threading.Event()


def _load_resources():
    try:
        from obsidian2vector.embedder import Embedder

        _state["embedder"] = Embedder()

        if config.DB_TYPE == "milvus":
            from pymilvus import connections, Collection
            connections.connect(host=config.MILVUS_HOST, port=config.MILVUS_PORT)
            _state["collection"] = Collection(config.MILVUS_COLLECTION)
            _state["collection"].load()
        elif config.DB_TYPE == "chroma":
            import chromadb
            client = chromadb.PersistentClient(path=config.CHROMA_PATH)
            _state["collection"] = client.get_collection(name=config.CHROMA_COLLECTION)
        else:
            raise ValueError(f"Unsupported db_type: {config.DB_TYPE}")

        _state["ready"] = True
    except Exception as e:
        _state["error"] = e
    finally:
        _ready_event.set()


def _ensure_ready():
    if _state["ready"]:
        return
    _ready_event.wait()
    if _state["error"]:
        raise _state["error"]


def _fetch_tags_from_milvus() -> set[str]:
    collection = _state["collection"]
    results = collection.query(
        expr="",
        output_fields=["tags"],
        limit=16384,
    )
    all_tags: set[str] = set()
    for row in results:
        raw = row.get("tags", "") or ""
        for t in raw.split(","):
            t = t.strip()
            if t:
                all_tags.add(t)
    return all_tags


def _fetch_links_from_milvus() -> set[str]:
    collection = _state["collection"]
    results = collection.query(
        expr="",
        output_fields=["links"],
        limit=16384,
    )
    all_links: set[str] = set()
    for row in results:
        raw = row.get("links", "") or ""
        for l in raw.split(","):
            l = l.strip()
            if l:
                all_links.add(l)
    return all_links


def _fetch_tags_from_chroma() -> set[str]:
    results = _state["collection"].get(include=["metadatas"])
    all_tags: set[str] = set()
    for meta in results.get("metadatas", []):
        raw = meta.get("tags", "") or ""
        for t in raw.split(","):
            t = t.strip()
            if t:
                all_tags.add(t)
    return all_tags


def _fetch_links_from_chroma() -> set[str]:
    results = _state["collection"].get(include=["metadatas"])
    all_links: set[str] = set()
    for meta in results.get("metadatas", []):
        raw = meta.get("links", "") or ""
        for l in raw.split(","):
            l = l.strip()
            if l:
                all_links.add(l)
    return all_links


def _search_milvus(query_embedding, limit, tags, links, top_k):
    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
    results = _state["collection"].search(
        data=query_embedding,
        anns_field="vector",
        param=search_params,
        limit=limit,
        output_fields=["id", "title", "tags", "links", "path"],
    )

    filtered = []
    for r in results[0]:
        r_tags = r.entity.get("tags", "") or ""
        r_links = r.entity.get("links", "") or ""
        if tags and tags not in r_tags:
            continue
        if links and links not in r_links:
            continue
        filtered.append(
            {
                "title": r.entity.get("title", ""),
                "path": r.entity.get("path", ""),
                "tags": r_tags,
                "links": r_links,
                "score": r.distance,
            }
        )
        if len(filtered) >= top_k:
            break
    return filtered


def _search_chroma(query_embedding, limit, tags, links, top_k):
    results = _state["collection"].query(
        query_embeddings=query_embedding,
        n_results=limit,
        include=["metadatas", "distances"],
    )

    if not results or "metadatas" not in results or not results["metadatas"]:
        return []

    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    filtered = []
    for i, meta in enumerate(metadatas):
        r_tags = meta.get("tags", "") or ""
        r_links = meta.get("links", "") or ""
        if tags and tags not in r_tags:
            continue
        if links and links not in r_links:
            continue
        filtered.append(
            {
                "title": meta.get("title", ""),
                "path": meta.get("path", ""),
                "tags": r_tags,
                "links": r_links,
                "score": distances[i] if i < len(distances) else 0,
            }
        )
        if len(filtered) >= top_k:
            break
    return filtered


def _format_results(results, query, has_filters):
    if not results:
        if has_filters:
            return "No results found matching the criteria."
        return "No results found."

    lines = [f"# Search Results: '{query}'", ""]
    for r in results:
        lines.append(f"## {r['title']}")
        lines.append(f"- **Path**: {r['path']}")
        lines.append(f"- **Score**: {r['score']:.3f}")
        if r["tags"]:
            lines.append(f"- **Tags**: {r['tags']}")
        if r["links"]:
            lines.append(f"- **Links**: {r['links']}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def search_obsidian(query: str = "", top_k: int = 5, tags: str = "", links: str = "") -> str:
    """Search Obsidian notes using vector similarity with optional tag/link filtering.

    Args:
        query: Search text for semantic similarity search
        top_k: Number of results to return (default 5)
        tags: Filter by tag (substring match)
        links: Filter by wiki link (substring match)

    Returns:
        Formatted search results with title, path, tags, links, and score.
        Use get_note_by_path to read the full content of any result.
    """
    _ensure_ready()
    query_to_use = query if query else "notes"
    query_embedding = _state["embedder"].encode([query_to_use]).tolist()

    limit = 100 if (tags or links) else top_k

    if config.DB_TYPE == "milvus":
        results = _search_milvus(query_embedding, limit, tags, links, top_k)
    else:
        results = _search_chroma(query_embedding, limit, tags, links, top_k)

    if not results:
        if tags or links:
            return "No results found matching the criteria."
        return "No results found."

    return _format_results(results, query, bool(tags or links))


@mcp.tool()
def list_all_tags() -> str:
    """List all unique tags from the Obsidian vault.

    Returns:
        Formatted list of all tags found in notes
    """
    _ensure_ready()
    if config.DB_TYPE == "milvus":
        all_tags = _fetch_tags_from_milvus()
    else:
        all_tags = _fetch_tags_from_chroma()

    if not all_tags:
        return "No tags found."

    return "## All Tags\n\n" + "\n".join(f"- {tag}" for tag in sorted(all_tags))


@mcp.tool()
def list_all_links() -> str:
    """List all unique wiki links from the Obsidian vault.

    Returns:
        Formatted list of all wiki links found in notes
    """
    _ensure_ready()
    if config.DB_TYPE == "milvus":
        all_links = _fetch_links_from_milvus()
    else:
        all_links = _fetch_links_from_chroma()

    if not all_links:
        return "No links found."

    return "## All Links\n\n" + "\n".join(f"- {link}" for link in sorted(all_links))


@mcp.tool()
def get_note_by_path(path: str) -> str:
    """Get a specific note by its file path.

    Args:
        path: Relative path to the note file (e.g., 'Persons/Scholars/example.md')

    Returns:
        Full note content with metadata
    """
    _ensure_ready()
    full_path = os.path.join(config.VAULT_PATH, path)

    if not os.path.isfile(full_path):
        return f"Note not found: {path}"

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        return f"Failed to read note: {e}"

    return content


@mcp.resource("obsidian://stats")
def get_stats() -> str:
    """Get statistics about the indexed Obsidian vault."""
    _ensure_ready()
    db_name = "Milvus (L2)" if config.DB_TYPE == "milvus" else "Chroma (cosine similarity)"

    if config.DB_TYPE == "milvus":
        collection = _state["collection"]
        count = collection.num_entities
    else:
        count = _state["collection"].count()

    return f"""# Obsidian Vault Stats

- **Total Notes**: {count}
- **Model**: {config.EMBEDDING_MODEL}
- **Vector Dimension**: {config.EMBEDDING_DIM}
- **Database**: {db_name}
"""


def main():
    t = threading.Thread(target=_load_resources, daemon=True)
    t.start()
    mcp.run()


if __name__ == "__main__":
    main()
