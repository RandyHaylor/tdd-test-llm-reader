# fastReader

**Deterministic, structural pre-reader for LLM agents and humans.** Turn "open this 7 MB file" into a handful of sub-kilobyte hops. No format-specific config — one tool handles markdown, code, HTML/XML, JSONL, YAML, logs, and plain prose.

<!-- badges: (pre-repo; no CI yet) -->

---

## Why

An LLM that reads a file with the generic `Read` tool spends roughly `bytes / 4` tokens just to see it. For anything over a few hundred KB, that consumes the context window before you've even started reasoning. fastReader's first step, `load`, costs **≤ 1 %** of that on every file type tested — and what it returns isn't a preview, it's a **count histogram for every structural scanner family**. The agent reads the histogram, picks the scanner(s) that match the document's shape, and pulls a custom TOC. No preconceptions about the format needed.

Measured on four real files (2026-04-23, `tokens ≈ bytes / 4`):

| File                                  | Raw bytes | `load` bytes | Savings   |
|---------------------------------------|----------:|-------------:|----------:|
| log4javascript `manual.html` (HTML)   |   213,868 |          766 | **99.64 %** |
| Claude Code plan (markdown)           |    49,379 |          492 | **99.00 %** |
| xstate `api-reference.md` (code docs) |   257,396 |          642 | **99.75 %** |
| 7 MB Claude session JSONL             | 7,041,642 |          672 | **99.99 %** |

Full scenario-by-scenario table further down.

---

## Install (pre-repo)

fastReader is a self-contained Python package. There's no PyPI release yet — just copy the folder under any parent directory and run it as a module.

```bash
# 1. Drop this folder anywhere you like. For Claude Code users, the natural home is:
cp -r fastReader ~/.claude/skills/

# 2. Invoke each subcommand by pointing PYTHONPATH at the PARENT of the fastReader folder:
export PYTHONPATH=~/.claude/skills
python3 -m fastReader.load  <file...>
python3 -m fastReader.toc   <hash> [flags]
python3 -m fastReader.get   <hash> [flags]
python3 -m fastReader.search <keywords...> --manifests <hash> [hash2 ...]
```

Manifest hashes are deterministic from file content + slice range, and cached under `~/.fastReader/cache/`. Tests: `cd fastReader && python3 -m pytest test -q` (98 green as of this writing).

---

## The grammar in one paragraph

`load` reads a file (or several) and returns a short **count histogram** across every structural scanner family, plus a content-addressed hash. You read the histogram and pick a scanner family that matches this document. `toc <hash> --<family>` prints an annotated TOC — line range, child count, and a preview per row. Pick the interesting row, `load --line START COUNT` to slice it into its own hash, and recurse. `get` pulls a row's full content. `search` finds keywords across any number of loaded hashes and returns hits with chapter/section/subsection breadcrumbs.

---

## Live walkthrough 1 — an HTML manual the agent has never seen (214 KB)

```bash
$ python3 -m fastReader.load log4javascript/docs/manual.html
```

```text
  Blocks: 264
  Bracket Depth 1: 87
  Bracket Depth 2: 9
  Indent Depth 5: 228
  Indent Depth 6: 235
  Tag Depth 2: 2
  Tag Depth 3: 2
  Tag Depth 4: 3
  Tag Depth 5: 20      ← one-screen TOC candidate
  Tag Depth 6: 85
  Tag Depth 7: 262
  ...
  Browse: python3 -m fastReader.toc --sections c3bf1ebb
```

No chapters, no sections (this isn't markdown). The histogram tells me `Tag Depth 5: 20` is the one-screen structural view.

```bash
$ python3 -m fastReader.toc c3bf1ebb --tag-depth 5 --show-line-range-count --sample-size 100 --limit 0
```

```text
tag_depth_5 9   ln 122-253  (132)   <div id="loggersappenderslayoutslevels">   (8 children)
tag_depth_5 12  ln 495-928  (434)   <div id="loggers">                         (8 children)
tag_depth_5 13  ln 929-2396 (1468)  <div id="appenders">                       (7 children)
tag_depth_5 14  ln 2397-3033 (637)  <div id="layouts">                         (8 children)
# WARNING: 'tag_depth_5 13' spans 1468 lines but the preview is a tiny window.
```

fastReader auto-fires the integrity warning on the 1468-line giant. Slice-load it to get a fresh hash scoped to those lines, then drill one more level:

```bash
$ python3 -m fastReader.load log4javascript/docs/manual.html --line 929 1468
# → new hash 0c8aca73
$ python3 -m fastReader.toc 0c8aca73 --tag-depth 2 --show-line-range-count --sample-size 100
```

```text
tag_depth_2 2  ln 3-96    (94)   <div id="appender">              (5 children)
tag_depth_2 3  ln 97-113  (17)   <div id="alertappender">         (6 children)
tag_depth_2 4  ln 114-502 (389)  <div id="ajaxappender">          (12 children)
tag_depth_2 5  ln 503-1025 (523) <div id="popupappender">         (11 children)
tag_depth_2 6  ln 1026-1423 (398) <div id="inpageappender">       (10 children)
tag_depth_2 7  ln 1424-1468 (45)  <div id="browserconsoleappender"> (8 children)
```

**Four commands, ≈ 4.3 KB total output, zero preconceptions about the doc.** If the task was "tell me about PopUpAppender", the agent now knows to slice lines 503–1025.

---

## Live walkthrough 2 — a Claude Code plan file (49 KB markdown with code fences)

```bash
$ python3 -m fastReader.load mutable-pondering-pascal.md
```

```text
  Chapters: 10
  Sections: 14            ← narrative TOC
  Subsections: 22
  Bracket Depth 1: 37     ← every fenced code / JSON / subprocess line
  Indent Depth 1: 20
```

Two perpendicular views are useful here — the agent pulls BOTH:

```bash
$ python3 -m fastReader.toc d66092f1 --sections --show-line-range-count --sample-size 100
```

```text
section  7  ln 427-566 (140)  ## Periodic Review Loop (Sanity Checks)
section  8  ln 567-639  (73)  ## Loop Lifecycle: Templates, Archiving, and Recovery
section 14  ln 694-751  (58)  ## User Control — Pause, Override, Exit
```

```bash
$ python3 -m fastReader.toc d66092f1 --bracket-depth 1 --show-line-range-count --sample-size 80
```

```text
bracket_depth_1 17  ln 202-206  (5)   ["git", ...])` works cross-platform ...
bracket_depth_1 29  ln 447-549  (103) {  (4 children)    ← nested JSON/Python block
bracket_depth_1 32  ln 556-588  (33)  {"systemMessage": "REVIEW REJECTED: ..."}
```

The same 49 KB document, two maps (~6 KB combined): narrative structure AND an inventory of every executable artifact. Raw `Read` gives you neither view at any price — just a wall of text.

---

## The four structural scanners (one pass, all at once)

| Scanner            | Flag                | Good for                                                             |
|--------------------|---------------------|----------------------------------------------------------------------|
| Header regex       | `--chapters` / `--sections` / `--subsections` | Markdown / reST / RFCs / anything with `#` or `##` heading syntax    |
| Indent-depth       | `--indent-depth N`  | Python, YAML, outlined notes, pretty-printed JSON                    |
| Bracket-depth      | `--bracket-depth N` | JSONL (record per line), JSON, braces/brackets inside any text       |
| Tag-depth          | `--tag-depth N`     | HTML, XML, SVG, any balanced-tag markup                              |
| Blocks (fallback)  | `--blocks`          | Files with no detectable structure — fixed-size chunk-and-preview    |

`load` runs every scanner simultaneously. You pick which to surface at `toc` time.

---

## Self-documenting CLI

Three help views per subcommand — don't guess flags, ask the tool:

```bash
python3 -m fastReader.toc --help             # argparse flag reference
python3 -m fastReader.toc --help-examples    # copy-paste recipes
python3 -m fastReader.toc --help-use-cases   # "user said X → run Y" mapping
```

Works for `load`, `toc`, `get`, `search`. `--help-examples` / `--help-use-cases` do **not** require the subcommand's normal positional args — `toc --help-examples` works with no hash.

Example (truncated):

```text
$ python3 -m fastReader.toc --help-examples
# Copy-paste examples for: fastReader.toc
# (replace <hash>, <h1>, <h2>, <file> with real values)

# Sections with line ranges and sizes - the essential overview
python3 -m fastReader.toc <hash> --sections --show-line-range-count --sample-size 80

# Hypothesis + conclusion view: intro AND closing thought of every section
python3 -m fastReader.toc <hash> --sections --show-line-range-count \
    --sample-size 80 --end-sample-size 120 --limit 0
...
```

---

## Integrity warnings (do not ignore)

fastReader truncates aggressively — that's the feature. But tidy previews can look authoritative even when the middle of a long block held the critical detail.

1. **After scanning, read in full before concluding.** Once a row of interest is identified, `get --section N` it (or slice-load just that range). Previews are for navigation, not final answers.
2. **If new terminology appeared in a preview, search for it** (`search <term> --manifests <hash>`) before drawing a conclusion.
3. **Heed the high-ratio warning.** When a section spans ≈ 10× the preview size, fastReader prints a `WARNING` line noting the end-preview is the LAST line of the block, **not** a summary.
4. **Don't confuse shape with content.** Tag / bracket / indent counts give you structure. The actual rules live in the content.

fastReader appends an `INTEGRITY NOTE` after every `toc` run. Follow it.

---

## Full benchmark

Four target files. Scenarios:

- **S1** — `wc -c` (raw `Read` cost proxy).
- **S2** — `fastReader.load <file>`.
- **S3** — `toc <hash> --sections --show-line-range-count --sample-size 80`.
- **S4** — S3 + `--end-sample-size 120 --limit 0`.
- **S5** — file-type-specific scanner (tag-depth-2 on HTML, bracket-depth-1 on JSONL, etc.).
- **S6** — slice-drill the biggest entry and re-TOC the slice.
- **S7** — realistic keyword search.

Script: `/tmp/fastReader_token_measurements_script.sh` (emitted in the `reference-docs/phase-b-benchmark-results.md` of this project). All numbers are stdout bytes; tokens ≈ bytes / 4.

| Scenario               | HTML (214 KB) | PLAN (49 KB) | CODEMD (257 KB) | JSONL (7 MB) |
|------------------------|--------------:|-------------:|----------------:|-------------:|
| S1 raw (wc -c)         |       213,868 |       49,379 |         257,396 |    7,041,642 |
| S2 load                |           766 |          492 |             642 |          672 |
| S3 sections            |           551 |        1,471 |           1,306 |          551 |
| S4 sections + end-prev |           551 |        3,313 |           2,581 |          551 |
| S5 format-specific     |           896 |        1,353 |             551 |        3,685 |
| S5b (2nd view)         |             — |        1,915 |           1,594 |            — |
| S6 slice-drill         |         1,298 |        1,386 |           2,074 |        1,138 |
| S7 keyword search      |         1,180 |        3,327 |           3,165 |       45,646 |

S3/S4 "empty" on HTML and JSONL is **correct** — those formats have no markdown-header markers, and the histogram already told the agent to use `--tag-depth` / `--bracket-depth` instead. That choice is the feature.

---

## What fastReader is NOT

- **Not a renderer** — use `quick-json-reader` for JSON visualization.
- **Not a web fetcher** — use your harness's fetch tool; pipe the parsed text through `load`.
- **Not a code understander** — it sees structure, not semantics.
- **Not a replacement for reading** — it's a scope-reducing pre-step. Always pull content in full for decisions that matter.

---

## Contributing / status

Pre-repo. No issue tracker yet. File layout:

```text
fastReader/
├── cli.py              # argparse + dispatch; --help-examples interception
├── scanner.py          # the four structural scanners
├── cache.py            # content-addressed manifest cache (~/.fastReader/cache)
├── help_content.json   # data-driven --help-examples / --help-use-cases
├── agent_instructions.json
├── SKILL.md            # Claude Code skill descriptor + recipes
├── README.md           # this file
└── test/               # pytest suite (98 tests as of 2026-04-23)
```

License: **TBD**.
