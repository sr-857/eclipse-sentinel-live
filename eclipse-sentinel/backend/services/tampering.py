"""
Eclipse Sentinel — Prototype Tampering Analysis

Detects possible image manipulation using OpenCV-based signals:
  • Error Level Analysis (ELA) — compression inconsistencies
  • Edge density analysis — abnormal edge patterns
  • Texture consistency — local variance analysis
  • Noise level analysis — inconsistent noise patterns

Returns: NORMAL / REVIEW / SUSPICIOUS with a tampering score.
This is labeled "Prototype Tampering Analysis".
"""

import cv2
import numpy as np
import tempfile
import os


def _error_level_analysis(image_path: str) -> float:
    """
    ELA: Re-compress the image and compare to find regions with
    different compression levels (possible splicing indicator).
    Returns a score 0.0–1.0 where higher = more suspicious.
    """
    image = cv2.imread(image_path)
    if image is None:
        return 0.5

    # Re-save at low quality
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp.close()
    cv2.imwrite(tmp.name, image, [cv2.IMWRITE_JPEG_QUALITY, 75])
    recompressed = cv2.imread(tmp.name)
    os.unlink(tmp.name)

    if recompressed is None:
        return 0.5

    # Resize if shapes differ slightly
    if image.shape != recompressed.shape:
        recompressed = cv2.resize(recompressed, (image.shape[1], image.shape[0]))

    # Calculate difference
    diff = cv2.absdiff(image, recompressed).astype(np.float32)
    ela_map = np.mean(diff, axis=2)  # Average across channels

    # Analyse the distribution of ELA values
    mean_ela = float(np.mean(ela_map))
    std_ela = float(np.std(ela_map))

    # High std relative to mean suggests uneven compression = suspicious
    if mean_ela < 1.0:
        return 0.1  # Likely a PNG (no JPEG compression artifacts)

    ratio = std_ela / (mean_ela + 1e-6)
    # Normalize to 0–1 range
    score = min(1.0, ratio / 2.0)
    return round(score, 3)


def _edge_density_analysis(image_path: str) -> float:
    """
    Check for abnormal edge density patterns that might indicate
    cut-and-paste regions.
    Returns 0.0–1.0 where higher = more anomalous.
    """
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return 0.5

    edges = cv2.Canny(image, 50, 150)

    # Divide into grid and check edge density variance
    h, w = edges.shape
    grid_h, grid_w = max(1, h // 4), max(1, w // 4)
    densities = []

    for r in range(4):
        for c in range(4):
            region = edges[r*grid_h:(r+1)*grid_h, c*grid_w:(c+1)*grid_w]
            if region.size > 0:
                density = float(np.sum(region > 0)) / region.size
                densities.append(density)

    if not densities:
        return 0.5

    # High coefficient of variation in edge density = suspicious
    mean_d = float(np.mean(densities))
    std_d = float(np.std(densities))

    if mean_d < 0.001:
        return 0.1  # Very few edges (blank/solid regions)

    cv_score = std_d / (mean_d + 1e-6)
    return round(min(1.0, cv_score / 3.0), 3)


def _noise_analysis(image_path: str) -> float:
    """
    Analyse noise levels across image regions.
    Inconsistent noise suggests different source images were combined.
    Returns 0.0–1.0 where higher = more suspicious.
    """
    image = cv2.imread(image_path)
    if image is None:
        return 0.5

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float64)

    # Estimate noise using Laplacian
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)

    h, w = laplacian.shape
    grid_h, grid_w = max(1, h // 4), max(1, w // 4)
    noise_levels = []

    for r in range(4):
        for c in range(4):
            region = laplacian[r*grid_h:(r+1)*grid_h, c*grid_w:(c+1)*grid_w]
            if region.size > 0:
                noise_levels.append(float(np.std(region)))

    if len(noise_levels) < 2:
        return 0.3

    mean_n = float(np.mean(noise_levels))
    std_n = float(np.std(noise_levels))

    if mean_n < 1.0:
        return 0.1

    cv_noise = std_n / (mean_n + 1e-6)
    return round(min(1.0, cv_noise / 1.5), 3)


def analyse_tampering(image_path: str) -> dict:
    """
    Run prototype tampering analysis on the document image.

    Returns:
        {
            "status": "NORMAL" | "REVIEW" | "SUSPICIOUS",
            "score": float (0.0–1.0, higher = more suspicious),
            "label": "Prototype Tampering Analysis",
            "signals": dict,
            "reason": str,
        }
    """
    try:
        ela_score = _error_level_analysis(image_path)
        edge_score = _edge_density_analysis(image_path)
        noise_score = _noise_analysis(image_path)
    except Exception as e:
        return {
            "status": "REVIEW",
            "score": 0.5,
            "label": "Prototype Tampering Analysis",
            "signals": {},
            "reason": f"Analysis partially failed: {str(e)}",
        }

    # Weighted combination
    combined = ela_score * 0.40 + edge_score * 0.30 + noise_score * 0.30
    combined = round(combined, 3)

    # Determine status
    if combined < 0.25:
        status = "NORMAL"
        reason = "No significant manipulation signals detected"
    elif combined < 0.55:
        status = "REVIEW"
        reasons = []
        if ela_score > 0.3:
            reasons.append("compression inconsistencies detected")
        if edge_score > 0.3:
            reasons.append("uneven edge patterns")
        if noise_score > 0.3:
            reasons.append("noise level variations")
        reason = "Possible concerns: " + ", ".join(reasons) if reasons else "Minor anomalies warrant review"
    else:
        status = "SUSPICIOUS"
        reason = "Multiple tampering signals detected — manual inspection recommended"

    return {
        "status": status,
        "score": combined,
        "label": "Prototype Tampering Analysis",
        "signals": {
            "error_level_analysis": ela_score,
            "edge_density": edge_score,
            "noise_consistency": noise_score,
        },
        "reason": reason,
    }
