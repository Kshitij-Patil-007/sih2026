from __future__ import annotations

import numpy as np
from PIL import Image, ImageEnhance

from backend.aryan_preprocess import PreparedImage


def fuse(optical: PreparedImage, sar: PreparedImage) -> dict:
    target = optical.rgb.size
    sar_rgb = sar.rgb.resize(target, Image.Resampling.BILINEAR).convert("L")
    sar_arr = np.asarray(sar_rgb, dtype=np.float32)
    opt = optical.array
    # Dual-encoder stand-in: optical color stream + SAR edge/backscatter stream.
    gx = np.abs(np.diff(sar_arr, axis=1, prepend=sar_arr[:, :1]))
    gy = np.abs(np.diff(sar_arr, axis=0, prepend=sar_arr[:1, :]))
    edges = np.clip(gx + gy, 0, 255)
    fused = opt.copy()
    fused[:, :, 0] = np.clip(0.75 * opt[:, :, 0] + 0.35 * sar_arr, 0, 255)
    fused[:, :, 1] = np.clip(0.85 * opt[:, :, 1] + 0.10 * (255 - edges), 0, 255)
    fused[:, :, 2] = np.clip(0.70 * opt[:, :, 2] + 0.40 * edges, 0, 255)
    vis = Image.fromarray(fused.astype(np.uint8), mode="RGB")
    vis = ImageEnhance.Contrast(vis).enhance(1.12)

    sar_mean = float(sar_arr.mean())
    if sar_mean < 55:
        land = "dark backscatter (smooth water or radar shadow)"
        conf = 0.7
    elif float(edges.mean()) > 28:
        land = "bright structured returns typical of built-up / ships"
        conf = 0.76
    else:
        land = "moderate volume scattering (vegetation / agriculture)"
        conf = 0.68

    answer = (
        f"Optical–SAR fusion (dual-encoder stand-in) overlays Sentinel-1-style backscatter "
        f"on the RGB composite. SAR stream reads as {land}."
    )
    return {
        "answer": answer,
        "confidence": conf,
        "overlay": vis,
        "notes": [
            "Optical RGB encoder kept color; SAR encoder contributed edges + backscatter.",
            "Gemini was not used — SAR geometry is out of distribution for that API.",
        ],
    }
