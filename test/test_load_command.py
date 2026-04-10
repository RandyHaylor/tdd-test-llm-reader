import os
import shutil
import tempfile
import json
import pytest
from src.fastReader.commands.load import run_load
from src.fastReader.cache import generate_hash
from src.fastReader.models import Document

def test_run_load_basic():
    """T21-T26: Verify run_load returns manifest_id and fast_reader guide."""
    cache_dir = tempfile.mkdtemp()
    try:
        stdin_text = "# Chapter 1\nContent line\n## Section A\nMore content"
        config = {
            "chapter": {"patterns": ["^# "]},
            "section": {"patterns": ["^## "]},
            "subsection": {"patterns": []},
            "page_break": {"patterns": []},
            "page": {"patterns": []},
            "double_line_break": {"patterns": []},
            "block": {"size": 800}
        }
        
        result = run_load(stdin_text, cache_dir, config)
        
        # Check manifest_id
        h = generate_hash(stdin_text)
        assert result["manifest_id"] == h
        
        # Check fast_reader guide
        guide = result["fast_reader"]
        assert "FastReader loaded" in guide
        assert f"python3 -m src.fastReader.cli get --chapter 1 --manifest {h}" in guide
        assert f"python3 -m src.fastReader.cli get --section 1 --manifest {h}" in guide
            
    finally:
        shutil.rmtree(cache_dir)

def test_run_load_empty_document():
    """T26: run_load with empty document returns empty guide."""
    cache_dir = tempfile.mkdtemp()
    try:
        stdin_text = ""
        config = {
            "chapter": {"patterns": ["^# "]},
            "section": {"patterns": ["^## "]},
            "subsection": {"patterns": []},
            "page_break": {"patterns": []},
            "page": {"patterns": []},
            "double_line_break": {"patterns": []},
            "block": {"size": 800}
        }
        result = run_load(stdin_text, cache_dir, config)
        assert "FastReader loaded" in result["fast_reader"]
    finally:
        shutil.rmtree(cache_dir)
