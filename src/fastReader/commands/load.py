import os
from typing import Dict, Any, List
from src.fastReader.models import Document, Manifest
from src.fastReader.scanner import scan_document
from src.fastReader.cache import generate_hash, save_text_to_cache, save_manifest
from src.fastReader.toc import build_toc

def run_load(file_path: str, cache_dir: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the load command logic.

    1. Read file from file_path
    2. Save content to cache as <hash>.txt
    3. Scan document to create Manifest
    4. Save Manifest to cache as <hash>.json
    5. Return manifest_id and count summary
    """
    # 1. Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()

    # 2. Save content to cache
    content_hash = generate_hash(file_content)
    cache_path = save_text_to_cache(file_content, cache_dir)

    # 2. Scan document
    document = Document.from_file(cache_path)
    manifest = scan_document(document, config)

    # 3. Save manifest
    save_manifest(manifest, cache_dir, content_hash)

    # 4. Build summary with marker counts
    summary = {
        "chapters": len(manifest.markers.get("chapter", [])),
        "sections": len(manifest.markers.get("section", [])),
        "subsections": len(manifest.markers.get("subsection", [])),
        "page_breaks": len(manifest.markers.get("page_break", [])),
        "pages": len(manifest.markers.get("page", [])),
        "double_line_breaks": len(manifest.markers.get("double_line_break", [])),
        "blocks": len(manifest.markers.get("block", []))
    }

    return {
        "manifest_id": content_hash,
        "summary": summary
    }
