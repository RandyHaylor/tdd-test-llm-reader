# Architecture — Sprint 0

## Core Concept

FastReader is a standalone Python CLI that:
1. Accepts document text via stdin
2. Saves normalized text to cache
3. Scans for structural markers (chapters, sections, subsections, pages, page_breaks, blocks)
4. Builds a JSON manifest with all marker positions
5. Returns stats to the user
6. Can generate custom TOCs on demand

No LLM calls during scanning. Pure regex/heuristic detection.

## Data Structures

### Marker
```python
{
  "index": int,           # 1, 2, 3... within this marker type
  "line_number": int,     # Line where marker starts (1-indexed)
  "char_index": int       # Position within line where content starts (skips whitespace)
}
```

### Manifest
```python
{
  "source": str,          # Path to cached txt file
  "total_chars": int,     # Total characters in document
  "total_lines": int,     # Total lines in document
  "markers": {
    "chapters": [Marker, ...],
    "sections": [Marker, ...],
    "subsections": [Marker, ...],
    "pages": [Marker, ...],
    "page_breaks": [Marker, ...],
    "blocks": [Marker, ...]
  }
}
```

### Document
```python
{
  "file_path": str,       # Path to cached txt
  "content": str,         # Raw text content
  "manifest": Manifest
}
```

## Manifest JSON Example

```json
{
  "source": "~/.claude/llm-fast-reader/<hash>.txt",
  "total_chars": 24310,
  "total_lines": 487,
  "markers": {
    "chapters": [
      { "index": 1, "line_number": 1, "char_index": 0 },
      { "index": 2, "line_number": 98, "char_index": 0 },
      { "index": 3, "line_number": 250, "char_index": 2 }
    ],
    "sections": [
      { "index": 1, "line_number": 5, "char_index": 0 },
      { "index": 2, "line_number": 42, "char_index": 4 },
      { "index": 3, "line_number": 105, "char_index": 2 }
    ],
    "subsections": [
      { "index": 1, "line_number": 8, "char_index": 4 }
    ],
    "pages": [
      { "index": 1, "line_number": 1, "char_index": 0 },
      { "index": 2, "line_number": 65, "char_index": 0 }
    ],
    "page_breaks": [],
    "blocks": [
      { "index": 1, "line_number": 1, "char_index": 0 },
      { "index": 2, "line_number": 31, "char_index": 0 }
    ]
  }
}
```

## CLI Operations

### Operation 1: save_and_scan

**Command:**
```bash
cat large_doc.txt | llm-fast-reader.py load
```

**Process:**
1. Read stdin and save to `~/.claude/llm-fast-reader/<hash>.txt`
2. Scan the saved txt file for all structural markers
3. Build and save manifest to `~/.claude/llm-fast-reader/<hash>.json`
4. Return stats (counts only, no internal manifest shown)

**Returns:**
```json
{
  "chapters": 4,
  "sections": 12,
  "subsections": 38,
  "pages": 10,
  "page_breaks": 0,
  "blocks": 31,
  "cache_path": "~/.claude/llm-fast-reader/<hash>.txt"
}
```

**Purpose:** LLM sees counts to decide what granularity to request in TOC.

### Operation 2: build_toc

**Command:**
```bash
llm-fast-reader.py toc --pages --sections --manifest <hash> --preview 50
```

**Parameters:**
- `--pages`, `--sections`, `--subsections`, `--chapters`, `--blocks`: marker types to include
- `--manifest <hash>`: reference to the saved manifest
- `--preview <n>`: extract preview of N characters starting at each marker (default: 30)

**Process:**
1. Load manifest from cache
2. Filter markers by requested types
3. Limit to ~15 entries total (mix of types)
4. Extract preview snippets from cached txt file
5. Return TOC with snippets

**Returns:**
```json
[
  {
    "type": "page",
    "index": 1,
    "line_number": 1,
    "preview": "Introduction to the system architecture..."
  },
  {
    "type": "section",
    "index": 1,
    "line_number": 5,
    "preview": "Core Components The system is built around..."
  },
  ...
]
```

**Purpose:** LLM gets a curated TOC with snippets to navigate the cached txt file.

## Pattern Config (JSON, loaded with defaults)

```json
{
  "patterns": [
    {
      "type": "chapter",
      "regex": "^Chapter \\d+|^CHAPTER \\d+",
      "category": "chapters"
    },
    {
      "type": "section",
      "regex": "^Section \\d+|^##\\s|^---",
      "category": "sections"
    },
    {
      "type": "subsection",
      "regex": "^###\\s|^\\*\\*.*\\*\\*",
      "category": "subsections"
    },
    {
      "type": "page_break",
      "regex": "^\\f|^\\[PAGE BREAK\\]",
      "category": "page_breaks"
    },
    {
      "type": "page",
      "regex": "^--- Page \\d+ ---|page \\d+ of",
      "category": "pages"
    }
  ],
  "block_size": 800
}
```

## Utility Functions

- `extract_preview(content, line_number, char_index, length) -> str`
- `scan_document(file_path, config) -> Document`
- `save_manifest(manifest, output_dir) -> str (manifest_path)`
- `load_manifest(manifest_path) -> Manifest`
- `generate_hash(content) -> str`
- `build_toc(manifest, marker_types, preview_length, limit=15) -> List[Dict]`
