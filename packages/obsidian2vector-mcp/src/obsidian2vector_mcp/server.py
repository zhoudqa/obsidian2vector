#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
from obsidian2vector import config
from obsidian2vector.embedder import Embedder
from obsidian2vector.parser import parse_vault

mcp = FastMCP("Obsidian Search")

embedder = Embedder()

if config.DB_TYPE == "milvus":
    from pymilvus import connections, Collection
    connections.connect(host=config.MILVUS_HOST, port=config.MILVUS_PORT)
    collection = Collection(config.MILVUS_COLLECTION)
    collection.load()
else:
    import chromadb
    client = chromadb.PersistentClient(path=config.CHROMA_PATH)
    collection = client.get_collection(name=config.CHROMA_COLLECTION)

notes = parse_vault(config.VAULT_PATH)


def _search_milvus(query_embedding, limit, tags, links, top_k):
    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
    results = collection.search(
        data=query_embedding,
        anns_field="vector",
        param=search_params,
        limit=limit,
        output_fields=["id", "title", "content", "tags", "links", "path"],
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
                "content": r.entity.get("content", ""),
                "score": r.distance,
            }
        )
        if len(filtered) >= top_k:
            break
    return filtered


def _search_chroma(query_embedding, limit, tags, links, top_k):
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=limit,
        include=["metadatas", "documents", "distances"],
    )

    if not results or "metadatas" not in results or not results["metadatas"]:
        return []

    metadatas = results.get("metadatas", [[]])[0]
    documents = results.get("documents", [[]])[0]
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
                "content": documents[i] if i < len(documents) else "",
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
        doc = r["content"]
        lines.append(
            f"- **Content**: {doc[:200]}..." if len(doc) > 200 else f"- **Content**: {doc}"
        )
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
        Formatted search results with title, content snippet, tags, links, and score
    """
    query_to_use = query if query else "笔记"
    query_embedding = embedder.encode([query_to_use]).tolist()

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
    all_tags = set()
    for n in notes:
        for t in n["tags"]:
            if t:
                all_tags.add(t)

    if not all_tags:
        return "No tags found."

    return "## All Tags\n\n" + "\n".join(f"- {tag}" for tag in sorted(all_tags))


@mcp.tool()
def list_all_links() -> str:
    """List all unique wiki links from the Obsidian vault.

    Returns:
        Formatted list of all wiki links found in notes
    """
    all_links = set()
    for n in notes:
        for link in n["links"]:
            if link:
                all_links.add(link)

    if not all_links:
        return "No links found."

    return "## All Links\n\n" + "\n".join(f"- {link}" for link in sorted(all_links))


@mcp.tool()
def get_note_by_path(path: str) -> str:
    """Get a specific note by its file path.

    Args:
        path: Relative path to the note file (e.g., 'Persons/Scholars/宋爽.md')

    Returns:
        Full note content with metadata
    """
    for n in notes:
        if n["path"] == path:
            lines = [f"# {n['title']}", ""]
            lines.append(f"**Path**: {n['path']}")
            if n["tags"]:
                lines.append(f"**Tags**: {', '.join(n['tags'])}")
            if n["links"]:
                lines.append(f"**Links**: {', '.join(n['links'])}")
            lines.append("")
            lines.append("## Content")
            lines.append(n["content"])
            return "\n".join(lines)

    return f"Note not found: {path}"


@mcp.resource("obsidian://stats")
def get_stats() -> str:
    """Get statistics about the indexed Obsidian vault."""
    db_name = "Milvus (L2)" if config.DB_TYPE == "milvus" else "Chroma (cosine similarity)"
    return f"""# Obsidian Vault Stats

- **Total Notes**: {len(notes)}
- **Model**: {config.EMBEDDING_MODEL}
- **Vector Dimension**: {config.EMBEDDING_DIM}
- **Database**: {db_name}
"""


def main():
    mcp.run()


if __name__ == "__main__":
    main()
