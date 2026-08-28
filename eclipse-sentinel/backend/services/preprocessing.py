"""
Eclipse Sentinel — Image Preprocessing Service

Uses OpenCV to prepare uploaded document images for OCR and analysis:
  • Resize to a manageable resolution
  • Orientation handling
  • Noise reduction (Gaussian blur + Non-local means denoising)
  • Contrast improvement (CLAHE)
  • Basic document alignment attempt (deskew)
"""

import os
import tempfile
import cv2
import numpy as np


def _deskew(image: np.ndarray) -> np.ndarray:
    """Attempt to correct small rotation / skew in a document image."""
    try:
        gray = image if len(image.shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Use Canny + HoughLines to detect dominant angle
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
        if lines is None or len(lines) < 3:
            return image

        angles = []
        for rho, theta in lines[:, 0]:
            angle_deg = np.degrees(theta) - 90
            if -15 < angle_deg < 15:  # Only consider small deviations
                angles.append(angle_deg)

        if not angles:
            return image

        median_angle = float(np.median(angles))
        if abs(median_angle) < 0.3:
            return image  # Already straight enough

        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            image, rotation_matrix, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return rotated
    except Exception:
        return image  # If deskew fails, return original


def preprocess_document(image_path: str) -> tuple:
    """
    Preprocess the document image for analysis.

    Returns:
        (preprocessed_path, info_dict)
    """
    info = {
        "steps": [],
        "original_size": None,
        "processed_size": None,
    }

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image at {image_path}")

    h, w = image.shape[:2]
    info["original_size"] = {"width": w, "height": h}
    info["steps"].append("Image loaded successfully")

    # ── Resize if too large (keep aspect ratio) ─────────────────────
    max_dimension = 2000
    if max(h, w) > max_dimension:
        scale = max_dimension / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        info["steps"].append(f"Resized from {w}x{h} to {new_w}x{new_h}")
    else:
        info["steps"].append("Resolution within acceptable range")

    # ── Orientation handling ─────────────────────────────────────────
    # Basic: if portrait-oriented, check if it's likely a landscape doc flipped
    h2, w2 = image.shape[:2]
    if h2 > w2 * 1.8:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        info["steps"].append("Rotated 90° (detected portrait orientation)")
    else:
        info["steps"].append("Orientation looks correct")

    # ── Noise reduction ──────────────────────────────────────────────
    denoised = cv2.fastNlMeansDenoisingColored(image, None, 6, 6, 7, 15)
    info["steps"].append("Applied noise reduction (Non-local means denoising)")

    # ── Contrast improvement (CLAHE) ─────────────────────────────────
    lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l_channel)
    enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    info["steps"].append("Enhanced contrast using CLAHE")

    # ── Basic deskew attempt ─────────────────────────────────────────
    deskewed = _deskew(enhanced)
    if deskewed is not enhanced:
        info["steps"].append("Applied deskew correction")
    else:
        info["steps"].append("No significant skew detected")

    # ── Save processed image ─────────────────────────────────────────
    h_final, w_final = deskewed.shape[:2]
    info["processed_size"] = {"width": w_final, "height": h_final}

    out_path = tempfile.NamedTemporaryFile(
        delete=False, suffix=".png", prefix="eclipse_preprocessed_"
    ).name
    cv2.imwrite(out_path, deskewed)
    info["steps"].append("Preprocessing complete")

    return out_path, info
