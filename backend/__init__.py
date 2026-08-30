"""
SatQuery AI Backend
Handles GeoTIFF processing, vision AI, and query routing
"""

from .geo_loader import load_geotiff, get_image_metadata
from .vlm_engine import ask_vision_model, process_query
from .change_detection import detect_changes, generate_diff_heatmap
from .feature_mapper import detect_and_highlight

__all__ = [
    'load_geotiff',
    'get_image_metadata',
    'ask_vision_model',
    'process_query',
    'detect_changes',
    'generate_diff_heatmap',
    'detect_and_highlight'
]
