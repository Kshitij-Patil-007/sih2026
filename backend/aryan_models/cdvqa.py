from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from backend.aryan_preprocess import PreparedImage


def _coregister(before: PreparedImage, after: PreparedImage) -> tuple[np.ndarray, np.ndarray, Image.Image, Image.Image]:
    """Resize the after image onto the before grid — a hackathon stand-in for true co-registration."""
    target = before.rgb.size
    after_rgb = after.rgb.resize(target, Image.Resampling.BILINEAR)
    return before.array, np.asarray(after_rgb, dtype=np.float32), before.rgb, after_rgb


def _change_map(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    diff = np.abs(a - b).mean(axis=2)
    # Robust threshold: mean + 1.1 * std, with a floor so quiet scenes still show structure.
    thr = max(18.0, float(diff.mean() + 1.1 * diff.std()))
    mask = (diff >= thr).astype(np.uint8)
    ratio = float(mask.mean())
    return diff, mask, ratio


def _siamese_patch_scores(a: np.ndarray, b: np.ndarray, patches: int = 8) -> np.ndarray:
    """Stretch-goal Siamese head: cosine distance between patch histograms (no GPU)."""
    h, w, _ = a.shape
    ph, pw = h // patches, w // patches
    heat = np.zeros((patches, patches), dtype=np.float32)
    for i in range(patches):
        for j in range(patches):
            pa = a[i * ph : (i + 1) * ph, j * pw : (j + 1) * pw].reshape(-1, 3)
            pb = b[i * ph : (i + 1) * ph, j * pw : (j + 1) * pw].reshape(-1, 3)
            ha, _ = np.histogramdd(pa, bins=(6, 6, 6), range=((0, 255),) * 3)
            hb, _ = np.histogramdd(pb, bins=(6, 6, 6), range=((0, 255),) * 3)
            va, vb = ha.ravel() + 1e-6, hb.ravel() + 1e-6
            va /= np.linalg.norm(va)
            vb /= np.linalg.norm(vb)
            heat[i, j] = 1.0 - float(np.dot(va, vb))
    return heat


def render_overlay(after_rgb: Image.Image, diff: np.ndarray, mask: np.ndarray) -> Image.Image:
    base = after_rgb.convert("RGBA")
    heat = diff / max(1.0, float(diff.max()))
    overlay = np.zeros((*mask.shape, 4), dtype=np.uint8)
    overlay[..., 0] = np.clip(80 + heat * 175, 0, 255).astype(np.uint8)
    overlay[..., 1] = np.clip(40 + (1 - heat) * 30, 0, 255).astype(np.uint8)
    overlay[..., 2] = 20
    overlay[..., 3] = (mask * 150).astype(np.uint8)
    layer = Image.fromarray(overlay, mode="RGBA").filter(ImageFilter.GaussianBlur(radius=1.2))
    composed = Image.alpha_composite(base, layer)
    return composed.convert("RGB")


def _describe_change(a: np.ndarray, b: np.ndarray, mask: np.ndarray, ratio: float, question: str) -> tuple[str, float]:
    q = question.lower()
    delta = b - a
    changed = mask.astype(bool)
    if changed.any():
        d_r = float(delta[:, :, 0][changed].mean())
        d_g = float(delta[:, :, 1][changed].mean())
        d_b = float(delta[:, :, 2][changed].mean())
        d_bright = float((delta.mean(axis=2))[changed].mean())
    else:
        d_r = d_g = d_b = d_bright = 0.0

    blue_shift = float(b[:, :, 2].mean() - a[:, :, 2].mean())
    cues: list[str] = []
    if d_b > 8 and d_b >= d_g - 2:
        cues.append("increased blue / moisture (possible inundation)")
    elif blue_shift > 6:
        cues.append("scene-wide blue-channel rise (possible inundation)")
    if d_g < -10 and d_r > 5:
        cues.append("loss of vegetation (browning or clearing)")
    if d_g > 12:
        cues.append("greening / vegetation gain")
    if abs(d_bright) > 18 and abs(d_r - d_g) < 8:
        cues.append("albedo shift consistent with new roof / bare soil / debris")
    if not cues:
        cues.append("localized radiometric change without a single dominant spectral signature")

    pct = ratio * 100
    if pct < 2:
        magnitude = "Minimal"
        conf = 0.62
    elif pct < 8:
        magnitude = "Moderate, localized"
        conf = 0.74
    elif pct < 20:
        magnitude = "Substantial"
        conf = 0.82
    else:
        magnitude = "Widespread"
        conf = 0.88

    focus = ""
    if any(w in q for w in ("flood", "water", "inundat")):
        wet = d_b > 6 or blue_shift > 5
        focus = (
            " Flood/water read: blue-channel rise suggests inundation over the town/floodplain."
            if wet
            else " Flood/water read: little extra water signal in the change mask."
        )
        conf = min(0.92, conf + (0.08 if wet else -0.04))
    elif any(w in q for w in ("building", "urban", "damage", "destroy", "collapse")):
        focus = " Built-up read: high-frequency brightness change is consistent with structure / debris." if abs(d_bright) > 10 else " Built-up read: structural change is weak relative to background."
    elif any(w in q for w in ("deforest", "forest", "tree", "vegetat", "crop")):
        focus = " Vegetation read: green-channel drop in changed pixels." if d_g < -8 else " Vegetation read: no strong canopy loss signature."

    text = (
        f"{magnitude} change over {pct:.1f}% of the co-registered frame. "
        f"Primary cues: {'; '.join(cues)}.{focus}"
    )
    return text, float(max(0.5, min(0.94, conf)))


def run_cdvqa(before: PreparedImage, after: PreparedImage, question: str) -> dict:
    a, b, before_rgb, after_rgb = _coregister(before, after)
    diff, mask, ratio = _change_map(a, b)
    siamese = _siamese_patch_scores(a, b)
    overlay = render_overlay(after_rgb, diff, mask)

    # Draw a few bounding boxes around the hottest connected-ish tiles.
    boxes = _box_from_siamese(siamese, after_rgb.size)
    boxed = overlay.copy()
    draw = ImageDraw.Draw(boxed)
    for x0, y0, x1, y1 in boxes[:4]:
        draw.rectangle([x0, y0, x1, y1], outline=(250, 210, 80), width=3)

    answer, confidence = _describe_change(a, b, mask, ratio, question)
    return {
        "answer": answer,
        "confidence": confidence,
        "change_ratio": ratio,
        "siamese_peak": float(siamese.max()) if siamese.size else 0.0,
        "overlay": boxed,
        "after_aligned": after_rgb,
        "before_aligned": before_rgb,
        "boxes": boxes,
        "notes": [
            "After image resampled onto the before grid (affine co-registration stand-in).",
            f"Change pixels at {ratio:.1%} of the frame (robust threshold).",
            f"Siamese patch-histogram peak distance {float(siamese.max()):.3f} (stretch-goal head, CPU).",
        ],
    }


def _box_from_siamese(heat: np.ndarray, size: tuple[int, int]) -> list[tuple[int, int, int, int]]:
    patches = heat.shape[0]
    w, h = size
    pw, ph = w / patches, h / patches
    coords = [(i, j, heat[i, j]) for i in range(patches) for j in range(patches)]
    coords.sort(key=lambda t: t[2], reverse=True)
    boxes = []
    peak = coords[0][2] if coords else 0
    for i, j, score in coords:
        if score < max(0.08, peak * 0.55):
            continue
        x0, y0 = int(j * pw), int(i * ph)
        x1, y1 = int(min(w - 1, (j + 1) * pw)), int(min(h - 1, (i + 1) * ph))
        boxes.append((x0, y0, x1, y1))
        if len(boxes) >= 4:
            break
    return boxes
