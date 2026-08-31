"""
Feature Mapper - Advanced Remote Sensing & Computer Vision Engine
Detects features in satellite/aerial imagery (roads, water, buildings, vegetation, vehicles)
using spectral indices (NDWI, NDVI), Line Segment Detection (LSD), and multi-scale texture filtering.
"""

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import cv2


def detect_and_highlight(image: Image.Image, query: str, highlight_color=None):
    """
    Detect features in satellite images using remote sensing computer vision algorithms.

    Supported queries:
        - "Highlight roads / streets / highways"
        - "Show water bodies / rivers / lakes"
        - "Find buildings / structures / built-up areas"
        - "Detect vegetation / forests / parks / crops"
        - "Count vehicles / ships"

    Args:
        image: PIL Image (RGB)
        query: User's natural language query
        highlight_color: Optional RGB tuple (defaults to domain-matched color)

    Returns:
        dict with:
            - 'feature':        str, extracted feature category
            - 'count':          int, number of distinct regions found
            - 'highlighted':    PIL Image with regions overlaid & labeled
            - 'mask':           np.ndarray (bool), True where feature detected
            - 'coverage_pct':   float, % of image covered
            - 'regions':        list of dicts with area/centroid per region
            - 'answer':         str, natural language summary
    """

    # 1. Extract target feature category
    feature = _extract_feature_from_query(query)

    # 2. Pick default color if not specified (Roads: Red, Water: Blue, Veg: Green, Bld: Orange)
    if highlight_color is None:
        color_palette = {
            'roads': (230, 40, 40),        # Vivid Red
            'water': (30, 120, 255),       # Vivid Blue
            'vegetation': (40, 200, 60),   # Green
            'buildings': (255, 140, 0),    # Orange/Amber
            'vehicles': (255, 220, 0),     # Yellow
        }
        highlight_color = color_palette.get(feature, (220, 40, 40))

    # 3. Compute accurate binary segmentation mask
    mask = _get_feature_mask(image, feature)

    # 4. Clean up mask morphology
    cleaned = _cleanup_mask(mask, feature)

    # 5. Label distinct connected regions & extract stats
    labeled, count = ndimage.label(cleaned)
    regions = _extract_regions(labeled, count, feature)
    actual_count = len(regions)

    coverage_pct = round(float(cleaned.sum()) / cleaned.size * 100, 2) if cleaned.size > 0 else 0.0

    # 6. Composite visual overlay with translucent mask and boundary contours
    highlighted = _overlay_color(image, cleaned, regions, highlight_color)

    # 7. Generate structured summary
    answer = _generate_answer(feature, actual_count, coverage_pct, regions)

    return {
        'feature': feature,
        'count': actual_count,
        'highlighted': highlighted,
        'mask': cleaned,
        'coverage_pct': coverage_pct,
        'regions': regions,
        'answer': answer,
    }


def _extract_feature_from_query(query: str) -> str:
    """Classify natural language query to target feature category"""
    q = query.lower()

    feature_keywords = {
        'roads': ['road', 'highway', 'street', 'path', 'expressway', 'bridge', 'runway', 'freeway'],
        'water': ['water', 'river', 'lake', 'pond', 'ocean', 'sea', 'canal', 'stream', 'reservoir'],
        'vegetation': ['vegetation', 'forest', 'tree', 'green', 'park', 'grass', 'field', 'crop', 'agriculture', 'farm'],
        'buildings': ['building', 'structure', 'house', 'construction', 'urban', 'rooftop', 'built-up', 'settlement'],
        'vehicles': ['vehicle', 'car', 'truck', 'ship', 'boat', 'vessel', 'aircraft', 'plane'],
    }

    for feature, keywords in feature_keywords.items():
        if any(kw in q for kw in keywords):
            return feature

    return 'roads'  # fallback


def _get_feature_mask(image: Image.Image, feature: str) -> np.ndarray:
    """Extract binary segmentation mask using remote sensing algorithms"""
    img_rgb = image.convert('RGB')
    np_img = np.array(img_rgb)
    bgr = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    r, g, b = np_img[:, :, 0].astype(np.float32), np_img[:, :, 1].astype(np.float32), np_img[:, :, 2].astype(np.float32)

    # Local texture standard deviation
    ksize = 15
    mean = cv2.blur(gray.astype(np.float32), (ksize, ksize))
    sqr_mean = cv2.blur(gray.astype(np.float32)**2, (ksize, ksize))
    std = np.sqrt(np.maximum(sqr_mean - mean**2, 0))

    if feature == 'roads':
        return _detect_roads(gray, h, s, v)

    elif feature == 'water':
        return _detect_water(gray, b, g, r, std)

    elif feature == 'vegetation':
        return _detect_vegetation(h, s, v, r, g, b)

    elif feature == 'buildings':
        roads_mask = _detect_roads(gray, h, s, v)
        water_mask = _detect_water(gray, b, g, r, std)
        veg_mask = _detect_vegetation(h, s, v, r, g, b)
        return _detect_buildings(gray, std, v, roads_mask, water_mask, veg_mask)

    elif feature == 'vehicles':
        return _detect_vehicles(gray, s, v, std)

    return np.zeros_like(gray, dtype=bool)


def _detect_roads(gray: np.ndarray, h: np.ndarray, s: np.ndarray, v: np.ndarray) -> np.ndarray:
    """
    Road and expressway detection using:
    1. Line Segment Detector (LSD) on linear street grid corridors
    2. Color segmentation for yellow/orange expressways & interchanges
    """
    # (a) Yellow/Orange expressways & highway bridges
    yellow_roads = (h >= 12) & (h <= 42) & (s >= 55) & (v >= 90)

    # (b) Linear street networks via Line Segment Detection
    lsd = cv2.createLineSegmentDetector(0)
    lines, width, prec, nfa = lsd.detect(gray)
    line_mask = np.zeros_like(gray, dtype=np.uint8)

    if lines is not None:
        for line in lines:
            pts = line.flatten()
            x1, y1, x2, y2 = pts[0], pts[1], pts[2], pts[3]
            length = np.hypot(x2 - x1, y2 - y1)
            if length > 30:  # long continuous roads/corridors
                cv2.line(line_mask, (int(x1), int(y1)), (int(x2), int(y2)), 255, 3)

    # Filter linear streets with appropriate luminance and low color saturation
    street_lines = (line_mask > 0) & (s < 60) & (v > 100)

    return yellow_roads | street_lines


def _detect_water(gray: np.ndarray, b: np.ndarray, g: np.ndarray, r: np.ndarray, std: np.ndarray) -> np.ndarray:
    """
    Water body detection using:
    1. NDWI spectral response proxy (Green & Blue >= Red)
    2. Low-variance surface smoothness filtering
    3. Contiguous morphological basin extraction
    """
    # Water spectrum: smooth, moderate brightness, B & G >= R
    water_spectrum = (b >= r - 2) & (g >= r - 2)
    water_pixels = (std < 20) & water_spectrum & (gray > 35) & (gray < 185)

    # Morphological closing to bridge small text labels and boats
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
    water_closed = cv2.morphologyEx(water_pixels.astype(np.uint8) * 255, cv2.MORPH_CLOSE, kernel)

    # Keep significant water bodies (> 4000 pixels)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(water_closed)
    water_mask = np.zeros_like(gray, dtype=bool)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] > 4000:
            water_mask |= (labels == i)

    return water_mask


def _detect_vegetation(h: np.ndarray, s: np.ndarray, v: np.ndarray, r: np.ndarray, g: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Vegetation / Park detection using:
    1. NDVI spectral proxy: Green reflectance dominance
    2. HSV green hue range (Hue 35-85) with moderate-to-high saturation
    """
    # Green dominance in RGB
    green_rgb = (g > r + 8) & (g > b) & (s > 35)
    # Green hue in HSV
    green_hsv = (h >= 35) & (h <= 85) & (s >= 40) & (v >= 35)

    return green_rgb | green_hsv


def _detect_buildings(gray: np.ndarray, std: np.ndarray, v: np.ndarray,
                      roads: np.ndarray, water: np.ndarray, veg: np.ndarray) -> np.ndarray:
    """
    Built-up / building blocks detection:
    High local texture variation + rooftop structures excluding water, vegetation, and roads.
    """
    # Buildings have high local texture variance
    building_candidates = (std > 28) & (~water) & (~roads) & (~veg) & (v > 45)

    # Morphological opening to consolidate building blocks
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    cleaned = cv2.morphologyEx(building_candidates.astype(np.uint8) * 255, cv2.MORPH_OPEN, kernel)

    return cleaned > 0


def _detect_vehicles(gray: np.ndarray, s: np.ndarray, v: np.ndarray, std: np.ndarray) -> np.ndarray:
    """
    Vehicle & vessel detection:
    High contrast isolated point targets (10 - 500 pixels).
    """
    bright_spots = (v > 200) | ((gray > 180) & (s < 40))
    labeled, count = ndimage.label(bright_spots)

    vehicle_mask = np.zeros_like(gray, dtype=bool)
    if count > 0:
        sizes = ndimage.sum(bright_spots, labeled, range(1, count + 1))
        for idx, sz in enumerate(sizes, start=1):
            if 10 <= sz <= 600:  # Vehicle / ship sized
                vehicle_mask |= (labeled == idx)

    return vehicle_mask


def _cleanup_mask(mask: np.ndarray, feature: str) -> np.ndarray:
    """Apply feature-specific morphological cleanup"""
    if feature == 'roads':
        # Keep linear structures intact with minimal dilation
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(mask.astype(np.uint8) * 255, cv2.MORPH_CLOSE, kernel)
        return cleaned > 0

    elif feature == 'water':
        return mask

    elif feature == 'vegetation':
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned = cv2.morphologyEx(mask.astype(np.uint8) * 255, cv2.MORPH_CLOSE, kernel)
        return cleaned > 0

    elif feature == 'buildings':
        return mask

    elif feature == 'vehicles':
        return mask

    return mask


def _extract_regions(labeled: np.ndarray, count: int, feature: str, min_area=30) -> list:
    """Extract per-region stats with area and centroid coordinates"""
    regions = []
    if count == 0:
        return regions

    for i in range(1, count + 1):
        region_mask = labeled == i
        area_px = int(region_mask.sum())
        if area_px >= min_area:
            ys, xs = np.where(region_mask)
            if len(xs) > 0 and len(ys) > 0:
                centroid = (int(xs.mean()), int(ys.mean()))
                regions.append({
                    'id': len(regions) + 1,
                    'area_pixels': area_px,
                    'centroid_xy': centroid,
                })

    # Sort largest first
    regions.sort(key=lambda x: x['area_pixels'], reverse=True)
    # Re-assign IDs in sorted order
    for idx, reg in enumerate(regions, start=1):
        reg['id'] = idx

    return regions


def _generate_answer(feature: str, count: int, coverage_pct: float, regions: list) -> str:
    """Generate structured natural language summary"""
    if count == 0:
        return f"No distinct {feature} regions detected in this satellite imagery."

    answer = f"Detected **{count}** {feature} segment{'s' if count > 1 else ''}, covering **{coverage_pct}%** of the image area."

    if regions:
        largest = regions[0]['area_pixels']
        answer += f" The primary identified segment covers **{largest:,}** pixels."

    return answer


def _overlay_color(image: Image.Image, mask: np.ndarray, regions: list, color=(230, 40, 40)) -> Image.Image:
    """
    Composite semi-transparent colored highlight overlay and region contours.
    """
    base = image.convert('RGBA')

    # 1. Fill mask with semi-transparent color
    color_layer = np.zeros((*mask.shape, 4), dtype=np.uint8)
    color_layer[mask] = [color[0], color[1], color[2], 135]  # Semi-transparent
    color_pil = Image.fromarray(color_layer, 'RGBA')

    # 2. Extract contour boundary outline
    outline = _get_outline(mask)
    outline_layer = np.zeros((*mask.shape, 4), dtype=np.uint8)
    bright_color = tuple(min(c + 40, 255) for c in color)
    outline_layer[outline] = [bright_color[0], bright_color[1], bright_color[2], 240]
    outline_pil = Image.fromarray(outline_layer, 'RGBA')

    # Composite layers
    result = Image.alpha_composite(base, color_pil)
    result = Image.alpha_composite(result, outline_pil)

    # 3. Draw numbered labels for the top 15 largest regions
    draw = ImageDraw.Draw(result)
    for region in regions[:15]:
        cx, cy = region['centroid_xy']
        label = str(region['id'])
        r = 11
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 210), outline=(0, 0, 0, 180))
        draw.text((cx - 4, cy - 6), label, fill=(color[0], color[1], color[2], 255))

    return result.convert('RGB')


def _get_outline(mask: np.ndarray) -> np.ndarray:
    """Extract 1-pixel boundary contour of the mask"""
    eroded = ndimage.binary_erosion(mask, structure=np.ones((3, 3)))
    return mask & ~eroded


if __name__ == "__main__":
    print("Feature Mapper initialized successfully.")
