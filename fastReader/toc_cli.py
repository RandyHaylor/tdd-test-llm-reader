from typing import List, Dict, Any, Optional
from fastReader.models import Manifest, Marker
from fastReader.preview import extract_preview

def build_toc(
    manifest: Manifest, 
    content_lines: List[str], 
    marker_types: List[str] = None, 
    preview_length: int = 30,
    limit: Optional[int] = 15
) -> List[Dict[str, Any]]:
    """Build a Table of Contents list of dicts.
    
    Args:
        manifest: The document manifest
        content_lines: List of document lines
        marker_types: List of marker types to include (default: ['section'])
        preview_length: Length of preview to extract
        limit: Maximum number of entries to return (default: 15)
        
    Returns:
        List of TOC entry dictionaries
    """
    if marker_types is None:
        marker_types = ['section']
        
    all_selected_markers: List[Marker] = []
    
    for m_type in marker_types:
        if m_type in manifest.markers:
            all_selected_markers.extend(manifest.markers[m_type])
            
    # Sort by line number (interleaving)
    all_selected_markers.sort(key=lambda m: m.line)
    
    # Apply limit
    if limit is not None:
        all_selected_markers = all_selected_markers[:limit]
        
    toc: List[Dict[str, Any]] = []
    for marker in all_selected_markers:
        preview = extract_preview(
            content_lines, 
            marker.line, 
            marker.char_index, 
            preview_length
        )
        
        toc.append({
            "type": marker.marker_type,
            "index": marker.index,
            "line_number": marker.line,
            "preview": preview
        })
        
    return toc
