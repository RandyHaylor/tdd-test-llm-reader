### FOLLOW THE PLAN AT /home/aikenyon/.claude/plans/humming-doodling-wind.md




# FastReader — Document Structure Layer for AI Agents

## Purpose

FastReader is a Python middleware that sits between an AI agent and raw documents. It pre-processes document structure using code-based heuristics (no LLM calls), producing a JSON manifest of structural markers. The agent receives a compact summary of what's in the document and requests only the sections it needs, reducing token usage and cost.

## Core Workflow

1. **Ingest**: Agent pipes/loads a document into `llm-fast-reader.py`
2. **Scan**: Python crawls the document for all structural patterns in a single pass
3. **Manifest**: A JSON file is created at `.claude/llm-fast-reader/` with all detected markers and their line positions
4. **Report**: A compact stats summary is returned to the agent (counts per marker type, total length, recommended zoom level)
5. **Browse**: Agent requests a TOC or content at the zoom level that fits its context budget

## Structural Markers Detected

All markers are captured in one scan. Each marker records its line number, character offset, and a preview (first N characters of meaningful text, default 30).

| Marker Type | Detection Heuristic |
|---|---|
| Chapters | `Chapter N`, `CHAPTER N`, large heading markup |
| Sections | `Section N`, `##`-style headers, bold/sized subheadings |
| Subsections | `###`+ headers, indented subheadings |
| Page breaks | Form feeds (`\f`), explicit page-break markers |
| Pages | Page number patterns, header/footer repetition |
| Double+ line breaks | Two or more consecutive blank lines |
| Blocks | Fixed-size fallback chunks (~800 chars), used when structural markers are sparse |

A JSON config defines the pattern list and categorization rules so new marker types can be added without code changes.

## CLI Interface

```bash
# Initial scan — returns stats summary
llm-fast-reader.py load <filepath>

# TOC at a specific zoom level
llm-fast-reader.py toc --chapters
llm-fast-reader.py toc --sections
llm-fast-reader.py toc --pages
llm-fast-reader.py toc --blocks

# Retrieve content by reference
llm-fast-reader.py get --chapter 3
llm-fast-reader.py get --section 5
llm-fast-reader.py get --page 12
llm-fast-reader.py get --block 7-9

# Customize preview length
llm-fast-reader.py toc --sections --preview 60
```

## Stats Summary (returned on `load`)

Example output:

```
Document: spec.md (24,310 chars, 487 lines)
  Chapters:    4
  Sections:   12
  Subsections: 38
  Page breaks:  0
  Blocks:      31

Suggested: use --chapters or --sections for an efficient overview.
```

The suggestion logic is simple: recommend the lowest-count marker type that still provides reasonable coverage. If a type has an excessively high count relative to the document length, suggest a coarser level.

## JSON Manifest

Stored at `.claude/llm-fast-reader/<filename>.json`:

```json
{
  "source": "spec.md",
  "total_chars": 24310,
  "total_lines": 487,
  "markers": {
    "chapters": [
      { "index": 1, "line": 1, "offset": 0, "preview": "Introduction to the system..." },
      { "index": 2, "line": 98, "offset": 4820, "preview": "Architecture overview..." }
    ],
    "sections": [ ... ],
    "blocks": [ ... ]
  }
}
```

## Tool Use Syntax Generation

FastReader can generate tool-call snippets so an agent can copy/paste or execute retrieval commands directly. A config JSON or LLM-provided template defines the tool format. Example:

```json
{
  "tool_format": "read_file(path=\"{path}\", start_line={start}, end_line={end})"
}
```

When the agent requests a TOC, each entry includes a ready-made tool call string with the path and line range pre-filled.

## Abbreviated Syntax (Stretch Goal)

After any listing command, results are cached to `recent-listings.json`. The agent can then retrieve by index:

```bash
llm-fast-reader.py get-listing 1    # fetch first item from last listing
llm-fast-reader.py get-listing 3-5  # fetch items 3 through 5
```

## Design Principles

- **No LLM calls during scanning.** All structure detection is regex/heuristic Python code.
- **One scan, many views.** The initial pass captures everything; subsequent commands just filter the manifest.
- **Count-driven zoom.** The agent picks the granularity that keeps output manageable — coarse when counts are low, fine when needed.
- **Configurable patterns.** A JSON file defines what to look for and how to categorize it, so the tool adapts to different document conventions.
