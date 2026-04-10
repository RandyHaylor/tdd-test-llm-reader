# fastReader

- A document indexing layer for AI agents that reduces token usage, speeds up document traversal, and improves output quality by giving agents structured access to large documents instead of reading them blindly.
  - An efficient wrapper around clever search and scanning tools that counts how documents are structurally separated (chapters, sections, subsections, pages, blocks) and presents a token-efficient interface for previewing and retrieving exactly the right scope.
  - More useful than the current paradigm of LLMs keyword-searching or reading chunk by chunk — because searches return the full container hierarchy (chapter → section → subsection) containing each hit, with previews, so the agent can load exactly the right section in a single command.
  - Agents stop loading random text windows and doing multiple reads above and below to fill in context — instead they get a structured hit with its containing section boundaries and retrieve precisely that.
  - Search quality is higher and more comprehensive than an agent guessing which files to open. Without fastReader, agents pick the files that sound most relevant and hope for the best — missing content spread across multiple files or buried in unexpected locations. fastReader searches across all loaded files simultaneously and surfaces every hit with its structural context, so the agent knows exactly where the answer is before reading a single line of content.
  - Exceptionally well-suited for scanning and overview tasks. A `toc` call across multiple files gives the agent a complete structural map — chapters, sections, subsections — at near-zero token cost, with no content loaded at all. The agent can then `get` only the sections it needs to fill in detail. Tested against a direct file-read approach on the same task, fastReader produced a more accurate, better-structured overview at roughly half the token usage.

---

## Installation

Download the zip for your platform from the [latest release](../../releases/latest), unzip it, and place the `fastReader/` folder in your AI tool's global skills directory. Global installation makes FastReader available across all your projects.

| Platform | Skill folder |
|---|---|
| Claude Code | `~/.claude/skills/` |
| Copilot | `~/.copilot/skills/` |
| Cursor | `~/.cursor/skills/` |
| Cline | `~/.cline/skills/` |
| OpenClaw | `~/.openclaw/skills/` |
| Gemini CLI | `~/.gemini/skills/` |

> Skill folder locations vary by platform version and OS — check your platform's documentation if the path above doesn't work. The goal is global (user-level) installation so the skill is available in every project without copying it in each time.

Python 3 is required. No build step or package installation needed.

---

## What the agent sees

Use FastReader for efficient document indexing and reading:

```
python3 -m fastReader.cli load /path/to/file.md [file2.md ...]
```

Load multiple files at once. After loading, browse with `toc`, retrieve content with `get`, or search across all loaded files:

```
python3 -m fastReader.cli toc <hash> --sections [--chapters] [--subsections] [--blocks] [--sample-size 60]
python3 -m fastReader.cli get <hash> --section 3 [--chapter N] [--subsection N] [--block N]
python3 -m fastReader.cli search <keywords> --manifests <hash1> [hash2 ...] [--exact] [--case-sensitive] [--all] [--sample-size 60]
```

Load and search in one step:

```
python3 -m fastReader.cli load file1.md file2.md --search <keywords> [--exact] [--case-sensitive] [--all] [--sample-size 60]
```

### 1. load — index 3 files at once

```
$ python3 -m fastReader.cli load hooks.md plugins.md memory.md

Loaded 3 files:
  hooks.md                                 hash:b16405a5  chapters:9  sections:10  subsections:114  blocks:175
  plugins.md                               hash:5efa5fb4  chapters:1  sections:6  subsections:14  blocks:24
  memory.md                                hash:ded1ef0c  chapters:4  sections:7  subsections:23  blocks:33

  Browse: python3 -m fastReader.cli toc --sections <hash>
  Search: python3 -m fastReader.cli search <keywords> --manifests b16405a5 5efa5fb4 ded1ef0c [--exact] [--case-sensitive] [--all]
```

### 2. toc — browse structure of hooks.md

```
$ python3 -m fastReader.cli toc b16405a5 --sections

[
  { "type": "section", "index": 1,  "line_number": 15,   "preview": "## Hook lifecycle" },
  { "type": "section", "index": 2,  "line_number": 145,  "preview": "## Configuration" },
  { "type": "section", "index": 3,  "line_number": 457,  "preview": "## Hook input and output" },
  { "type": "section", "index": 4,  "line_number": 668,  "preview": "## Hook events" },
  { "type": "section", "index": 5,  "line_number": 2050, "preview": "## Prompt-based hooks" },
  { "type": "section", "index": 6,  "line_number": 2163, "preview": "## Agent-based hooks" },
  { "type": "section", "index": 7,  "line_number": 2211, "preview": "## Run hooks in the background" },
  { "type": "section", "index": 8,  "line_number": 2310, "preview": "## Security considerations" },
  { "type": "section", "index": 9,  "line_number": 2330, "preview": "## Windows PowerShell tool" },
  { "type": "section", "index": 10, "line_number": 2353, "preview": "## Debug hooks" }
]

# To search: python3 -m fastReader.cli search <keywords> --manifests b16405a5 [hash2 ...] [--exact] [--case-sensitive] [--all]
```

### 3. get — retrieve section 7 content

```
$ python3 -m fastReader.cli get b16405a5 --section 7

## Run hooks in the background

By default, hooks block Claude's execution until they complete. For long-running
tasks like deployments, test suites, or external API calls, set "async": true to
run the hook in the background while Claude continues working...

### Configure an async hook
### How async hooks execute
### Example: run tests after file changes
```

### 4. load with search — index and search in one command

```
$ python3 -m fastReader.cli load hooks.md plugins.md memory.md --search PreToolUse --exact --sample-size 60

Loaded 3 files:
  hooks.md                                 hash:b16405a5  chapters:9  sections:10  subsections:114  blocks:175
  plugins.md                               hash:5efa5fb4  chapters:1  sections:6  subsections:14  blocks:24
  memory.md                                hash:ded1ef0c  chapters:4  sections:7  subsections:23  blocks:33

  Browse: python3 -m fastReader.cli toc --sections <hash>
  Search: python3 -m fastReader.cli search <keywords> --manifests b16405a5 5efa5fb4 ded1ef0c [--exact] [--case-sensitive] [--all]

Search results for: PreToolUse
{
  "b16405a5 (hooks.md)": [
    {
      "line_number": 31,
      "preview": "| `PreToolUse`         | Before a tool call executes. Can bl",
      "containers": {
        "chapter":    { "index": 1, "line_number": 5,  "preview": "# Hooks reference" },
        "section":    { "index": 1, "line_number": 15, "preview": "## Hook lifecycle" }
      }
    },
    {
      "line_number": 855,
      "preview": "### PreToolUse",
      "containers": {
        "chapter":    { "index": 4,  "line_number": 744, "preview": "# Run your setup commands..." },
        "section":    { "index": 4,  "line_number": 668, "preview": "## Hook events" },
        "subsection": { "index": 30, "line_number": 855, "preview": "### PreToolUse" }
      }
    },
    { "...": "40 more hits" }
  ],
  "5efa5fb4 (plugins.md)": [],
  "ded1ef0c (memory.md)": []
}
```

---

## CLI Reference

### load

```bash
python3 -m fastReader.cli load <file> [file2 ...]
  [--search <keywords>] [--exact] [--case-sensitive] [--all] [--sample-size N]
```

Single file returns verbose output with browse/search hints. Multiple files return a compact table. Add `--search` to run a search immediately after loading.

### toc

```bash
python3 -m fastReader.cli toc <hash> --sections [--chapters] [--subsections] [--pages] [--blocks]
  [--sample-size N]   # characters per preview (default: 30)
  [--limit N]         # max entries returned (default: 15, 0 = no limit)
```

### get

```bash
python3 -m fastReader.cli get <hash> --section N [--chapter N] [--subsection N] [--page N] [--block N]
```

### search

```bash
python3 -m fastReader.cli search <keywords> --manifests <hash1> [hash2 ...]
  [--exact]           # whole-word match
  [--case-sensitive]  # default is case-insensitive
  [--all]             # all keywords must appear on same line (default: any)
  [--sample-size N]   # characters per hit preview (default: 80)
```

Results are grouped by `hash (filename)`, each hit showing line number, preview, and containing chapter/section/subsection.

## Structural Markers Detected

| Marker Type | Detection Heuristic |
|---|---|
| Chapters | `Chapter N`, `CHAPTER N`, `#`-style headings |
| Sections | `##`-style headers |
| Subsections | `###`+ headers |
| Page breaks | Form feeds (`\f`), explicit page-break markers |
| Blocks | Fixed-size fallback chunks |

## Design Principles

- No LLM calls during scanning — all detection is regex/heuristic Python.
- One scan, many views — the initial pass captures everything; subsequent commands filter the manifest.
- Configurable patterns — `fastReader/config.json` defines what to detect.

---

## Architecture

FastReader is Python middleware between an AI agent and raw documents. It pre-processes document structure using code-based heuristics (no LLM calls), producing a JSON manifest of structural markers. The agent receives a compact summary of what's in the document and requests only the sections it needs, reducing token usage and cost.

### Core Workflow

1. **Load**: Agent loads a document file into FastReader
2. **Scan**: Python crawls the document for all structural patterns in a single pass
3. **Manifest**: A JSON file is created at `~/.fastReader/cache/` with all detected markers and their line positions
4. **Report**: A compact stats summary is returned (counts per marker type, recommended zoom level)
5. **Browse**: Agent requests a TOC or content at the zoom level that fits its context budget

### Count-Driven Zoom

The agent picks the granularity that keeps output manageable — coarse when counts are low, fine when needed. Use `--chapters` or `--sections` for an overview; drill into `--subsections` or `--blocks` when more detail is needed.

### Manifest Cache

Manifests are stored at `~/.fastReader/cache/` as `<hash>.json` and `<hash>.txt`. The hash is SHA-256 of the file content (first 8 chars). Re-loading a file overwrites the cached manifest.
