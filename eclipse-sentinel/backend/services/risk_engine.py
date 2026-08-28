"""
Eclipse Sentinel — Risk Engine

Calculates the final risk score from all prototype checks.
Uses a transparent weighted scoring system — NO random numbers.

Weights:
    Document validation     20%
    Tampering analysis      30%
    Face verification       30%
    Data consistency        10%
    Liveness                10%

Score mapping:
    0–30  = LOW RISK    → CLEAR
    31–70 = MEDIUM RISK → MANUAL REVIEW
    71–100 = HIGH RISK  → SECONDARY VERIFICATION
"""


def _status_to_score(status: str) -> float:
    """Convert a check status to a risk contribution (0.0 = safe, 1.0 = risky)."""
    status = status.upper().strip()
    mapping = {
        # Safe statuses
        "PASS": 0.1,
        "NORMAL": 0.1,
        "MATCH": 0.1,
        "FACE DETECTED": 0.15,
        "LIKELY LIVE": 0.1,
        # Moderate concern
        "WARNING": 0.5,
        "REVIEW": 0.55,
        "PROTOTYPE": 0.4,
        # High concern
        "FAIL": 0.85,
        "SUSPICIOUS": 0.9,
        "MISMATCH": 0.9,
        "FACE NOT DETECTED": 0.6,
        # Unavailable
        "NOT AVAILABLE": 0.35,
        "UNAVAILABLE": 0.35,
    }
    return mapping.get(status, 0.4)


def calculate_risk(
    doc_validation: dict,
    tampering: dict,
    face_result: dict,
    consistency: dict,
    liveness: dict,
) -> dict:
    """
    Calculate the final risk score and generate explanation.

    Returns:
        {
            "risk_score": int (0–100),
            "risk_level": "LOW" | "MEDIUM" | "HIGH",
            "recommended_action": str,
            "explanation": dict,
        }
    """
    # ── Extract individual scores ────────────────────────────────
    doc_status = doc_validation.get("status", "WARNING")
    tampering_status = tampering.get("status", "REVIEW")
    face_status = face_result.get("status", "FACE NOT DETECTED")
    consistency_status = consistency.get("status", "WARNING")
    liveness_status = liveness.get("status", "NOT AVAILABLE")

    doc_risk = _status_to_score(doc_status)
    tampering_risk = _status_to_score(tampering_status)
    face_risk = _status_to_score(face_status)
    consistency_risk = _status_to_score(consistency_status)
    liveness_risk = _status_to_score(liveness_status)

    # ── Weighted combination ─────────────────────────────────────
    # Weights: doc=20%, tampering=30%, face=30%, consistency=10%, liveness=10%
    weighted_score = (
        doc_risk * 0.20
        + tampering_risk * 0.30
        + face_risk * 0.30
        + consistency_risk * 0.10
        + liveness_risk * 0.10
    )

    # Scale to 0–100
    risk_score = int(round(weighted_score * 100))
    risk_score = max(0, min(100, risk_score))

    # ── Determine risk level ─────────────────────────────────────
    if risk_score <= 30:
        risk_level = "LOW"
        recommended_action = "CLEAR"
    elif risk_score <= 70:
        risk_level = "MEDIUM"
        recommended_action = "MANUAL REVIEW"
    else:
        risk_level = "HIGH"
        recommended_action = "SECONDARY VERIFICATION"

    # ── Build explanation ────────────────────────────────────────
    def _icon(status):
        s = status.upper()
        if s in ("PASS", "NORMAL", "MATCH", "FACE DETECTED", "LIKELY LIVE"):
            return "✓"
        elif s in ("FAIL", "SUSPICIOUS", "MISMATCH"):
            return "✗"
        else:
            return "⚠"

    findings = [
        {
            "check": "Document Validation",
            "status": doc_status,
            "icon": _icon(doc_status),
            "weight": "20%",
            "detail": doc_validation.get("reason", ""),
        },
        {
            "check": "Tampering Analysis",
            "status": tampering_status,
            "icon": _icon(tampering_status),
            "weight": "30%",
            "detail": tampering.get("reason", ""),
        },
        {
            "check": "Face Verification",
            "status": face_status,
            "icon": _icon(face_status),
            "weight": "30%",
            "detail": face_result.get("comparison", {}).get("reason", "")
                      or ("Face detected in document" if face_status == "FACE DETECTED" else "No face found"),
        },
        {
            "check": "Data Consistency",
            "status": consistency_status,
            "icon": _icon(consistency_status),
            "weight": "10%",
            "detail": consistency.get("reason", ""),
        },
        {
            "check": "Liveness",
            "status": liveness_status,
            "icon": _icon(liveness_status),
            "weight": "10%",
            "detail": liveness.get("reason", ""),
        },
    ]

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "recommended_action": recommended_action,
        "explanation": {
            "summary": f"Risk score {risk_score}/100 — {risk_level} RISK",
            "findings": findings,
            "scoring_method": "Weighted combination of prototype check results",
            "weights": {
                "document_validation": "20%",
                "tampering_analysis": "30%",
                "face_verification": "30%",
                "data_consistency": "10%",
                "liveness": "10%",
            },
        },
    }
