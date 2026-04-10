import pytest
from src.fastReader.cli import parse_args

def test_load_subcommand():
    """Test parsing 'load' correctly (no args)."""
    args = parse_args(['load'])
    assert args.command == 'load'

def test_toc_chapters():
    """Test parsing 'toc --chapters --manifest <hash>' correctly."""
    args = parse_args(['toc', '--chapters', '--manifest', 'somehash'])
    assert args.command == 'toc'
    assert args.chapters is True
    assert args.manifest == 'somehash'

def test_toc_sections_with_preview():
    """Test parsing 'toc --sections --preview 60 --manifest <hash>' correctly."""
    args = parse_args(['toc', '--sections', '--preview', '60', '--manifest', 'hash123'])
    assert args.command == 'toc'
    assert args.sections is True
    assert args.preview == 60
    assert args.manifest == 'hash123'

def test_get_chapter():
    """Test parsing 'get --chapter 3 --manifest <hash>' correctly."""
    args = parse_args(['get', '--chapter', '3', '--manifest', 'hash456'])
    assert args.command == 'get'
    assert args.chapter == 3
    assert args.manifest == 'hash456'

def test_get_block():
    """Test parsing 'get --block 7 --manifest <hash>' correctly."""
    args = parse_args(['get', '--block', '7', '--manifest', 'hash789'])
    assert args.command == 'get'
    assert args.block == 7
    assert args.manifest == 'hash789'

def test_get_subsection():
    """Test parsing 'get --subsection 5 --manifest <hash>' correctly."""
    args = parse_args(['get', '--subsection', '5', '--manifest', 'hash000'])
    assert args.command == 'get'
    assert args.subsection == 5
    assert args.manifest == 'hash000'
