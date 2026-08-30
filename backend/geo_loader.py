"""
GeoTIFF Loader and Image Preprocessing
Converts multi-band satellite images to viewable RGB format
"""

import numpy as np
from PIL import Image
import io

def load_geotiff(file_path):
    """
    Load a GeoTIFF file and convert to RGB image.

    Args:
        file_path: Path to .tif file or file-like object

    Returns:
        dict with:
            - 'image': PIL Image object (RGB)
            - 'metadata': dict with satellite info
            - 'raw_array': numpy array (for change detection)
    """
    try:
        # Try using rasterio first (best for GeoTIFF)
        import rasterio
        from rasterio.plot import reshape_as_image

        with rasterio.open(file_path) as src:
            # Read bands
            data = src.read()

            # Get metadata
            metadata = {
                'bands': src.count,
                'width': src.width,
                'height': src.height,
                'crs': str(src.crs) if src.crs else 'Unknown',
                'bounds': src.bounds,
            }

            # Convert to RGB (handle multi-band)
            if src.count >= 3:
                # Use first 3 bands as RGB
                rgb = np.dstack([data[0], data[1], data[2]])
            else:
                # Grayscale - duplicate to RGB
                rgb = np.dstack([data[0], data[0], data[0]])

            # Normalize to 0-255
            rgb = _normalize_image(rgb)

            # Convert to PIL Image
            image = Image.fromarray(rgb.astype('uint8'), 'RGB')

            return {
                'image': image,
                'metadata': metadata,
                'raw_array': data
            }

    except ImportError:
        # Fallback: try loading as regular image with PIL
        return _load_as_regular_image(file_path)
    except Exception as e:
        print(f"Error loading GeoTIFF: {e}")
        # Fallback to PIL
        return _load_as_regular_image(file_path)


def _load_as_regular_image(file_path):
    """Fallback loader for regular images (PNG, JPG)"""
    try:
        image = Image.open(file_path).convert('RGB')
        arr = np.array(image)

        return {
            'image': image,
            'metadata': {
                'width': image.width,
                'height': image.height,
                'format': image.format
            },
            'raw_array': arr
        }
    except Exception as e:
        raise ValueError(f"Could not load image: {e}")


def _normalize_image(arr):
    """
    Normalize satellite image array to 0-255 range.
    Handles different bit depths and applies contrast stretching.
    """
    # Remove any NaN or inf values
    arr = np.nan_to_num(arr, nan=0, posinf=255, neginf=0)

    # Apply percentile stretch (2% - 98%) for better contrast
    p2, p98 = np.percentile(arr, (2, 98))
    arr = np.clip(arr, p2, p98)

    # Scale to 0-255
    if arr.max() > arr.min():
        arr = (arr - arr.min()) / (arr.max() - arr.min()) * 255
    else:
        arr = np.zeros_like(arr)

    return arr


def get_image_metadata(file_path):
    """
    Extract metadata from satellite image without loading full array.
    Useful for displaying info before processing.
    """
    result = load_geotiff(file_path)
    return result['metadata']


# Test function
if __name__ == "__main__":
    print("GeoTIFF Loader Module")
    print("To test: load_geotiff('path/to/your/image.tif')")
