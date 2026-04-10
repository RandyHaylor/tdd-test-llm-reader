from dataclasses import dataclass
from typing import Dict, List

VALID_MARKER_TYPES = {"chapter", "section", "subsection", "page_break", "page", "double_line_break", "block"}


@dataclass
class Marker:
    """Represents a structural marker in a document."""
    marker_type: str
    index: int
    line: int
    char_index: int  # Within-line position where content starts (after whitespace)

    def __post_init__(self):
        if self.marker_type not in VALID_MARKER_TYPES:
            raise ValueError(f"marker_type must be one of {VALID_MARKER_TYPES}, got {self.marker_type}")


@dataclass
class Manifest:
    """Represents a document manifest with structural markers."""
    source: str
    total_chars: int
    total_lines: int
    markers: Dict[str, List[Marker]]


@dataclass
class Document:
    """Represents a document with its path, content, and lines."""
    path: str
    content: str
    lines: List[str]

    @classmethod
    def from_file(cls, path: str) -> "Document":
        """Load a document from a file."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')
        return cls(path=path, content=content, lines=lines)

    @property
    def total_chars(self) -> int:
        """Return the total number of characters in the document."""
        return len(self.content)

    @property
    def total_lines(self) -> int:
        """Return the total number of lines in the document."""
        return len(self.lines)
