"""
Eclipse Sentinel — OCR Service

Uses Tesseract (via pytesseract) to extract text from the preprocessed
document image.  Attempts to identify common identity-document fields
such as Name, Date of Birth, Document Number, and Expiry Date.

Returns structured results with confidence indicators.
"""

import re
import cv2
import pytesseract
import numpy as np


# Common date patterns found on ID documents
_DATE_PATTERNS = [
    r"\b(\d{2}[/\-.]\d{2}[/\-.]\d{4})\b",          # DD/MM/YYYY
    r"\b(\d{4}[/\-.]\d{2}[/\-.]\d{2})\b",          # YYYY/MM/DD
    r"\b(\d{2}\s*/\s*\d{2}\s*/\s*\d{4})\b",        # DD / MM / YYYY (with spaces)
    r"\b(\d{1,2}\s+\w{3,9}\s+\d{4})\b",            # 14 September 1998
]

# Document number patterns (alphanumeric, dashes, common formats)
_DOC_NUM_PATTERNS = [
    r"\b([A-Z]{1,3}[-\s]?\d{5,10}[-\s]?\d{0,5})\b",   # ECL-26188-042
    r"\b(\d{4}\s?\d{4}\s?\d{4})\b",                     # 1234 5678 9012
    r"\b([A-Z]\d{7,8})\b",                               # Passport-style: A1234567
]


def _prepare_for_ocr(image_path: str) -> np.ndarray:
    """Convert to grayscale and apply thresholding for better OCR."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Could not read image for OCR")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Adaptive thresholding works well for documents with varying illumination
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15,
        C=8,
    )
    return binary


def _extract_fields(raw_text: str) -> dict:
    """
    Attempt to identify common identity-document fields from raw OCR text.
    Does NOT assume a specific format — uses pattern matching.
    """
    fields = {}
    lines = [ln.strip() for ln in raw_text.split("\n") if ln.strip()]

    # ── Look for dates ───────────────────────────────────────────────
    dates_found = []
    for pattern in _DATE_PATTERNS:
        for match in re.finditer(pattern, raw_text, re.IGNORECASE):
            dates_found.append(match.group(1))

    if dates_found:
        fields["dates_detected"] = dates_found
        # Heuristic: first date is often DOB, second might be expiry
        if len(dates_found) >= 1:
            fields["possible_date_of_birth"] = dates_found[0]
        if len(dates_found) >= 2:
            fields["possible_expiry_date"] = dates_found[1]

    # ── Look for document numbers ────────────────────────────────────
    for pattern in _DOC_NUM_PATTERNS:
        match = re.search(pattern, raw_text)
        if match:
            fields["possible_document_number"] = match.group(1)
            break

    # ── Look for names (heuristic: all-caps words, 2+ words) ────────
    name_keywords = {"NAME", "SURNAME", "GIVEN", "FIRST", "LAST", "FULL"}
    for i, line in enumerate(lines):
        upper_line = line.upper()
        # Check if this line or the previous line contains a name label
        if any(kw in upper_line for kw in name_keywords):
            # The name might be on this line after a colon, or the next line
            parts = line.split(":", 1)
            if len(parts) == 2 and len(parts[1].strip()) > 2:
                fields["possible_name"] = parts[1].strip()
            elif i + 1 < len(lines) and len(lines[i + 1]) > 2:
                fields["possible_name"] = lines[i + 1]
            break

    # If no labelled name found, look for lines with all-caps multi-word text
    if "possible_name" not in fields:
        for line in lines:
            # Skip very short lines and lines that look like labels
            if len(line) < 4 or len(line) > 60:
                continue
            words = line.split()
            if 2 <= len(words) <= 5 and all(w.isalpha() and w.isupper() for w in words):
                fields["possible_name"] = line
                break

    # ── Look for gender ──────────────────────────────────────────────
    gender_match = re.search(r"\b(MALE|FEMALE|M|F)\b", raw_text.upper())
    if gender_match:
        val = gender_match.group(1)
        fields["possible_gender"] = "MALE" if val in ("M", "MALE") else "FEMALE"

    return fields


def extract_text(image_path: str) -> dict:
    """
    Run OCR on the preprocessed document image.

    Returns:
        {
            "ocr_success": bool,
            "extracted_text": str,
            "confidence": float,
            "fields": dict,
            "warnings": list[str],
            "word_count": int,
        }
    """
    result = {
        "ocr_success": False,
        "extracted_text": "",
        "confidence": 0.0,
        "fields": {},
        "warnings": [],
        "word_count": 0,
    }

    try:
        binary_image = _prepare_for_ocr(image_path)

        # Get detailed OCR data including confidence
        ocr_data = pytesseract.image_to_data(
            binary_image,
            output_type=pytesseract.Output.DICT,
            config="--oem 3 --psm 6",
        )

        # Build full text and calculate average confidence
        words = []
        confidences = []
        for i, text in enumerate(ocr_data["text"]):
            text = text.strip()
            conf = int(ocr_data["conf"][i])
            if text and conf > 0:
                words.append(text)
                confidences.append(conf)

        raw_text = " ".join(words)

        # Also get plain text (preserves line structure better)
        plain_text = pytesseract.image_to_string(
            binary_image,
            config="--oem 3 --psm 6",
        ).strip()

        avg_confidence = float(np.mean(confidences)) if confidences else 0.0

        result["ocr_success"] = len(words) > 3
        result["extracted_text"] = plain_text if plain_text else raw_text
        result["confidence"] = round(avg_confidence, 1)
        result["word_count"] = len(words)

        # ── Extract fields ───────────────────────────────────────────
        result["fields"] = _extract_fields(plain_text if plain_text else raw_text)

        # ── Warnings ─────────────────────────────────────────────────
        if avg_confidence < 40:
            result["warnings"].append(
                "Low OCR confidence — text may be unreliable"
            )
        if len(words) < 5:
            result["warnings"].append(
                "Very few words detected — document may be blank or image quality is poor"
            )
        if not result["fields"]:
            result["warnings"].append(
                "Could not identify standard ID fields from the extracted text"
            )

    except Exception as e:
        result["ocr_success"] = False
        result["warnings"].append(f"OCR processing failed: {str(e)}")

    return result
