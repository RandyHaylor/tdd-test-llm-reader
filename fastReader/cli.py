import argparse
import sys
import json
import os
from typing import List, Optional
from fastReader.commands.load import run_load
from fastReader.commands.toc import run_toc
from fastReader.commands.get import run_get
from fastReader.commands.search import run_search
from fastReader.scanner import load_config

DEFAULT_CACHE_DIR = os.path.expanduser("~/.fastReader/cache")
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
AGENT_INSTRUCTIONS_PATH = os.path.join(os.path.dirname(__file__), "agent_instructions.json")

with open(AGENT_INSTRUCTIONS_PATH) as _f:
    _hints = json.load(_f)

def parse_args(argv: List[str]) -> argparse.Namespace:
    """Parse command-line arguments for FastReader CLI."""
    parser = argparse.ArgumentParser(
        prog='llm-fast-reader',
        description='FastReader — Document Structure Layer for AI Agents'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # 'load' subcommand
    load_parser = subparsers.add_parser('load', help='Scan a document file and create manifest')
    load_parser.add_argument('files', nargs='+', help='Path(s) to document file(s)')
    load_parser.add_argument('--search', nargs='+', metavar='KEYWORD', help='Search keywords to run immediately after loading')
    load_parser.add_argument('--exact', action='store_true', help='Whole-word search match')
    load_parser.add_argument('--case-sensitive', action='store_true', help='Case-sensitive search')
    load_parser.add_argument('--all', dest='match_all', action='store_true', help='All keywords must appear on the same line')
    load_parser.add_argument('--sample-size', type=int, default=80, help='Search result preview length (default: 80)')

    # 'toc' subcommand
    toc_parser = subparsers.add_parser('toc', help='Display table of contents')
    toc_parser.add_argument('manifest', help='Manifest hash')
    toc_parser.add_argument('--chapters', action='store_true', help='Show chapters')
    toc_parser.add_argument('--sections', action='store_true', help='Show sections')
    toc_parser.add_argument('--subsections', action='store_true', help='Show subsections')
    toc_parser.add_argument('--pages', action='store_true', help='Show pages')
    toc_parser.add_argument('--blocks', action='store_true', help='Show blocks')
    toc_parser.add_argument('--sample-size', type=int, default=30, help='Preview length (default: 30)')
    toc_parser.add_argument('--limit', type=int, default=15, help='Limit number of entries (default: 15, use 0 for no limit)')

    # 'get' subcommand
    get_parser = subparsers.add_parser('get', help='Retrieve content by reference')
    get_parser.add_argument('manifest', help='Manifest hash')
    get_parser.add_argument('--chapter', type=int, help='Chapter number')
    get_parser.add_argument('--section', type=int, help='Section number')
    get_parser.add_argument('--subsection', type=int, help='Subsection number')
    get_parser.add_argument('--page', type=int, help='Page number')
    get_parser.add_argument('--block', type=int, help='Block number')

    # 'search' subcommand
    search_parser = subparsers.add_parser('search', help='Search for keywords and return hits with container context')
    search_parser.add_argument('keywords', nargs='+', help='Keywords to search for')
    search_parser.add_argument('--manifests', nargs='+', required=True, help='One or more manifest hashes to search')
    search_parser.add_argument('--exact', action='store_true', help='Match whole words only')
    search_parser.add_argument('--case-sensitive', action='store_true', help='Case-sensitive matching (default: case-insensitive)')
    search_parser.add_argument('--all', dest='match_all', action='store_true', help='All keywords must appear on the same line (default: any keyword matches)')
    search_parser.add_argument('--sample-size', type=int, default=80, help='Preview length per hit (default: 80)')

    return parser.parse_args(argv)

def main(argv: Optional[List[str]] = None):
    """Main entry point for FastReader CLI."""
    if argv is None:
        argv = sys.argv[1:]
    
    args = parse_args(argv)
    
    if not os.path.exists(DEFAULT_CACHE_DIR):
        os.makedirs(DEFAULT_CACHE_DIR, exist_ok=True)
        
    config = load_config(DEFAULT_CONFIG_PATH)

    if args.command == 'load':
        loaded = []  # list of (file_path, manifest_id, summary) tuples

        for file_path in args.files:
            try:
                result = run_load(file_path, DEFAULT_CACHE_DIR, config)
            except FileNotFoundError as e:
                print(f"Error: {e}", file=sys.stderr)
                continue
            loaded.append((file_path, result['manifest_id'], result['summary']))

        if len(loaded) == 1:
            # Single file — verbose output with browse/search hints
            file_path, manifest_id, summary = loaded[0]
            print(f"\n{file_path}")
            for key, count in summary.items():
                if count > 0:
                    label = key.replace('_', ' ').title()
                    print(f"  {label}: {count}")
            print(f"\n  {_hints['after_load_single'][0].format(manifest_id=manifest_id)}")
            print(f"  {_hints['after_load_single'][1].format(manifest_id=manifest_id)}")
        else:
            # Multi-file — compact combined table
            print(f"\nLoaded {len(loaded)} files:")
            for file_path, manifest_id, summary in loaded:
                name = os.path.basename(file_path)
                counts = "  ".join(
                    f"{k.split('_')[0]}:{v}"
                    for k, v in summary.items()
                    if v > 0 and k in ('chapters', 'sections', 'subsections', 'blocks')
                )
                print(f"  {name:<40} hash:{manifest_id}  {counts}")

            all_hashes = " ".join(m for _, m, _ in loaded)
            print(f"\n  {_hints['after_load_multi'][0]}")
            print(f"  {_hints['after_load_multi'][1].format(all_hashes=all_hashes)}")

        # Optional inline search
        if args.search and loaded:
            all_hashes_list = [m for _, m, _ in loaded]
            print(f"\nSearch results for: {' '.join(args.search)}")
            try:
                search_results = run_search(
                    all_hashes_list,
                    DEFAULT_CACHE_DIR,
                    keywords=args.search,
                    exact=args.exact,
                    case_sensitive=args.case_sensitive,
                    match_all=args.match_all,
                    preview_length=args.sample_size,
                )
                print(json.dumps(search_results, indent=2))
            except FileNotFoundError as e:
                print(f"Search error: {e}", file=sys.stderr)
        
    elif args.command == 'toc':
        marker_types = []
        if args.chapters: marker_types.append('chapter')
        if args.sections: marker_types.append('section')
        if args.subsections: marker_types.append('subsection')
        if args.pages: marker_types.append('page_break')
        if args.blocks: marker_types.append('block')
        
        if not marker_types:
            marker_types = ['section']
            
        limit = args.limit if args.limit > 0 else None
        
        try:
            result = run_toc(
                args.manifest,
                DEFAULT_CACHE_DIR,
                marker_types=marker_types,
                preview_length=args.sample_size,
                limit=limit
            )
            print(json.dumps(result, indent=2))
            print(f"\n# {_hints['after_toc'].format(manifest_id=args.manifest)}")
        except FileNotFoundError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            sys.exit(1)

    elif args.command == 'get':
        try:
            result = run_get(
                args.manifest,
                DEFAULT_CACHE_DIR,
                chapter=args.chapter,
                section=args.section,
                subsection=args.subsection,
                page=args.page,
                block=args.block
            )
            print(result)
        except FileNotFoundError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            sys.exit(1)
            
    elif args.command == 'search':
        try:
            results = run_search(
                args.manifests,
                DEFAULT_CACHE_DIR,
                keywords=args.keywords,
                exact=args.exact,
                case_sensitive=args.case_sensitive,
                match_all=args.match_all,
                preview_length=args.sample_size,
            )
            print(json.dumps(results, indent=2))
        except FileNotFoundError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            sys.exit(1)

    elif args.command is None:
        parse_args(['--help'])
    else:
        print(f"Command {args.command} not implemented yet.")

if __name__ == "__main__":
    main()
