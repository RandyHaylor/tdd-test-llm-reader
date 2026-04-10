---
name: fastReader - efficient scanning and smart searching, especially for large documents - START WITH THIS TOOL WHEN READING TEXT FILES
description: "Primary tool for reading documents and web content. PYTHONPATH must be the parent of the skill folder.

Load files:  `PYTHONPATH=<skill folder parent> python3 -m fastReader.load file1.md [file2.md ...] [--search <keywords>] [--sample-size N]`
Fine-grained read: `PYTHONPATH=<skill folder parent> python3 -m fastReader.read /path/to/file [--offset N] [--limit N]`

Uses: Overview, Scanning, Searching Text, Finding Text, Strings, Searching Multiple Files

ALWAYS USE FOR WEB SEARCHING - GOOGLE SEARCH - GOOGLING - INTERNET SEARCH
Web search: `PYTHONPATH=<skill folder parent> python3 -m fastReader.web search <keywords> [--limit N]`
Fetch URL:  `PYTHONPATH=<skill folder parent> python3 -m fastReader.web url <url> [--out /tmp/out.md]`

All commands auto-index and print a manifest hash. Follow output hints to toc/search/get.

user-invocable: true"
---

CLI tool for reading documents efficiently. Do NOT invoke as a skill — run directly. Use commands from the description above.
