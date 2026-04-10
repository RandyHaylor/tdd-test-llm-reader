from typing import Dict, Any, List
from src.fastReader.models import Document, Manifest
from src.fastReader.scanner import scan_document
from src.fastReader.cache import generate_hash, save_text_to_cache, save_manifest
from src.fastReader.toc import build_toc

def run_load(stdin_text: str, cache_dir: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the load command logic.
    
    1. Save content to cache as <hash>.txt
    2. Scan document to create Manifest
    3. Save Manifest to cache as <hash>.json
    4. Return manifest_id and a self-documenting 'fast_reader' guide
    """
    # 1. Save content to cache
    content_hash = generate_hash(stdin_text)
    cache_path = save_text_to_cache(stdin_text, cache_dir)
    
    # 2. Scan document
    document = Document.from_file(cache_path)
    manifest = scan_document(document, config)
    
    # 3. Save manifest
    save_manifest(manifest, cache_dir, content_hash)
    
    # 4. Prepare self-documenting Table of Contents
    marker_types = ['chapter', 'section', 'subsection', 'page_break', 'page']
    toc_entries = build_toc(manifest, document.lines, marker_types=marker_types, limit=None)
    
    # Fallback to blocks if no structural markers found
    if not toc_entries:
        toc_entries = build_toc(manifest, document.lines, marker_types=['block'], limit=None)
        
    # Bake instructions into each line
    guide_lines = []
    for m in toc_entries:
        cmd = f"python3 -m src.fastReader.cli get --{m['type'].replace('_break', '')} {m['index']} --manifest {content_hash}"
        guide_lines.append(f"{m['type']} {m['index']}: {m['preview']} -> {cmd}")
    
    fast_reader_guide = "FastReader loaded. Use the commands below to retrieve specific sections:\n" + "\n".join(guide_lines)
    
    return {
        "manifest_id": content_hash,
        "fast_reader": fast_reader_guide
    }
