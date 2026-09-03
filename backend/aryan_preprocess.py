from __future__ import annotations

import io
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageOps


@dataclass
class PreparedImage:
    name: str
    modality: str
    rgb: Image.Image
    array: np.ndarray
    notes: list[str]


def _detect_modality(name: str, image: Image.Image) -> tuple[str, list[str]]:
    notes: list[str] = []
    lowered = name.lower()
    if any(token in lowered for token in ("sar", "s1", "sentinel-1", "sentinel1")):
        notes.append("Filename tagged as SAR (Sentinel-1 style).")
        return "sar", notes
    if any(token in lowered for token in ("optical", "s2", "sentinel-2", "rgb", "planet")):
        notes.append("Filename tagged as optical RGB.")
        return "optical", notes
    if image.mode in ("L", "I", "F") or (image.mode == "RGB" and _is_near_grayscale(image)):
        notes.append("Single-band / near-grayscale pixels → treated as SAR.")
        return "sar", notes
    notes.append("Three-channel color → treated as optical RGB.")
    return "optical", notes


def _is_near_grayscale(image: Image.Image) -> bool:
    arr = np.asarray(image.convert("RGB"), dtype=np.float32)
    diffs = np.abs(arr[:, :, 0] - arr[:, :, 1]) + np.abs(arr[:, :, 1] - arr[:, :, 2])
    return float(diffs.mean()) < 6.0


def _composite_multiband(image: Image.Image, notes: list[str]) -> Image.Image:
    """GeoTIFF / multi-band rasters must be RGB-composited before any VLM call."""
    bands = image.getbands()
    if image.mode in ("RGBA", "RGB"):
        rgb = image.convert("RGB")
        notes.append("Converted to 8-bit RGB composite (3-band visualization).")
        return rgb
    if image.mode == "L":
        rgb = ImageOps.autocontrast(image).convert("RGB")
        notes.append("Single-band stretched and mapped to RGB for display / APIs.")
        return rgb
    if len(bands) > 3:
        notes.append(f"Multi-band source ({len(bands)} bands) → bands 1-3 RGB composite.")
        return image.convert("RGB")
    notes.append(f"Mode {image.mode} coerced to RGB composite.")
    return image.convert("RGB")


def prepare_image(filename: str, data: bytes) -> PreparedImage:
    image = Image.open(io.BytesIO(data))
    notes: list[str] = [f"Loaded {filename} ({image.mode}, {image.size[0]}×{image.size[1]})."]
    rgb = _composite_multiband(image, notes)
    rgb = ImageOps.exif_transpose(rgb)
    # Keep inference snappy while preserving enough spatial structure for change maps.
    rgb.thumbnail((768, 768), Image.Resampling.LANCZOS)
    modality, extra = _detect_modality(filename, rgb)
    notes.extend(extra)
    arr = np.asarray(rgb, dtype=np.float32)
    return PreparedImage(name=filename, modality=modality, rgb=rgb, array=arr, notes=notes)


def prepare_image_from_path(filepath: str, modality: str | None = None) -> PreparedImage:
    from pathlib import Path
    p = Path(filepath)
    filename = p.name
    with open(filepath, "rb") as f:
        data = f.read()
    prep = prepare_image(filename, data)
    if modality and modality in ("optical", "sar"):
        prep.modality = modality
    return prep


def encode_png(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def to_data_url(image: Image.Image) -> str:
    import base64

    return "data:image/png;base64," + base64.b64encode(encode_png(image)).decode("ascii")
