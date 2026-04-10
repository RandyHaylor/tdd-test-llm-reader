import argparse
import sys
import json
import os
from typing import List, Optional
from src.fastReader.commands.load import run_load
from src.fastReader.commands.toc import run_toc
from src.fastReader.commands.get import run_get
from src.fastReader.scanner import load_config

DEFAULT_CACHE_DIR = os.path.expanduser("~/.fastReader/cache")
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def parse_args(argv: List[str]) -> argparse.Namespace:
    """Parse command-line arguments for FastReader CLI."""
    parser = argparse.ArgumentParser(
        prog='llm-fast-reader',
        description='FastReader — Document Structure Layer for AI Agents'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # 'load' subcommand
    load_parser = subparsers.add_parser('load', help='Scan a document file and create manifest')
    load_parser.add_argument('file', help='Path to document file')

    # 'toc' subcommand
    toc_parser = subparsers.add_parser('toc', help='Display table of contents')
    toc_parser.add_argument('manifest', help='Manifest hash')
    toc_parser.add_argument('--chapters', action='store_true', help='Show chapters')
    toc_parser.add_argument('--sections', action='store_true', help='Show sections')
    toc_parser.add_argument('--subsections', action='store_true', help='Show subsections')
    toc_parser.add_argument('--pages', action='store_true', help='Show pages')
    toc_parser.add_argument('--blocks', action='store_true', help='Show blocks')
    toc_parser.add_argument('--preview', type=int, default=30, help='Preview length (default: 30)')
    toc_parser.add_argument('--limit', type=int, default=15, help='Limit number of entries (default: 15, use 0 for no limit)')

    # 'get' subcommand
    get_parser = subparsers.add_parser('get', help='Retrieve content by reference')
    get_parser.add_argument('manifest', help='Manifest hash')
    get_parser.add_argument('--chapter', type=int, help='Chapter number')
    get_parser.add_argument('--section', type=int, help='Section number')
    get_parser.add_argument('--subsection', type=int, help='Subsection number')
    get_parser.add_argument('--page', type=int, help='Page number')
    get_parser.add_argument('--block', type=int, help='Block number')

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
        try:
            result = run_load(args.file, DEFAULT_CACHE_DIR, config)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        # Format summary output as human-readable text
        manifest_id = result['manifest_id']
        summary = result['summary']

        print(f"FastReader found the following:")
        for key, count in summary.items():
            if count > 0:
                label = key.replace('_', ' ').title()
                print(f"  {label}: {count}")

        print(f"\nTo browse, run: python3 -m src.fastReader.cli toc --sections {manifest_id}")
        
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
                preview_length=args.preview,
                limit=limit
            )
            print(json.dumps(result, indent=2))
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
            
    elif args.command is None:
        parse_args(['--help'])
    else:
        print(f"Command {args.command} not implemented yet.")

if __name__ == "__main__":
    main()
