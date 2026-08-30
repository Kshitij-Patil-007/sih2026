"""
Feature Mapper
Detects ANY feature in satellite images (water, buildings, roads, forests, etc.)
based on user query, highlights them in a custom color, and counts regions.
"""

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


def detect_and_highlight(image: Image.Image, query: str, highlight_color=(220, 30, 30)):
    """
    Detect ANY feature based on user query using AI-guided segmentation,
    then highlight detected regions with a custom color.

    Examples:
        - "How many water bodies are there?"
        - "Highlight all buildings"
        - "Show me where the forests are"
        - "Count the ships in the port"

    Args:
        image: PIL Image (RGB)
        query: User's natural language query (e.g., "water bodies", "buildings")
        highlight_color: RGB tuple for highlighting (default red)

    Returns:
        dict with:
            - 'feature':        str, extracted feature name (e.g., "water bodies")
            - 'count':          int, number of distinct regions found
            - 'highlighted':    PIL Image with regions overlaid
            - 'mask':           np.ndarray (bool), True where feature detected
            - 'coverage_pct':   float, % of image covered
            - 'regions':        list of dicts with area/centroid per region
            - 'answer':         str, natural language summary
    """

    # Extract what feature the user is asking about
    feature = _extract_feature_from_query(query)

    # Get segmentation mask using AI or heuristics
    mask = _get_feature_mask(image, feature)

    # --- Morphological cleanup ---
    cleaned = ndimage.binary_fill_holes(mask)
    cleaned = ndimage.binary_opening(cleaned, structure=np.ones((3, 3)), iterations=2)
    cleaned = ndimage.binary_closing(cleaned, structure=np.ones((5, 5)), iterations=2)

    # Remove regions smaller than 200 pixels (noise)
    labeled, _ = ndimage.label(cleaned)
    if labeled.max() > 0:
        region_sizes = ndimage.sum(cleaned, labeled, range(1, labeled.max() + 1))
        small_regions = np.where(np.array(region_sizes) < 200)[0] + 1
        for idx in small_regions:
            cleaned[labeled == idx] = False

    # Re-label after cleanup
    labeled, count = ndimage.label(cleaned)

    # --- Per-region stats ---
    regions = []
    for i in range(1, count + 1):
        region_mask = labeled == i
        area_px = int(region_mask.sum())
        ys, xs = np.where(region_mask)
        if len(xs) > 0 and len(ys) > 0:
            centroid = (int(xs.mean()), int(ys.mean()))
            regions.append({
                'id': i,
                'area_pixels': area_px,
                'centroid_xy': centroid,
            })

    # Sort largest first
    regions.sort(key=lambda x: x['area_pixels'], reverse=True)

    coverage_pct = round(float(cleaned.sum()) / cleaned.size * 100, 2) if cleaned.size > 0 else 0.0

    # --- Build highlighted output image ---
    highlighted = _overlay_color(image, cleaned, regions, highlight_color)

    # --- Generate natural language answer ---
    answer = _generate_answer(feature, count, coverage_pct, regions)

    return {
        'feature': feature,
        'count': count,
        'highlighted': highlighted,
        'mask': cleaned,
        'coverage_pct': coverage_pct,
        'regions': regions,
        'answer': answer,
    }


def _extract_feature_from_query(query: str) -> str:
    """Extract what the user is asking about (water, buildings, etc.)"""
    query_lower = query.lower()

    feature_keywords = {
        'water': ['water', 'lake', 'river', 'pond', 'ocean', 'sea'],
        'buildings': ['building', 'structure', 'house', 'construction'],
        'roads': ['road', 'highway', 'street', 'path'],
        'vegetation': ['vegetation', 'forest', 'tree', 'green', 'plant'],
        'vehicles': ['vehicle', 'car', 'truck', 'ship', 'boat', 'aircraft', 'plane'],
        'agricultural': ['field', 'farm', 'crop', 'agriculture'],
    }

    for feature, keywords in feature_keywords.items():
        if any(kw in query_lower for kw in keywords):
            return feature

    return 'features'  # generic fallback


def _get_feature_mask(image: Image.Image, feature: str) -> np.ndarray:
    """
    Get binary mask for the requested feature using heuristics.

    In production, this would call a segmentation model (SAM, SegFormer, etc.)
    For now, we use color-based heuristics as a prototype.
    """
    img_rgb = image.convert('RGB')
    arr = np.array(img_rgb, dtype=np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    if feature == 'water':
        # Water detection (dark blue/teal/black in satellite imagery)
        blue_dominant = (b > r + 10) & (b > g + 5) & (b < 180)
        dark_teal = (b > r) & (g > r) & (r < 80) & (b < 160)
        very_dark = (r < 60) & (g < 80) & (b < 100)
        return blue_dominant | dark_teal | very_dark

    elif feature == 'buildings':
        # Buildings: gray/white rectangular structures
        gray = (np.abs(r - g) < 30) & (np.abs(g - b) < 30) & (r > 100)
        return gray

    elif feature == 'roads':
        # Roads: linear gray/black features
        gray_dark = (np.abs(r - g) < 20) & (np.abs(g - b) < 20) & (r < 120) & (r > 40)
        return gray_dark

    elif feature == 'vegetation':
        # Vegetation: green dominant
        green_dominant = (g > r + 15) & (g > b + 10)
        return green_dominant

    elif feature == 'vehicles':
        # Vehicles: small bright specks (white/colored)
        bright = (r > 150) | (g > 150) | (b > 150)
        return bright

    else:
        # Generic: detect high-contrast regions
        brightness = (r + g + b) / 3
        return brightness > 100


def _generate_answer(feature: str, count: int, coverage_pct: float, regions: list) -> str:
    """Generate natural language answer"""
    if count == 0:
        return f"No {feature} detected in this image."

    answer = f"Found **{count}** {feature} region"
    if count > 1:
        answer += "s"
    answer += f", covering **{coverage_pct}%** of the image."

    if regions and len(regions) > 0:
        largest = regions[0]['area_pixels']
        answer += f" The largest region covers **{largest:,}** pixels."

    return answer


def _overlay_color(image: Image.Image, mask: np.ndarray, regions: list, color=(220, 30, 30)) -> Image.Image:
    """
    Overlay detected feature pixels with a semi-transparent color tint,
    and draw numbered labels at each region's centroid.
    """
    base = image.convert('RGBA')

    # Paint feature pixels with chosen color (semi-transparent)
    color_layer = np.zeros((*mask.shape, 4), dtype=np.uint8)
    color_layer[mask] = [color[0], color[1], color[2], 160]  # R, G, B, Alpha
    color_pil = Image.fromarray(color_layer, 'RGBA')

    # Draw region outlines (brighter border)
    outline = _get_outline(mask)
    outline_layer = np.zeros((*mask.shape, 4), dtype=np.uint8)
    bright_color = tuple(min(c + 35, 255) for c in color)
    outline_layer[outline] = [bright_color[0], bright_color[1], bright_color[2], 230]
    outline_pil = Image.fromarray(outline_layer, 'RGBA')

    # Composite layers
    result = Image.alpha_composite(base, color_pil)
    result = Image.alpha_composite(result, outline_pil)

    # Draw labels at centroids
    draw = ImageDraw.Draw(result)
    for region in regions:
        cx, cy = region['centroid_xy']
        label = str(region['id'])
        # White circle background for readability
        r = 12
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 200))
        draw.text((cx - 5, cy - 8), label, fill=(180, 0, 0, 255))

    return result.convert('RGB')


def _get_outline(mask: np.ndarray) -> np.ndarray:
    """Extract 1-pixel outline of the mask using erosion."""
    eroded = ndimage.binary_erosion(mask, structure=np.ones((3, 3)))
    return mask & ~eroded


if __name__ == "__main__":
    print("Feature Mapper — import detect_and_highlight() to use.")
