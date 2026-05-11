#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import config
from embedder import Embedder
from parser import parse_vault
import chromadb

mcp = FastMCP("Obsidian Search")

embedder = Embedder()

client = chromadb.PersistentClient(path=config.CHROMA_PATH)
collection = client.get_collection(name=config.CHROMA_COLLECTION)

notes = parse_vault(config.VAULT_PATH)

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

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=limit,
        include=["metadatas", "documents", "distances"]
    )

    if not results or 'metadatas' not in results or not results['metadatas']:
        return "No results found."

    metadatas = results.get('metadatas', [[]])[0]
    documents = results.get('documents', [[]])[0]
    distances = results.get('distances', [[]])[0]

    filtered = []
    for i, meta in enumerate(metadatas):
        t = meta.get('tags', '') or ''
        l = meta.get('links', '') or ''

        if tags and tags not in t:
            continue
        if links and links not in l:
            continue

        filtered.append((meta, documents[i] if i < len(documents) else "", distances[i] if i < len(distances) else 0))
        if len(filtered) >= top_k:
            break

    if not filtered:
        return "No results found matching the criteria."

    lines = [f"# Search Results: '{query}'", ""]
    for meta, doc, dist in filtered:
        lines.append(f"## {meta.get('title', 'Unknown')}")
        lines.append(f"- **Path**: {meta.get('path', '')}")
        lines.append(f"- **Score**: {dist:.3f}")
        if meta.get('tags'):
            lines.append(f"- **Tags**: {meta.get('tags', '')}")
        if meta.get('links'):
            lines.append(f"- **Links**: {meta.get('links', '')}")
        lines.append(f"- **Content**: {doc[:200]}..." if len(doc) > 200 else f"- **Content**: {doc}")
        lines.append("")

    return "\n".join(lines)

@mcp.tool()
def list_all_tags() -> str:
    """List all unique tags from the Obsidian vault.
    
    Returns:
        Formatted list of all tags found in notes
    """
    all_tags = set()
    for n in notes:
        for t in n['tags']:
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
        for l in n['links']:
            if l:
                all_links.add(l)
    
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
        if n['path'] == path:
            lines = [f"# {n['title']}", ""]
            lines.append(f"**Path**: {n['path']}")
            if n['tags']:
                lines.append(f"**Tags**: {', '.join(n['tags'])}")
            if n['links']:
                lines.append(f"**Links**: {', '.join(n['links'])}")
            lines.append("")
            lines.append("## Content")
            lines.append(n['content'])
            return "\n".join(lines)
    
    return f"Note not found: {path}"

@mcp.resource("obsidian://stats")
def get_stats() -> str:
    """Get statistics about the indexed Obsidian vault."""
    return f"""# Obsidian Vault Stats

- **Total Notes**: {len(notes)}
- **Model**: {config.EMBEDDING_MODEL}
- **Vector Dimension**: {config.EMBEDDING_DIM}
- **Database**: Chroma (cosine similarity)
"""

if __name__ == "__main__":
    mcp.run()