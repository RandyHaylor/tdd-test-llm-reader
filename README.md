# fastReader

**Deterministic, structural pre-reader for LLM agents and humans.** Turn "open this 7 MB file" into a handful of sub-kilobyte hops — across markdown, code, HTML/XML, JSONL, YAML, logs, and plain prose. No per-format config.

<!-- Badges placeholder: CI + release badges go here once configured. -->

---

## Why

An LLM that reads a file with a generic `Read` tool spends roughly `bytes / 4` tokens just to see it. For anything over a few hundred KB, that consumes the context window before you've started reasoning. fastReader's first step — `load` — costs **≤ 1 %** of that on every file type tested and returns a **count histogram across every structural scanner family** (chapters / sections / subsections / blocks plus bracket-depth, tag-depth, indent-depth at every level). **The agent reads that histogram and picks the scanner(s) that match the document's shape.** No preconceptions about the format needed; no per-file-type configuration.

Measured against four real files on 2026-04-23 (`tokens ≈ bytes / 4`):

| File                                            | Raw bytes | `load` bytes | `load` % of raw | Savings on `load` |
|-------------------------------------------------|----------:|-------------:|----------------:|------------------:|
| log4javascript `manual.html` (HTML reference)   |   213,868 |          766 |          0.36 % |       **99.64 %** |
| Claude Code plan (`.md` with fenced code)       |    49,379 |          492 |          1.00 % |       **99.00 %** |
| xstate `api-reference.md` (code-reference docs) |   257,396 |          642 |          0.25 % |       **99.75 %** |
| 7 MB Claude session JSONL                       | 7,041,642 |          672 |        0.0095 % |       **99.99 %** |

Full scenario-by-scenario numbers further down.

---

## The histogram IS the TOC-chooser (the core idea)

`load` doesn't guess what kind of document you gave it. It runs every structural scanner in parallel and prints the count for each marker family:

```
  Chapters: 10
  Sections: 14
  Subsections: 22
  Blocks: 61
  Bracket Depth 1: 37
  Tag Depth 5: 20
  Indent Depth 1: 20
  ...
```

You (or the agent) read those counts and pick the scanner family. Rules of thumb:

- `Sections: 14` on a markdown file? → `toc --sections`.
- `Sections: 0` but `Tag Depth 5: 20` on HTML? → `toc --tag-depth 5`.
- Both `Sections: 14` and `Bracket Depth 1: 37`? → do BOTH — one gives the narrative TOC, the other an inventory of every fenced code block.
- `Bracket Depth 1: 3159` on a JSONL file? → `toc --bracket-depth 1 --limit 20` — one record per line.

Every `toc` row prints the line range `ln START-END (COUNT)`, child count, and a preview. Pick the interesting entry, `load --line START COUNT` to slice it into its own hash, and recurse. Four commands takes you from "214 KB HTML file I've never seen" to "these are the 7 `appender` subtypes, `#popupappender` is the big one at lines 1428–1950" — measured ~4 KB of output total.

---

## Installation

Download the zip for your platform from the [latest release](../../releases/latest), unzip it, and place the `fastReader/` folder in your AI tool's global skills directory:

| Platform     | Skill folder            |
|--------------|-------------------------|
| Claude Code  | `~/.claude/skills/`     |
| Copilot      | `~/.copilot/skills/`    |
| Cursor       | `~/.cursor/skills/`     |
| Cline        | `~/.cline/skills/`      |
| OpenClaw     | `~/.openclaw/skills/`   |
| Gemini CLI   | `~/.gemini/skills/`     |

> Skill folder locations vary by platform version and OS — check your platform's documentation if the path above doesn't match. Global (user-level) installation makes fastReader available across all your projects without per-project copying.

Python 3 is required. No build step, no package install. Optional: install [quick-json-reader](https://github.com/RandyHaylor/quick-json-reader) alongside in the same skills folder to unlock `fastReader json …` (see **Optional `json` module** below).

---

## Invocation — wrapper scripts do the plumbing

`fastReader/` ships with two cross-platform wrapper scripts — `fastReader.sh` (Linux/macOS) and `fastReader.bat` (Windows). They compute `PYTHONPATH` from their own location and dispatch the first positional arg to the right submodule. You never have to touch `PYTHONPATH` yourself.

```bash
# Linux / macOS
~/.claude/skills/fastReader/fastReader.sh load big_doc.md
~/.claude/skills/fastReader/fastReader.sh toc <hash> --sections --show-line-range-count
~/.claude/skills/fastReader/fastReader.sh get <hash> --section 3
~/.claude/skills/fastReader/fastReader.sh search error --manifests <hash>
```

```bat
REM Windows
%USERPROFILE%\.claude\skills\fastReader\fastReader.bat load big_doc.md
%USERPROFILE%\.claude\skills\fastReader\fastReader.bat toc <hash> --sections --show-line-range-count
```

Running the wrapper with no args — or with `--help` — prints the subcommand list, examples, and whether the optional `json` module is detected.

### Direct Python integration (skip the wrapper)

The wrapper is for convenience; the Python modules themselves are the public interface and are safe to invoke directly. Use this path when you want to:

- **Embed fastReader in your own CLI / dispatcher / orchestrator** — call `python3 -m fastReader.<cmd>` from whichever runner you already have.
- **Import as a library** — `from fastReader.commands.load import run_load`, `from fastReader.commands.toc import run_toc`, and so on. Each subcommand's `run_*` function is what the CLI uses internally and is stable.
- **Pipe output into another tool** — no shell-wrapper indirection between your pipeline and Python.
- **Run in a container / CI job** where the wrapper script is awkward to ship.

Invocation:

```bash
PYTHONPATH=~/.claude/skills python3 -m fastReader.load big_doc.md
PYTHONPATH=~/.claude/skills python3 -m fastReader.toc <hash> --sections --show-line-range-count
```

**PYTHONPATH foot-gun:** it must point at the **parent** of the `fastReader/` folder — pointing at `fastReader/` itself fails because `python3 -m fastReader.load` needs `fastReader` importable as a package. The wrapper exists specifically to absorb this; use it if you don't need the direct-Python path.

---

## What the agent sees

### 1. load — index one file

```
$ fastReader.sh load /path/to/log4javascript/docs/manual.html

/.../manual.html
  Blocks: 264
  Bracket Depth 1: 87
  Indent Depth 5: 228
  Indent Depth 6: 235
  Tag Depth 2: 2
  Tag Depth 5: 20          ← one-screen TOC candidate
  Tag Depth 6: 85
  Tag Depth 7: 262
  ...

  Browse: python3 -m fastReader.toc --sections c3bf1ebb
  Search: python3 -m fastReader.search <keywords> --manifests c3bf1ebb [--exact] [--case-sensitive] [--all]
```

No chapters, no sections — this isn't markdown. The histogram tells the agent `Tag Depth 5: 20` is the one-screen structural view.

### 2. toc — custom TOC from the chosen scanner

```
$ fastReader.sh toc c3bf1ebb --tag-depth 5 --show-line-range-count --sample-size 100 --limit 0

tag_depth_5 9   ln 122-253  (132)   <div id="loggersappenderslayoutslevels">   (8 children)
tag_depth_5 12  ln 495-928  (434)   <div id="loggers">                         (8 children)
tag_depth_5 13  ln 929-2396 (1468)  <div id="appenders">                       (7 children)
tag_depth_5 14  ln 2397-3033 (637)  <div id="layouts">                         (8 children)
# WARNING: 'tag_depth_5 13' spans 1468 lines but the preview is a tiny window.
# INTEGRITY NOTE: Previews above are truncated. Read the section in full with 'get' before concluding.
```

fastReader auto-fires the integrity warning on the 1468-line giant.

### 3. drill — slice and re-TOC

```
$ fastReader.sh load /path/to/manual.html --line 929 1468
#  → new hash 0c8aca73 scoped to just those 1468 lines

$ fastReader.sh toc 0c8aca73 --tag-depth 2 --show-line-range-count --sample-size 100

tag_depth_2 2  ln 3-96    (94)   <div id="appender">              (5 children)
tag_depth_2 3  ln 97-113  (17)   <div id="alertappender">         (6 children)
tag_depth_2 4  ln 114-502 (389)  <div id="ajaxappender">          (12 children)
tag_depth_2 5  ln 503-1025 (523) <div id="popupappender">         (11 children)
tag_depth_2 6  ln 1026-1423 (398) <div id="inpageappender">       (10 children)
tag_depth_2 7  ln 1424-1468 (45)  <div id="browserconsoleappender"> (8 children)
```

Four commands, ≈ 4.3 KB total, zero preconceptions about the doc. If the task were "tell me about PopUpAppender", the agent now knows to slice lines 503–1025.

### 4. search — cross-file with structural breadcrumbs

```
$ fastReader.sh search "plugin hooks" --manifests 5efa5fb4 b16405a5 --sample-size 60

5efa5fb4 (plugins.md): 0 hits
b16405a5 (hooks.md): 3 hits
  ln 172  For details on settings file resolution, see [settings]
    chapter 2 ln 83  # .claude/hooks/block-rm.sh    section 2 ln 145  ## Configuration
  ln 379  Define plugin hooks in `hooks/hooks.json` with an optional t
    chapter 2 ln 83  # .claude/hooks/block-rm.sh    section 2 ln 145  ## Configuration
```

Every hit includes its chapter → section → subsection breadcrumb with line numbers, so the agent knows exactly where to `get` from before reading a line.

### 5. get — pull one section's full content

```
$ fastReader.sh get 5efa5fb4 --section 1

## When to use plugins vs standalone configuration

Claude Code supports two ways to add custom skills, agents, and hooks:
...
```

### 6. web — search DuckDuckGo or fetch a URL, auto-indexed

```
$ fastReader.sh web search "python asyncio" --limit 4
Searching DDG: python asyncio ...
  fastreader-search.md    hash:458c6f9b  sections:4  blocks:4

$ fastReader.sh web url https://docs.ollama.com/capabilities/tool-calling --out /tmp/ollama-tool.md
Fetching https://docs.ollama.com/capabilities/tool-calling ...
  ollama-tool.md          hash:d88855ec  chapters:20  blocks:23
```

Results and fetched pages are indexed in the same step — the manifest hash is ready to `toc`, `get`, and `search` immediately. Uses Python's stdlib + a bundled HTML parser; no third-party packages, no API keys.

---

## The four structural scanners (one pass, all at once)

| Scanner        | Flag                                          | Good for                                                             |
|----------------|-----------------------------------------------|----------------------------------------------------------------------|
| Header regex   | `--chapters` / `--sections` / `--subsections` | Markdown / reST / RFCs / any file with `#` or `##` heading syntax    |
| Indent-depth   | `--indent-depth N`                            | Python, YAML, outlined notes, pretty-printed JSON                    |
| Bracket-depth  | `--bracket-depth N`                           | JSONL (record per line), JSON, braces/brackets inside any text       |
| Tag-depth      | `--tag-depth N`                               | HTML, XML, SVG, any balanced-tag markup                              |
| Blocks (fallback) | `--blocks`                                 | Files with no detectable structure — fixed-size chunk-and-preview    |

`load` runs every scanner simultaneously. You pick which to surface at `toc` time.

### Structural Markers Detected

| Marker Type   | Detection Heuristic                                  |
|---------------|------------------------------------------------------|
| Chapters      | `Chapter N`, `CHAPTER N`, `#`-style headings         |
| Sections      | `##`-style headers                                   |
| Subsections   | `###`+ headers                                       |
| Page breaks   | Form feeds (`\f`), explicit page-break markers       |
| Blocks        | Fixed-size fallback chunks                           |
| Bracket depth | Balanced `{…}` / `[…]` nesting levels                |
| Tag depth     | Balanced HTML/XML tag nesting levels                 |
| Indent depth  | Consistent leading-whitespace nesting levels         |

---

## Self-documenting CLI

Three help views per subcommand — don't guess flags, ask the tool:

```bash
fastReader.sh toc --help             # argparse flag reference
fastReader.sh toc --help-examples    # copy-paste recipes
fastReader.sh toc --help-use-cases   # "user said X → run Y" mapping
```

Applies to `load`, `toc`, `get`, `search`. `--help-examples` and `--help-use-cases` do **not** require the subcommand's normal positional args — `toc --help-examples` works with no hash.

---

## Optional `json` module — quick-json-reader integration

fastReader's structural scanners handle JSON/JSONL by **shape** — `--bracket-depth N` gives you one-entry-per-record, line-ranged navigation of any JSON document. For **semantic** JSON work (extracting by value, filtering fields, inferring schema, emitting CSV), install the sister project and fastReader will auto-detect it:

**→ [github.com/RandyHaylor/quick-json-reader](https://github.com/RandyHaylor/quick-json-reader)**

### How the integration works

At startup, `fastReader.sh` / `fastReader.bat` probes for the quick-json-reader binary in this order:

1. `$FAST_READER_JSON_BIN` environment variable (absolute path override).
2. Sibling skills folder: `<parent-of-fastReader>/quick-json-reader/quick-json-reader` (Linux/macOS) or `…\quick-json-reader\quick-json-reader.exe` (Windows).

If found, `json` is listed as a first-class subcommand alongside `load | toc | get | search` in the wrapper's own `--help` output, complete with its own example line. If not found, the help instead shows a clear `Optional module: json (NOT INSTALLED)` block telling the reader how to unlock it — no silent failures, no cryptic "file not found" errors. Invoking `fastReader.sh json …` while the binary is missing exits with code `3` and a stderr install hint.

### Pass-through, not reinterpretation

`fastReader.sh json <args…>` replaces the shell with a direct `exec` of the quick-json-reader binary. **All args after `json` are forwarded verbatim**, and the binary's exit code is preserved. fastReader does not translate, wrap, or second-guess quick-json-reader's flag grammar — that would lose the semantic precision that makes it useful.

### What quick-json-reader adds

Full flag grammar documented in its own repo; a non-exhaustive taste of what the integration unlocks:

```bash
# Find every value matching "error" or "timeout" anywhere in a deep doc
fastReader.sh json large_api_response.json --search-vals error timeout

# Locate structures by key name, expand their children
fastReader.sh json session.json --search-keys user profile --include-search-children

# Strip noise before piping to an agent (tokens, secrets, debug fields)
fastReader.sh json log.json --exclude-fields-matching token password secret
fastReader.sh json log.json --exclude-fields-containing debug internal temp

# Compose search + exclude + output format for clean machine handoff
fastReader.sh json log.json --search-vals user123 --exclude-fields-matching token --output json

# Inspect structure without dumping values (must be used alone)
fastReader.sh json big.json --show-schema
```

Output formats: `txt` (default, human), `csv` (RFC-compliant, tabular extraction), `json` (structured projection, best for tool chaining), `schema` (inferred structure).

### When to use which tool

| You want to …                                                              | Use                                                     |
|----------------------------------------------------------------------------|---------------------------------------------------------|
| Navigate a 7 MB JSONL chat log by record                                   | `fastReader.sh load`+ `toc --bracket-depth 1`            |
| Preview the 50th record's first 120 chars                                  | `fastReader.sh toc <hash> --bracket-depth 1 --sample-size 120` |
| Slice a big nested JSON doc into top-level entries                         | `fastReader.sh toc <hash> --bracket-depth 1`             |
| Find every `"error"` value regardless of nesting                           | `fastReader.sh json file.json --search-vals error`       |
| Strip `token` / `password` fields before handing JSON to another agent     | `fastReader.sh json file.json --exclude-fields-matching token password --output json` |
| Learn the shape of an unfamiliar JSON API response                         | `fastReader.sh json file.json --show-schema`             |
| Extract a sub-tree as CSV for spreadsheet handoff                          | `fastReader.sh json file.json --search-keys events --output csv` |

The two tools are complementary: fastReader for *where is it* (structural navigation), quick-json-reader for *what does it contain* (semantic extraction). They share the skills folder and the wrapper script; installing both costs you one copy-folder step.

### Help surface when the binary is absent

```text
$ fastReader.sh
usage: fastReader <subcommand> [args...]
subcommands: load | toc | get | search
...

Optional module:
  json  (NOT INSTALLED)
        fastReader already efficiently parses and displays bracketed and
        tagged text. For much more versatile JSON-specific integration —
        schema inference, value search, field exclusion — install the
        quick-json-reader skill alongside this one. When the binary is
        detected at <skills-parent>/quick-json-reader/quick-json-reader
        (or the FAST_READER_JSON_BIN env var), the json module becomes
        available automatically. No reinstall of fastReader required.
```

### Help surface when the binary is present

```text
$ fastReader.sh
usage: fastReader <subcommand> [args...]
subcommands: load | toc | get | search | json
examples:
  fastReader load big_doc.md
  fastReader toc <hash> --sections --show-line-range-count
  fastReader get <hash> --section 3
  fastReader search error --manifests <hash>
  fastReader json file.json --search-vals error
Add --help / --help-examples / --help-use-cases to any subcommand
for argparse flags, copy-paste recipes, or trigger->command mapping.

The json subcommand is provided by the sibling quick-json-reader skill,
detected on the skills-root alongside fastReader. Override the probed
path with the FAST_READER_JSON_BIN environment variable.
```

Both help variants live in text files (`wrapper_help_json_on.txt` and `wrapper_help_json_off.txt`) that the `.sh` and `.bat` wrappers share — editing the help text touches one file and both platforms update in lockstep.

No `fastReader` reinstall is needed when you add (or remove) quick-json-reader later — the wrapper detects the binary on every invocation.

---

## Measured benchmark (full scenario sweep)

Four target files. Seven scenarios per file:

| ID | Scenario |
|----|----------|
| S1 | `wc -c` (raw `Read` cost proxy) |
| S2 | `fastReader.sh load <file>` |
| S3 | `toc <hash> --sections --show-line-range-count --sample-size 80` |
| S4 | S3 + `--end-sample-size 120 --limit 0` |
| S5 | File-type-specific scanner (tag-depth-2 on HTML, bracket-depth-1 on JSONL, etc.) |
| S6 | Slice-drill the biggest entry, re-TOC the slice |
| S7 | Realistic keyword search |

`tokens ≈ bytes / 4`. All numbers are stdout bytes from the measurement script.

| Scenario                  |    HTML (214 KB) | PLAN (49 KB) | CODEMD (257 KB) | JSONL (7 MB) |
|---------------------------|-----------------:|-------------:|----------------:|-------------:|
| S1 raw (wc -c)            |          213,868 |       49,379 |         257,396 |    7,041,642 |
| S2 load                   |              766 |          492 |             642 |          672 |
| S3 sections               |              551 |        1,471 |           1,306 |          551 |
| S4 sections + end-previews |              551 |        3,313 |           2,581 |          551 |
| S5 format-specific view   |              896 |        1,353 |             551 |        3,685 |
| S5b (2nd complementary view) |             — |        1,915 |           1,594 |            — |
| S6 slice-drill            |            1,298 |        1,386 |           2,074 |        1,138 |
| S7 keyword search         |            1,180 |        3,327 |           3,165 |       45,646 |

S3/S4 returning only the boilerplate footer on HTML and JSONL is **correct** — those formats have no markdown-header markers, and the histogram already told the agent to reach for `--tag-depth` / `--bracket-depth` instead. That choice is the feature.

---

## Case studies

### Overview task — three Claude plugin doc files

Two agents given the same prompt: *"give me an overview of what's covered in these three files."*

|                  | fastReader agent                                                           | direct file-read agent                         |
|------------------|----------------------------------------------------------------------------|------------------------------------------------|
| Tokens           | **17,183**                                                                 | 30,871                                         |
| Tool calls       | 10                                                                         | 4                                              |
| Output quality   | Mapped directly to each document's actual section hierarchy                | Agent's interpretation of what it skimmed      |

More tool calls, nearly half the tokens, better-structured output.

### Inspecting an agent JSONL log — the tool eating its own cooking

An 11,830-token JSONL needed to be inspected to check what tool calls an agent made. Reading it directly would have blown the context window. Instead:

1. `fastReader.sh load <file>` indexed it (~300 B).
2. Three targeted `fastReader.sh search ... --manifests <hash>` calls extracted only the relevant tool-call lines.

Total tokens to answer the question: **~300**. Reading the file directly: 11,830 — and it would have failed entirely.

Keyword-only tools (grep, generic search) can also find matches in JSONL, but each matching line is thousands of characters and gets truncated or omitted. fastReader returns structured previews with line numbers, then lets you `get` the exact block — the advantage is **navigation after the find**, not just the find itself.

---

## Integrity warnings (do not ignore)

fastReader truncates aggressively — that's the feature. But a tidy 120-char end-preview can look authoritative even when the middle of a long block held the critical rule.

1. **After scanning, read in full before concluding.** Once a row is identified, `get --section N` it (or slice-load the line range). Previews are for navigation, not final answers.
2. **If new terminology appeared in a preview, search for it** (`search <term> --manifests <hash>`) before drawing conclusions.
3. **Heed the high-ratio warning.** When a section spans ≈ 10× the preview size, fastReader prints an explicit `WARNING` line noting the end-preview is the LAST line of the block, **not** a summary.
4. **Don't confuse shape with content.** Tag / bracket / indent counts give you structure. The rules live in the content.

Every `toc` run ends with an `INTEGRITY NOTE`. Follow it.

---

## CLI reference

### Common pattern

```bash
fastReader.sh <load|toc|get|search|web|read> [args...]
# or, without the wrapper:
PYTHONPATH=<parent-of-fastReader-folder> python3 -m fastReader.<cmd> [args...]
```

### load

```
fastReader.sh load <file> [file2 ...]
  [--line START COUNT]                       # slice-ingest only those lines as a new hash
  [--search <keywords>]                      # run a search immediately after loading
  [--exact] [--case-sensitive] [--all]
  [--sample-size N]                          # search preview length (default 80)
  [--help-examples] [--help-use-cases]
```

Single-file load returns verbose output + browse/search hints. Multiple files return a compact table with one hash per file.

### toc

```
fastReader.sh toc <hash>
  [--chapters] [--sections] [--subsections] [--pages] [--blocks]
  [--indent-depth N] [--bracket-depth N] [--tag-depth N]
  [--sample-size N]                          # start-preview chars (default 30)
  [--end-sample-size N]                      # end-preview chars (default 0 = off)
  [--limit N]                                # max entries (default 15, 0 = unlimited)
  [--show-line-range-count]                  # print ln START-END (COUNT)
  [--help-examples] [--help-use-cases]
```

### get

```
fastReader.sh get <hash>
  [--chapter N] [--section N] [--subsection N] [--page N] [--block N]
  [--help-examples] [--help-use-cases]
```

### search

```
fastReader.sh search <keywords...> --manifests <hash1> [hash2 ...]
  [--exact]                                  # whole-word match
  [--case-sensitive]                         # default: case-insensitive
  [--all]                                    # all keywords on same line (default: any)
  [--sample-size N]                          # preview chars per hit (default 80)
  [--help-examples] [--help-use-cases]
```

Results are grouped by `hash (filename)`, each hit showing line number, preview, and chapter/section/subsection breadcrumb.

### read

```
fastReader.sh read <file> [--offset N] [--limit N]
```

Direct line-range read from a file without indexing.

### web

```
fastReader.sh web search <keywords> [--limit N] [--out /tmp/file.md]
fastReader.sh web url <url> [--out /tmp/file.md]
```

Default output files: `/tmp/fastreader-search.md` (search) or `/tmp/fastreader-url.md` (url). Uses DuckDuckGo HTML search — no API key. Stdlib-compatible HTML parsing; no third-party deps.

### json (optional — requires quick-json-reader)

```
fastReader.sh json <args...>   # pass-through to quick-json-reader binary
```

Set `FAST_READER_JSON_BIN` to override the auto-detected binary path.

---

## Architecture

fastReader is Python middleware between an AI agent and raw documents. It pre-processes document structure using code-based heuristics (**no LLM calls during scanning**), producing a JSON manifest of structural markers. The agent receives a compact count histogram and requests only what it needs.

### Core workflow

1. **Load** — agent loads file(s) into fastReader.
2. **Scan** — Python crawls the document for all structural patterns in a single pass.
3. **Manifest** — JSON + txt written to `~/.fastReader/cache/` with all detected markers and line positions.
4. **Report** — compact histogram summary returned (counts per marker family + recommended browse/search hints).
5. **Browse / drill** — agent picks a scanner based on the histogram, requests a TOC at the right granularity, drills by slicing line ranges.

### Histogram-driven zoom

The agent picks the scanner family AND granularity that keep output manageable. Coarse when counts are low, fine when counts are dense. `toc --sections` on a markdown doc; `toc --tag-depth 5 --limit 0` on an HTML manual; `toc --bracket-depth 1 --limit 20` on a JSONL log.

### Design principles

- **No LLM calls during scanning** — all detection is regex/heuristic Python.
- **One scan, many views** — the initial pass captures everything; subsequent commands filter the manifest without re-reading the file.
- **Configurable patterns** — `fastReader/config.json` defines what to detect.
- **Content-addressed manifests** — hash is SHA-256 of file content (first 8 chars) so re-loading a file hits the cache.

### Manifest cache

Manifests are stored at `~/.fastReader/cache/` as `<hash>.json` and `<hash>.txt`. Re-loading a file overwrites the cached manifest. Slice-loads (`--line START COUNT`) produce their own distinct hashes keyed by content of the slice.

---

## What fastReader is NOT

- **Not a renderer** — use [quick-json-reader](https://github.com/RandyHaylor/quick-json-reader) for JSON visualization / extraction.
- **Not a web-scraping framework** — `fastReader.web` is a thin DDG + stdlib parser convenience, not a replacement for a real scraper.
- **Not a code understander** — it sees structure, not semantics.
- **Not a replacement for reading** — it's a scope-reducing pre-step. Pull content in full for decisions that matter.

---

## Contributing

- Tests: `python3 -m pytest fastReader/test -q` (Python 3.8+). At last check, **108 tests green**, including the wrapper-script suite.
- Issue tracker: GitHub Issues on this repo.
- Pre-1.0 — APIs and flag names may still change. The scanner families and `load → toc → get → search` grammar are stable.

## License

TBD.
