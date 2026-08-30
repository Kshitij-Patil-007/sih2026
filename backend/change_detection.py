"""
Change Detection Module
Compares two satellite images and highlights differences
"""

import numpy as np
from PIL import Image

# Try importing cv2, fallback to numpy if not available
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

def detect_changes(image_before, image_after, threshold=30):
    """
    Compare two images and detect changes.

    Args:
        image_before: PIL Image (before state)
        image_after: PIL Image (after state)
        threshold: Sensitivity (0-255, lower = more sensitive)

    Returns:
        dict with:
            - 'summary': Text description of changes
            - 'change_percentage': float (0-100)
            - 'diff_heatmap': PIL Image showing changes
            - 'changed_pixels': int
    """

    # Convert to numpy arrays
    arr_before = np.array(image_before.convert('RGB'))
    arr_after = np.array(image_after.convert('RGB'))

    # Ensure same size
    if arr_before.shape != arr_after.shape:
        # Resize to match
        h, w = arr_before.shape[:2]
        image_after = image_after.resize((w, h), Image.Resampling.LANCZOS)
        arr_after = np.array(image_after.convert('RGB'))

    # Calculate absolute difference
    diff = np.abs(arr_after.astype(float) - arr_before.astype(float))

    # Convert to grayscale difference magnitude
    diff_gray = np.mean(diff, axis=2)

    # Apply threshold
    change_mask = (diff_gray > threshold).astype(np.uint8) * 255

    # Calculate statistics
    changed_pixels = np.sum(change_mask > 0)
    total_pixels = change_mask.shape[0] * change_mask.shape[1]
    change_percentage = (changed_pixels / total_pixels) * 100

    # Generate heatmap
    heatmap = generate_diff_heatmap(arr_before, arr_after, change_mask)

    # Generate summary
    if change_percentage < 1:
        summary = f"Minimal changes detected ({change_percentage:.2f}% of image)"
    elif change_percentage < 5:
        summary = f"Small localized changes detected ({change_percentage:.2f}% of image)"
    elif change_percentage < 15:
        summary = f"Moderate changes detected ({change_percentage:.2f}% of image)"
    else:
        summary = f"Significant changes detected ({change_percentage:.2f}% of image)"

    return {
        'summary': summary,
        'change_percentage': round(change_percentage, 2),
        'diff_heatmap': heatmap,
        'changed_pixels': int(changed_pixels),
        'total_pixels': int(total_pixels)
    }


def generate_diff_heatmap(arr_before, arr_after, change_mask):
    """
    Create a visual heatmap overlay showing changes.

    Args:
        arr_before: numpy array (before image)
        arr_after: numpy array (after image)
        change_mask: binary mask of changed pixels

    Returns:
        PIL Image with heatmap overlay
    """

    # Create base image (after state)
    result = arr_after.copy()

    # Create red overlay for changes
    overlay = np.zeros_like(result)
    overlay[:, :, 0] = change_mask  # Red channel

    # Blend overlay with original image
    alpha = 0.4  # Transparency
    if HAS_CV2:
        result = cv2.addWeighted(result, 1, overlay, alpha, 0)
    else:
        # Pure numpy fallback
        result = (result * 1.0 + overlay * alpha).clip(0, 255).astype('uint8')

    # Convert back to PIL
    heatmap_image = Image.fromarray(result.astype('uint8'), 'RGB')

    return heatmap_image


def calculate_ndvi(image, nir_band_idx=3, red_band_idx=0):
    """
    Calculate NDVI (Normalized Difference Vegetation Index) if multispectral data available.
    NDVI = (NIR - Red) / (NIR + Red)

    Args:
        image: numpy array with multiple bands
        nir_band_idx: Index of Near-Infrared band
        red_band_idx: Index of Red band

    Returns:
        NDVI array (values from -1 to 1)
    """

    if image.ndim < 3 or image.shape[0] < max(nir_band_idx, red_band_idx) + 1:
        raise ValueError("Image doesn't have enough bands for NDVI calculation")

    nir = image[nir_band_idx].astype(float)
    red = image[red_band_idx].astype(float)

    # Calculate NDVI
    ndvi = np.zeros_like(nir)
    valid_mask = (nir + red) != 0
    ndvi[valid_mask] = (nir[valid_mask] - red[valid_mask]) / (nir[valid_mask] + red[valid_mask])

    return ndvi


def compare_ndvi(image_before, image_after):
    """
    Compare vegetation health between two multispectral images using NDVI.
    """

    try:
        ndvi_before = calculate_ndvi(image_before)
        ndvi_after = calculate_ndvi(image_after)

        # Calculate vegetation loss/gain
        ndvi_change = ndvi_after - ndvi_before

        avg_change = np.mean(ndvi_change)

        if avg_change > 0.05:
            summary = f"Vegetation increase detected (avg NDVI change: +{avg_change:.3f})"
        elif avg_change < -0.05:
            summary = f"Vegetation loss detected (avg NDVI change: {avg_change:.3f})"
        else:
            summary = f"Minimal vegetation change (avg NDVI change: {avg_change:.3f})"

        return {
            'summary': summary,
            'ndvi_change': float(avg_change),
            'ndvi_before_avg': float(np.mean(ndvi_before)),
            'ndvi_after_avg': float(np.mean(ndvi_after))
        }
    except Exception as e:
        return {'error': f"NDVI calculation failed: {e}"}


# Test function
if __name__ == "__main__":
    print("Change Detection Module")
    print("To test: detect_changes(image_before, image_after)")
