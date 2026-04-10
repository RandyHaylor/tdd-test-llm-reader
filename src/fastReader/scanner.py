import json
import re
from typing import Dict, List
from src.fastReader.models import Document, Manifest, Marker


def load_config(config_path: str) -> dict:
    """Load configuration from a JSON file.

    Args:
        config_path: Path to the configuration JSON file

    Returns:
        Dictionary containing the configuration
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def scan_document(document: Document, config: dict) -> Manifest:
    """Scan a document for structural markers using patterns from config.

    Args:
        document: Document object with path, content, and lines
        config: Configuration dictionary with marker patterns

    Returns:
        Manifest object with detected markers
    """
    markers: Dict[str, List[Marker]] = {
        "chapter": [],
        "section": [],
        "subsection": [],
        "page_break": [],
        "page": [],
        "double_line_break": [],
        "block": []
    }

    # Track indices for each marker type
    marker_indices: Dict[str, int] = {
        "chapter": 0,
        "section": 0,
        "subsection": 0,
        "page_break": 0,
        "page": 0,
        "double_line_break": 0,
        "block": 0
    }

    # Detect structural markers by scanning each line
    previous_blank = False
    blank_count = 0

    for line_num, line in enumerate(document.lines, start=1):
        # Calculate char_index (position of first non-whitespace char)
        stripped_line = line.lstrip()
        char_index = len(line) - len(stripped_line)

        # Check for double line breaks (2+ consecutive blank lines)
        if line.strip() == "":
            blank_count += 1
            if blank_count >= 2 and not previous_blank:
                marker_indices["double_line_break"] += 1
                markers["double_line_break"].append(
                    Marker(
                        marker_type="double_line_break",
                        index=marker_indices["double_line_break"],
                        line=line_num,
                        char_index=0
                    )
                )
                previous_blank = True
        else:
            blank_count = 0
            previous_blank = False

            # Check each marker type's patterns
            for marker_type in ["chapter", "section", "subsection", "page_break", "page"]:
                if marker_type not in config:
                    continue

                patterns = config[marker_type].get("patterns", [])
                for pattern in patterns:
                    if re.search(pattern, line):
                        marker_indices[marker_type] += 1
                        markers[marker_type].append(
                            Marker(
                                marker_type=marker_type,
                                index=marker_indices[marker_type],
                                line=line_num,
                                char_index=char_index
                            )
                        )
                        break  # Only match one pattern per line per marker type

    # Create block fallback chunks
    if "block" in config:
        block_size = config["block"].get("size", 800)
        _create_blocks(document, markers, marker_indices, block_size)

    # Create manifest
    manifest = Manifest(
        source=document.path,
        total_chars=document.total_chars,
        total_lines=document.total_lines,
        markers=markers
    )

    return manifest


def _create_blocks(document: Document, markers: Dict[str, List[Marker]],
                   marker_indices: Dict[str, int], block_size: int) -> None:
    """Create block fallback chunks in the document.

    Args:
        document: Document object
        markers: Dictionary to add block markers to
        marker_indices: Dictionary of marker indices
        block_size: Size of each block in characters
    """
    content = document.content
    offset = 0
    block_num = 0

    while offset < len(content):
        block_num += 1
        block_end = min(offset + block_size, len(content))

        # Find the line number where this block starts
        line_num = content[:offset].count('\n') + 1

        # Calculate char_index within that line
        last_newline = content.rfind('\n', 0, offset)
        if last_newline == -1:
            char_index = offset
        else:
            char_index = offset - (last_newline + 1)

        markers["block"].append(
            Marker(
                marker_type="block",
                index=block_num,
                line=line_num,
                char_index=char_index
            )
        )

        offset = block_end
