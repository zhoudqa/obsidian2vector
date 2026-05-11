import os
import re
import glob
from pathlib import Path
from typing import List, Dict, Any

def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
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

    frontmatter = {}
    for line in frontmatter_str.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip().strip('"')

    return frontmatter, body

def clean_markdown(text: str) -> str:
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[(.+?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

def extract_tags_and_links(content: str, frontmatter: Dict) -> tuple[List[str], List[str]]:
    tags = []
    if 'tags' in frontmatter:
        tags_str = frontmatter['tags']
        if isinstance(tags_str, str):
            tags = [t.strip() for t in tags_str.split(',')]
        elif isinstance(tags_str, list):
            tags = tags_str

    tags += re.findall(r'#([^\s#]+)', content)
    links = re.findall(r'\[\[(.*?)\]\]', content)

    return list(set(tags)), links

def parse_vault(vault_path: str) -> List[Dict[str, Any]]:
    notes = []
    md_files = glob.glob(os.path.join(vault_path, "**/*.md"), recursive=True)

    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            frontmatter, body = parse_frontmatter(content)
            clean_text = clean_markdown(body)

            if len(clean_text) < 10:
                continue

            tags, links = extract_tags_and_links(content, frontmatter)

            title = frontmatter.get('title', Path(md_file).stem)
            if not title:
                title = Path(md_file).stem

            rel_path = os.path.relpath(md_file, vault_path)

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

    return notes