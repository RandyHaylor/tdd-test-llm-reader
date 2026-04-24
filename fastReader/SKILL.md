---
name: fastReader
description: "Structural scanner and drilldown for text, JSON/JSONL, HTML, code, logs — USE FIRST BEFORE READING ANY LARGE FILE. Primary tool for navigating large or unfamiliar text. Load one or many files, get a structural TOC instantly, drill into the interesting sections, search across all loaded files with container context. Works on ANY text-like format (markdown, code, JSONL chat logs, YAML, HTML, plain prose) because it has four independent structural scanners (chapter/section regex, indent-depth, JSON bracket-depth, HTML/XML tag-depth) running simultaneously.

Core commands (replace <parent> with the folder containing this skill's folder, e.g. ~/.claude/skills):

Load:   `PYTHONPATH=<parent> python3 -m fastReader.load file1 [file2 ...] [--line START COUNT] [--search keyword]`
TOC:    `PYTHONPATH=<parent> python3 -m fastReader.toc <hash> [--sections|--subsections|--indent-depth N|--bracket-depth N|--tag-depth N] [--sample-size N] [--end-sample-size N] [--show-line-range-count]`
Get:    `PYTHONPATH=<parent> python3 -m fastReader.get <hash> [--section N|--subsection N|--block N]`
Search: `PYTHONPATH=<parent> python3 -m fastReader.search <keyword> --manifests <hash> [hash2 ...]`"
user-invocable: true
---

# fastReader — Your first move on any big file

Reading a file with the Read tool costs roughly `bytes / 4` tokens. fastReader's initial `load` step costs **≤ 1 %** of that — and tells you the document's full structural histogram in one shot.

Measured against four real files on 2026-04-23 (`tokens ≈ bytes / 4`):

| File type               | Raw bytes | `load` bytes | `load` as % of raw | Savings on `load` |
|-------------------------|----------:|-------------:|-------------------:|------------------:|
| HTML reference manual   |   213,868 |          766 |              0.36 % |       **99.64 %** |
| Claude Code plan (.md)  |    49,379 |          492 |              1.00 % |       **99.00 %** |
| Code-reference markdown |   257,396 |          642 |              0.25 % |       **99.75 %** |
| 7 MB session JSONL      | 7,041,642 |          672 |            0.0095 % |       **99.99 %** |

Full benchmark (S1–S7 per file) lives in the project's `reference-docs/phase-b-benchmark-results.md`. Reading the whole 7 MB session JSONL straight would blow the context window; fastReader navigates it in ≈1 KB increments.

**Use fastReader whenever a file is >500 lines, or you don't know its structure yet, or you have multiple files to search across.**

## The histogram IS the TOC-chooser (the core idea)

`load` doesn't guess what kind of document you gave it. It runs every structural scanner in parallel and prints the count for each marker family: chapters / sections / subsections / blocks, and then `Bracket Depth 1…N`, `Tag Depth 1…N`, `Indent Depth 1…N`. **You read those counts and pick the scanner that matches this document's shape.**

- `Sections: 14` on a markdown plan? → `toc --sections`.
- `Sections: 0` but `Tag Depth 5: 20` on an HTML page? → `toc --tag-depth 5`.
- Both `Sections: 14` and `Bracket Depth 1: 37`? → do BOTH — one gives the narrative TOC, the other an inventory of every fenced code block.
- `Bracket Depth 1: 3159` on a 7 MB JSONL? → `toc --bracket-depth 1 --limit 20` — one record per line.

Every `toc` row prints line range + child count + a preview. Pick the interesting one, `load --line START COUNT` to slice it into its own hash, and recurse. Four commands takes you from "214 KB HTML file I've never seen" to "these are the 7 appender subtypes, `#popupappender` is the big one at lines 1428–1950" — measured ~4 KB of output total.

## The one-paragraph grammar

`load` → fastReader scans the file once and returns the marker-count histogram + a hash. You read the histogram and pick a scanner family. Use that hash with `toc <flag>` to see the real map. Pick an entry, use `get` to pull its full content, or use `load --line START COUNT` to carve out a sub-document with its own hash (for recursive drilling). Multi-file loads give you parallel hashes and one cross-search across all of them.

## Discovering commands without leaving the shell

Every subcommand exposes three help views — use these instead of guessing flags:

- `python3 -m fastReader.<cmd> --help` — argparse flag reference.
- `python3 -m fastReader.<cmd> --help-examples` — copy-paste recipes curated per subcommand.
- `python3 -m fastReader.<cmd> --help-use-cases` — "user said X → run Y" trigger mapping.

Applies to `load`, `toc`, `get`, `search`. The `--help-*` flags do not require the subcommand's normal positional arguments, so `toc --help-examples` works without a hash.

## Trigger patterns — when to use what

| User said | First call |
|---|---|
| "find what hooks.md says about SessionStart" | `load hooks.md` → `search SessionStart --manifests <hash>` |
| "summarize this 10k-line doc" | `load doc.md` → `toc --sections --show-line-range-count --sample-size 80 --end-sample-size 120` |
| "look at the event handlers in this Python file" | `load file.py` → `toc <hash> --indent-depth 1` |
| "what record types are in this Claude session?" | `load session.jsonl` → `toc <hash> --bracket-depth 1 --sample-size 80` |
| "read just this specific section" | `get <hash> --section N` or `load <file> --line START COUNT` |
| "search all my log files for errors" | `load log1 log2 log3` → `search error --manifests <h1> <h2> <h3>` |
| "we talked about X earlier" (session JSONL lost) | `load ~/.claude/projects/*.jsonl` → `search "X" --manifests ...` |

## Recipe book (copy-paste, adjust paths)

### Recipe 1 — Scan an unfamiliar large file

```bash
PYTHONPATH=<parent> python3 -m fastReader.load big_doc.md
```
Output: chapters/sections/subsections counts, indentation/bracket/tag depth counts, block count, and the hash.

### Recipe 2 — Get a navigable TOC with size info and end-peek

```bash
PYTHONPATH=<parent> python3 -m fastReader.toc <hash> \
  --sections --show-line-range-count \
  --sample-size 80 --end-sample-size 120 --limit 0
```
Each row shows: `section 4  ln 668-2049 (1382)  ## Hook events` plus start preview and end preview. For a 10-section 2400-line file this costs ~1.5 KB. You see where the biggest sections are AND what they conclude with.

### Recipe 3 — Drill into a big section without loading the whole file

```bash
# First see a huge section in the TOC above. Say it spans line 668, 1382 lines.
PYTHONPATH=<parent> python3 -m fastReader.load big_doc.md --line 668 1382
# → produces a NEW hash for just those 1382 lines.
PYTHONPATH=<parent> python3 -m fastReader.toc <new_hash> \
  --subsections --show-line-range-count --sample-size 60 --end-sample-size 80
```
Line numbers re-zero to the slice. You can drill again recursively (slice the slice).

### Recipe 4 — Find what you want, with context

```bash
PYTHONPATH=<parent> python3 -m fastReader.search SessionStart --manifests <hash> --sample-size 80
```
Every hit returns: line number, preview, and "chapter X / section Y / subsection Z" breadcrumb with line numbers.

### Recipe 5 — Multi-file cross-search

```bash
PYTHONPATH=<parent> python3 -m fastReader.load doc1.md doc2.md doc3.md
# Compact table returns 3 hashes. Search all three at once:
PYTHONPATH=<parent> python3 -m fastReader.search "error code" --manifests <h1> <h2> <h3>
```
Zero-hit files say `0 hits`; skip them. High-hit files get drilled.

### Recipe 6 — Navigate code by indentation (Python, YAML, outlines)

```bash
PYTHONPATH=<parent> python3 -m fastReader.load some_module.py
PYTHONPATH=<parent> python3 -m fastReader.toc <hash> --indent-depth 0 --sample-size 80
# → Top-level defs/classes.
PYTHONPATH=<parent> python3 -m fastReader.toc <hash> --indent-depth 1 --sample-size 80
# → Methods, inner scopes.
```

### Recipe 7 — Navigate JSONL by record

```bash
PYTHONPATH=<parent> python3 -m fastReader.load session.jsonl
# Each JSONL line starts at bracket depth 1. Preview each record's first 120 chars.
PYTHONPATH=<parent> python3 -m fastReader.toc <hash> --bracket-depth 1 --sample-size 120 --limit 20
```

### Recipe 8 — Navigate HTML/XML

```bash
PYTHONPATH=<parent> python3 -m fastReader.load page.html
PYTHONPATH=<parent> python3 -m fastReader.toc <hash> --tag-depth 2 --sample-size 60
# → Direct children of <html>: <head>, <body>, etc.
```

### Recipe 9 — Find what a user remembers from an earlier session

When the user says "we talked about X" or "you said before" or "I told you earlier":

```bash
# Load the current session + any older sessions for this project
PYTHONPATH=<parent> python3 -m fastReader.load \
  ~/.claude/projects/<project-slug>/<session-id>.jsonl
# Search inside the session for the term/topic
PYTHONPATH=<parent> python3 -m fastReader.search "X" --manifests <hash>
```
Do this BEFORE claiming you don't recall. Session JSONLs hold the real transcript.

## Flag cheat sheet

| `toc` flag | Effect |
|---|---|
| `--sections` / `--chapters` / `--subsections` / `--blocks` / `--pages` | Pick which marker kind to list |
| `--indent-depth N` | Lines entering indent level N |
| `--bracket-depth N` | Positions entering JSON nesting level N |
| `--tag-depth N` | Balanced HTML/XML tags at level N |
| `--show-line-range-count` | Print `ln START-END (COUNT)` for each entry |
| `--sample-size N` | First N chars of each entry (default 30) |
| `--end-sample-size N` | Last N chars of each entry's span (default 0 = off) |
| `--limit N` | Max entries shown (0 = no cap) |

| `load` flag | Effect |
|---|---|
| `--line START COUNT` | Ingest only lines START..START+COUNT-1 as a new hashed doc |
| `--search kw [kw...]` | Immediately search after load |
| `--sample-size N` | Search preview length |

## INTEGRITY — the warning fastReader itself prints

This tool truncates aggressively. That's the feature. But it creates a real failure mode: a tidy 120-char end-preview can look authoritative even when the middle 1,300 lines contained the critical rule.

Rules of the road:

1. **After scanning, read in full before concluding.** If you identified a section, `get --section N` it (or `load --line START COUNT` to re-ingest). Previews are for navigation, NOT for final answers.
2. **If new terminology appeared in a preview, search for it.** A term glimpsed in an end-preview may appear elsewhere with different context. `search <term> --manifests <hash>` before you draw a conclusion.
3. **Heed the high-ratio warning.** When a section spans ~10× the preview size or more, fastReader prints a `WARNING` line explicitly noting the end-preview is the LAST line of the block, NOT a summary. Respect it — `get` that section.
4. **Don't confuse "shape" with "content."** Tag/bracket/indent scanners give you structure. The actual rules/values live in the content. Always pull content for decisions that matter.

fastReader itself appends an `INTEGRITY NOTE` after every `toc` output. Follow it.

## What fastReader is NOT

- **Not a renderer** — use `quick-json-reader` for JSON visualization.
- **Not a web fetcher** — use Claude Code's WebFetch; pipe the parsed text through `load`.
- **Not a code understander** — it sees structure, not semantics. For "what does this function do" you still need to read the code.
- **Not a replacement for reading** — it's a scope-reducing pre-step. Always read in full once you've narrowed the target.

## Tiny mental model

```
LOAD   →   hash   →   TOC  →   pick an entry   →   GET or SLICE-LOAD   →   content
                                     ↓
                                   SEARCH (find, with breadcrumbs)
```

Ten files? Ten hashes in parallel from one `load`. Cross-search them as a group.

For a human-friendly walkthrough with live transcripts and the benchmark table, see `README.md` in this skill folder.

---

**If the user invoked this skill, assume they want you to use it for something.**
