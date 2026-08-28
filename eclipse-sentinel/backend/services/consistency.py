"""
Eclipse Sentinel — Data Consistency Service

Uses OCR results to perform basic consistency checks:
  • Missing fields
  • Invalid date formats
  • Suspicious characters in names/numbers
  • Conflicting information
  • Basic internal consistency

Returns: PASS / WARNING / FAIL
"""

import re
from datetime import datetime


def _check_date_validity(date_str: str) -> dict:
    """Check if a detected date string is valid."""
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
        "%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d",
        "%d %B %Y", "%d %b %Y",
    ]

    # Clean up extra spaces
    cleaned = re.sub(r"\s+", " ", date_str.strip())

    for fmt in formats:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            # Basic sanity: date should be between 1920 and 2040
            if 1920 <= parsed.year <= 2040:
                return {"valid": True, "parsed": parsed.isoformat()[:10]}
            else:
                return {"valid": False, "reason": f"Year {parsed.year} is out of expected range"}
        except ValueError:
            continue

    return {"valid": False, "reason": "Could not parse date format"}


def _check_name_validity(name: str) -> dict:
    """Check if detected name looks reasonable."""
    if not name or len(name) < 2:
        return {"valid": False, "reason": "Name too short"}

    # Check for suspicious characters (digits, special chars in names)
    suspicious_chars = re.findall(r"[0-9@#$%^&*()+=\[\]{}|\\<>]", name)
    if suspicious_chars:
        return {"valid": False, "reason": f"Suspicious characters in name: {''.join(suspicious_chars)}"}

    # Check for reasonable length
    if len(name) > 80:
        return {"valid": False, "reason": "Name unusually long"}

    return {"valid": True}


def _check_doc_number(number: str) -> dict:
    """Check if document number format is reasonable."""
    if not number or len(number) < 3:
        return {"valid": False, "reason": "Document number too short"}

    # Should be mostly alphanumeric
    alnum_count = sum(1 for c in number if c.isalnum())
    total = len(number.replace(" ", "").replace("-", ""))

    if total > 0 and alnum_count / max(1, total) < 0.7:
        return {"valid": False, "reason": "Too many special characters in document number"}

    return {"valid": True}


def check_consistency(ocr_result: dict) -> dict:
    """
    Perform data consistency checks on OCR results.

    Returns:
        {
            "status": "PASS" | "WARNING" | "FAIL",
            "reason": str,
            "score": float (0.0–1.0),
            "checks": list,
        }
    """
    if not ocr_result.get("ocr_success", False):
        return {
            "status": "FAIL",
            "reason": "No OCR data available for consistency check",
            "score": 0.0,
            "checks": [],
        }

    fields = ocr_result.get("fields", {})
    checks = []
    issues = 0
    total = 0

    # ── Check name ───────────────────────────────────────────────
    if "possible_name" in fields:
        total += 1
        name_check = _check_name_validity(fields["possible_name"])
        checks.append({
            "field": "Name",
            "value": fields["possible_name"],
            "valid": name_check["valid"],
            "note": name_check.get("reason", "Looks valid"),
        })
        if not name_check["valid"]:
            issues += 1
    else:
        total += 1
        issues += 0.5
        checks.append({"field": "Name", "value": None, "valid": False, "note": "Not detected"})

    # ── Check DOB ────────────────────────────────────────────────
    if "possible_date_of_birth" in fields:
        total += 1
        dob_check = _check_date_validity(fields["possible_date_of_birth"])
        checks.append({
            "field": "Date of Birth",
            "value": fields["possible_date_of_birth"],
            "valid": dob_check["valid"],
            "note": dob_check.get("reason", dob_check.get("parsed", "Valid")),
        })
        if not dob_check["valid"]:
            issues += 1

        # Cross-check: DOB should be in the past
        if dob_check["valid"]:
            try:
                dob_date = datetime.fromisoformat(dob_check["parsed"])
                if dob_date > datetime.now():
                    issues += 1
                    checks[-1]["note"] = "Date of birth is in the future — suspicious"
                    checks[-1]["valid"] = False
            except (ValueError, KeyError):
                pass
    else:
        total += 1
        issues += 0.5
        checks.append({"field": "Date of Birth", "value": None, "valid": False, "note": "Not detected"})

    # ── Check document number ────────────────────────────────────
    if "possible_document_number" in fields:
        total += 1
        doc_check = _check_doc_number(fields["possible_document_number"])
        checks.append({
            "field": "Document Number",
            "value": fields["possible_document_number"],
            "valid": doc_check["valid"],
            "note": doc_check.get("reason", "Format looks valid"),
        })
        if not doc_check["valid"]:
            issues += 1
    else:
        total += 1
        issues += 0.5
        checks.append({"field": "Document Number", "value": None, "valid": False, "note": "Not detected"})

    # ── Check expiry date ────────────────────────────────────────
    if "possible_expiry_date" in fields:
        total += 1
        exp_check = _check_date_validity(fields["possible_expiry_date"])
        checks.append({
            "field": "Expiry Date",
            "value": fields["possible_expiry_date"],
            "valid": exp_check["valid"],
            "note": exp_check.get("reason", exp_check.get("parsed", "Valid")),
        })
        if not exp_check["valid"]:
            issues += 1

    # ── OCR confidence as a signal ───────────────────────────────
    ocr_confidence = ocr_result.get("confidence", 0.0)
    if ocr_confidence < 40:
        issues += 0.5
        checks.append({
            "field": "OCR Confidence",
            "value": f"{ocr_confidence:.0f}%",
            "valid": False,
            "note": "Low confidence — extracted data may be unreliable",
        })

    # ── Calculate score ──────────────────────────────────────────
    score = max(0.0, 1.0 - (issues / max(total, 1))) if total > 0 else 0.0
    score = round(score, 2)

    if score >= 0.7:
        status = "PASS"
        reason = "Data fields appear consistent"
    elif score >= 0.4:
        status = "WARNING"
        problem_fields = [c["field"] for c in checks if not c["valid"]]
        reason = f"Minor inconsistencies in: {', '.join(problem_fields)}" if problem_fields else "Some data needs review"
    else:
        status = "FAIL"
        reason = "Significant data inconsistencies detected"

    return {
        "status": status,
        "reason": reason,
        "score": score,
        "checks": checks,
    }
