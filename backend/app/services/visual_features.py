import re
from typing import Any

import numpy as np
from PIL import Image

_COLOR_ALIASES: dict[str, str] = {
    "red": "red",
    "crimson": "red",
    "burgundy": "red",
    "maroon": "red",
    "scarlet": "red",
    "blue": "blue",
    "navy": "blue",
    "azure": "blue",
    "cobalt": "blue",
    "green": "green",
    "emerald": "green",
    "olive": "green",
    "yellow": "yellow",
    "gold": "yellow",
    "golden": "yellow",
    "orange": "orange",
    "amber": "orange",
    "purple": "purple",
    "violet": "purple",
    "lavender": "purple",
    "pink": "pink",
    "rose": "pink",
    "brown": "brown",
    "tan": "brown",
    "beige": "brown",
    "black": "black",
    "white": "white",
    "gray": "gray",
    "grey": "gray",
}

_COLOR_WORD_PATTERN = re.compile(
    r"\b(" + "|".join(sorted(_COLOR_ALIASES.keys(), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
_COLORFUL_PATTERN = re.compile(
    r"\b(?:colorful|colourful|vibrant|vivid|multicolor|bright\s+colors?|brightly\s+colored)\b",
    re.IGNORECASE,
)
_MUTED_PATTERN = re.compile(
    r"\b(?:muted|pastel|soft\s+colors?|gentle\s+colors?|soft\s+light)\b",
    re.IGNORECASE,
)
_DARK_PATTERN = re.compile(r"\b(?:dark|night|midnight)\b", re.IGNORECASE)
_BRIGHT_PATTERN = re.compile(r"\b(?:bright|sunny|daylight)\b", re.IGNORECASE)
_LIGHT_TONE_PATTERN = re.compile(
    r"\b(?:light\s+colors?|light\s+toned|light\s+background)\b",
    re.IGNORECASE,
)


def extract_visual_features(image_path: str) -> dict[str, Any]:
    """Compute compact local brightness, colorfulness, and hue ratios via Pillow + NumPy."""
    with Image.open(image_path) as image:
        rgb_image = image.convert("RGB")
        rgb_image.thumbnail((128, 128))
        arr = np.asarray(rgb_image, dtype=np.float32) / 255.0

    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    cmax = np.max(arr, axis=-1)
    cmin = np.min(arr, axis=-1)
    diff = cmax - cmin

    sat = np.where(cmax > 1e-6, diff / (cmax + 1e-6), 0.0)
    val = cmax

    hue = np.zeros_like(cmax)
    mask = diff > 1e-6
    rm = mask & (cmax == r)
    gm = mask & (cmax == g)
    bm = mask & (cmax == b)
    hue[rm] = (60.0 * ((g[rm] - b[rm]) / diff[rm])) % 360.0
    hue[gm] = (60.0 * ((b[gm] - r[gm]) / diff[gm]) + 120.0) % 360.0
    hue[bm] = (60.0 * ((r[bm] - g[bm]) / diff[bm]) + 240.0) % 360.0

    # Hasler-Susstrunk RGB colorfulness normalized to [0, 1].
    rg = (r - g) * 255.0
    yb = (0.5 * (r + g) - b) * 255.0
    raw_cf = float(
        np.sqrt(np.std(rg) ** 2 + np.std(yb) ** 2)
        + 0.3 * np.sqrt(np.mean(rg) ** 2 + np.mean(yb) ** 2)
    )
    colorfulness = float(np.clip(raw_cf / 100.0, 0.0, 1.0))

    color_masks = {
        "red": ((hue <= 12.0) | (hue >= 335.0)) & (sat >= 0.45) & (val >= 0.12),
        "pink": (
            ((hue >= 305.0) & (hue < 335.0) & (sat >= 0.22) & (val >= 0.35))
            | (((hue <= 10.0) | (hue >= 335.0)) & (sat >= 0.22) & (sat < 0.55) & (val >= 0.65))
        ),
        "brown": ((hue <= 38.0) | (hue >= 345.0))
        & (sat >= 0.16)
        & (sat < 0.48)
        & (val >= 0.10)
        & (val < 0.60),
        "orange": (hue > 12.0) & (hue <= 38.0) & (sat >= 0.48) & (val >= 0.35),
        "yellow": (hue > 38.0) & (hue <= 68.0) & (sat >= 0.28) & (val >= 0.35),
        "green": (hue > 68.0) & (hue <= 165.0) & (sat >= 0.18) & (val >= 0.12),
        "blue": (hue > 165.0) & (hue <= 255.0) & (sat >= 0.18) & (val >= 0.12),
        "purple": (hue > 255.0) & (hue <= 305.0) & (sat >= 0.18) & (val >= 0.12),
        "black": (val < 0.16) | ((val < 0.22) & (sat < 0.28)),
        "white": (val > 0.85) & (sat < 0.14),
        "gray": (sat < 0.18) & (val >= 0.16) & (val <= 0.85),
    }

    colors = {
        name: round(float(np.mean(color_mask)), 4)
        for name, color_mask in color_masks.items()
    }

    return {
        "mean_brightness": round(float(np.mean(val)), 4),
        "dark_ratio": round(float(np.mean(val < 0.28)), 4),
        "bright_ratio": round(float(np.mean(val > 0.72)), 4),
        "mean_saturation": round(float(np.mean(sat)), 4),
        "colorfulness": round(colorfulness, 4),
        "vibrant_ratio": round(float(np.mean((sat >= 0.48) & (val >= 0.25))), 4),
        "soft_color_ratio": round(
            float(np.mean((sat >= 0.08) & (sat <= 0.45) & (val >= 0.35))), 4
        ),
        "colors": colors,
    }


def extract_visual_query_cues(query: str) -> dict[str, Any]:
    """Identify explicit color, brightness, and colorfulness cues in a query."""
    clean = " ".join(query.strip().split())
    colors = list(
        dict.fromkeys(_COLOR_ALIASES[m.lower()] for m in _COLOR_WORD_PATTERN.findall(clean))
    )
    is_colorful = bool(_COLORFUL_PATTERN.search(clean))
    is_muted = bool(_MUTED_PATTERN.search(clean))
    is_dark = bool(_DARK_PATTERN.search(clean))
    # Avoid treating "bright colors" as high white luminance.
    cleaned_no_bright_colors = re.sub(
        r"\bbright\s+colors?\b", "", clean, flags=re.IGNORECASE
    )
    is_bright = bool(_BRIGHT_PATTERN.search(cleaned_no_bright_colors)) or bool(
        _LIGHT_TONE_PATTERN.search(clean)
    )

    return {
        "colors": colors,
        "colorful": is_colorful,
        "muted": is_muted,
        "dark": is_dark,
        "bright": is_bright,
        "has_any": bool(colors or is_colorful or is_muted or is_dark or is_bright),
    }


def compute_visual_modifier(
    visual_features: dict[str, Any] | None,
    cues: dict[str, Any],
    semantic_score: float,
) -> float:
    """Compute a small bounded modifier [-0.030, +0.035] gated by semantic relevance."""
    if not visual_features or not cues.get("has_any"):
        return 0.0

    # Prevent visually matching but semantically unrelated images from getting boosted.
    positive_gate = float(np.clip((semantic_score - 0.12) / 0.12, 0.0, 1.0))

    raw_adjustments: list[float] = []
    color_dist = visual_features.get("colors", {})

    for color in cues.get("colors", []):
        ratio = float(color_dist.get(color, 0.0))
        if ratio >= 0.08:
            # 0.08 -> ~+0.006, 0.35+ -> +0.025
            raw_adjustments.append(min(0.025, 0.075 * ratio))
        else:
            raw_adjustments.append(-0.018 * (1.0 - ratio / 0.08))

    if cues.get("colorful"):
        cf = float(visual_features.get("colorfulness", 0.0))
        vr = float(visual_features.get("vibrant_ratio", 0.0))
        vividness = 0.65 * cf + 0.35 * min(1.0, vr * 2.0)
        if vividness >= 0.45:
            raw_adjustments.append(min(0.025, 0.05 * (vividness - 0.35)))
        elif vividness < 0.32:
            raw_adjustments.append(-0.025 * (0.32 - vividness) / 0.32)

    if cues.get("muted"):
        soft_ratio = float(visual_features.get("soft_color_ratio", 0.0))
        cf = float(visual_features.get("colorfulness", 0.0))
        if 0.10 <= cf <= 0.48 and soft_ratio >= 0.15:
            raw_adjustments.append(min(0.020, 0.035 * soft_ratio))
        elif cf > 0.65:
            raw_adjustments.append(-0.012)

    if cues.get("dark"):
        dark_ratio = float(visual_features.get("dark_ratio", 0.0))
        mean_b = float(visual_features.get("mean_brightness", 0.5))
        if dark_ratio >= 0.35 or mean_b <= 0.42:
            raw_adjustments.append(min(0.022, 0.035 * dark_ratio))
        elif mean_b >= 0.68 and dark_ratio < 0.15:
            raw_adjustments.append(-0.015)

    if cues.get("bright"):
        bright_ratio = float(visual_features.get("bright_ratio", 0.0))
        mean_b = float(visual_features.get("mean_brightness", 0.5))
        if mean_b >= 0.55 or bright_ratio >= 0.35:
            raw_adjustments.append(min(0.020, 0.03 * max(0.0, mean_b - 0.45)))
        elif mean_b < 0.30:
            raw_adjustments.append(-0.012)

    if not raw_adjustments:
        return 0.0

    modifier = float(np.mean(raw_adjustments))
    if modifier > 0:
        modifier *= positive_gate

    return float(np.clip(modifier, -0.030, 0.035))
