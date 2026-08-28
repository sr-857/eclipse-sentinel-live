"""
Eclipse Sentinel — Document Validation Service

Checks quality and structure: resolution, brightness, contrast, blur,
aspect ratio, OCR readability, and field completeness.
Returns: PASS / WARNING / FAIL with explanation.
"""

import cv2
import numpy as np


def _check_image_quality(image_path: str) -> dict:
    image = cv2.imread(image_path)
    if image is None:
        return {"quality_score": 0.0, "issues": ["Could not read image"]}

    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    resolution_ok = w >= 400 and h >= 300
    brightness = float(np.mean(gray))
    brightness_ok = 40 < brightness < 230
    contrast = float(np.std(gray))
    contrast_ok = contrast > 20
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    blur_ok = laplacian_var > 50
    ratio = w / h if h > 0 else 0
    ratio_ok = 0.5 < ratio < 3.0

    issues = []
    if not resolution_ok: issues.append(f"Low resolution ({w}x{h})")
    if not brightness_ok: issues.append(f"Poor brightness ({brightness:.0f})")
    if not contrast_ok: issues.append(f"Low contrast ({contrast:.0f})")
    if not blur_ok: issues.append(f"Blurry image (sharpness={laplacian_var:.0f})")
    if not ratio_ok: issues.append(f"Unusual aspect ratio ({ratio:.2f})")

    score = sum([resolution_ok, brightness_ok, contrast_ok, blur_ok, ratio_ok]) / 5.0
    return {
        "resolution": {"width": w, "height": h},
        "brightness": round(brightness, 1),
        "contrast": round(contrast, 1),
        "sharpness": round(laplacian_var, 1),
        "aspect_ratio": round(ratio, 2),
        "quality_score": round(score, 2),
        "issues": issues,
    }


def validate_document(image_path: str, ocr_result: dict) -> dict:
    quality = _check_image_quality(image_path)
    quality_score = quality.get("quality_score", 0.0)

    ocr_success = ocr_result.get("ocr_success", False)
    ocr_confidence = ocr_result.get("confidence", 0.0)
    word_count = ocr_result.get("word_count", 0)
    fields = ocr_result.get("fields", {})

    important_fields = ["possible_name", "possible_date_of_birth", "possible_document_number"]
    fields_found = sum(1 for f in important_fields if f in fields)
    field_score = fields_found / len(important_fields)

    ocr_norm = min(ocr_confidence / 100.0, 1.0) if ocr_success else 0.0
    combined = quality_score * 0.4 + ocr_norm * 0.3 + field_score * 0.3

    reasons = []
    if combined >= 0.65:
        status = "PASS"
        reasons.append("Document meets basic quality and content requirements")
    elif combined >= 0.35:
        status = "WARNING"
        if quality["issues"]: reasons.append(f"Quality: {', '.join(quality['issues'][:2])}")
        if word_count < 5: reasons.append("Limited readable text")
        if fields_found < 2: reasons.append("Some ID fields not found")
        if not reasons: reasons.append("Needs closer review")
    else:
        status = "FAIL"
        if not ocr_success: reasons.append("No readable text extracted")
        if quality["issues"]: reasons.append(f"Quality: {', '.join(quality['issues'][:3])}")
        if not reasons: reasons.append("Below minimum quality standards")

    return {
        "status": status,
        "reason": "; ".join(reasons),
        "score": round(combined, 2),
        "details": {
            "image_quality": quality,
            "ocr_readable": ocr_success,
            "ocr_confidence": ocr_confidence,
            "word_count": word_count,
            "fields_found": fields_found,
        },
    }
