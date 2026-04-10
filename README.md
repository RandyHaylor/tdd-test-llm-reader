# fastReader

- Document indexing
- Smart nested section-based search results
- Smart scanning and overviews
- Reduces token usage, speeds up traversal, improves output quality
- Gives agents structured access to large documents instead of reading them blindly

## What this actually is

- Structured scanning — counts chapters, sections, subsections, pages, blocks in a single pass
  - Token-efficient interface for previewing and retrieving exactly the right scope
- Better than keyword-searching or chunk-by-chunk reading
  - Searches return the full container hierarchy (chapter → section → subsection) with previews
  - Agent loads exactly the right section in a single command — no guessing, no repeated reads
- Higher quality, more comprehensive search than an agent guessing which files to open
  - Searches across all loaded files simultaneously
  - Every hit includes structural context so the agent knows exactly where the answer is before reading a line
- Exceptionally well-suited for scanning and overview tasks
  - `toc` gives a complete structural map at near-zero token cost — no content loaded at all
  - Agent then `get`s only the sections needed

---

## Case Studies

### Overview task — 3 Claude plugin doc files

Two agents given the same task: *"give me an overview of what's covered in these three files."*

| | fastReader agent | direct file-read agent |
|---|---|---|
| Tokens | **17,183** | 30,871 |
| Tool calls | 10 | 4 |
| Output quality | Mapped directly to document's actual section hierarchy | Agent's interpretation of what it skimmed |

fastReader used more tool calls but nearly half the tokens. More importantly, the output was better — structured by the document itself rather than the agent guessing at what mattered.

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

### 1. load — index 2 files at once

```
$ python3 -m fastReader.load plugins.md hooks.md

Loaded 2 files:
  plugins.md                               hash:5efa5fb4  chapters:1  sections:6  subsections:14  blocks:24
  hooks.md                                 hash:b16405a5  chapters:9  sections:10  subsections:114  blocks:175

  Browse: python3 -m fastReader.toc --sections <hash>
  Search: python3 -m fastReader.search <keywords> --manifests 5efa5fb4 b16405a5 [--exact] [--case-sensitive] [--all]
```

### 2. toc — browse structure of plugins.md

```
$ python3 -m fastReader.toc 5efa5fb4 --sections

section 1  ln 13  ## When to use plugins vs stan
section 2  ln 41  ## Quickstart
section 3  ln 174  ## Plugin structure overview
section 4  ln 198  ## Develop more complex plugin
section 5  ln 330  ## Convert existing configurat
section 6  ln 417  ## Next steps

# To search: python3 -m fastReader.search <keywords> --manifests 5efa5fb4 [hash2 ...] [--exact] [--case-sensitive] [--all]
```

### 3. get — retrieve section 1 content

```
$ python3 -m fastReader.get 5efa5fb4 --section 1

## When to use plugins vs standalone configuration

Claude Code supports two ways to add custom skills, agents, and hooks:
...
```

### 4. search — find across both files

```
$ python3 -m fastReader.search "plugin hooks" --manifests 5efa5fb4 b16405a5 --sample-size 60

5efa5fb4 (plugins.md): 0 hits
b16405a5 (hooks.md): 3 hits
  ln 172  For details on settings file resolution, see [settings](/en/
    chapter 2 ln 83  # .claude/hooks/block-rm.sh  section 2 ln 145  ## Configuration
  ln 379  Define plugin hooks in `hooks/hooks.json` with an optional t
    chapter 2 ln 83  # .claude/hooks/block-rm.sh  section 2 ln 145  ## Configuration
  ln 403  See the [plugin components reference](/en/plugins-reference#
    chapter 2 ln 83  # .claude/hooks/block-rm.sh  section 2 ln 145  ## Configuration
```

---

## CLI Reference

> The agent only needs `load` and `read` as seed prompt commands — instructions for `toc`, `get`, and `search` are automatically injected by fastReader's output when context indicates.

### load

```bash
python3 -m <skill folder>/fastReader.load <file> [file2 ...]
  [--search <keywords>] [--exact] [--case-sensitive] [--all] [--sample-size N]
```

Single file returns verbose output with browse/search hints. Multiple files return a compact table. Add `--search` to run a search immediately after loading.

### read

```bash
python3 -m <skill folder>/fastReader.read <file> [--offset N] [--limit N]
```

### toc

```bash
python3 -m <skill folder>/fastReader.toc <hash> --sections [--chapters] [--subsections] [--pages] [--blocks]
  [--sample-size N]   # characters per preview (default: 30)
  [--limit N]         # max entries returned (default: 15, 0 = no limit)
```

### get

```bash
python3 -m <skill folder>/fastReader.get <hash> --section N [--chapter N] [--subsection N] [--page N] [--block N]
```

### search

```bash
python3 -m <skill folder>/fastReader.search <keywords> --manifests <hash1> [hash2 ...]
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
