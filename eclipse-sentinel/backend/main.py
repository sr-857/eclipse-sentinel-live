"""
Eclipse Sentinel — AI-Based Fake Identity & Document Screening System
FastAPI Backend — ML Prototype

Team Eclipse | SIH26188

IMPORTANT: This is a PROTOTYPE / DEMONSTRATION system.
It does NOT provide production-grade identity verification.
"""

import os
import tempfile
import traceback
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.preprocessing import preprocess_document
from services.ocr import extract_text
from services.document_check import validate_document
from services.tampering import analyse_tampering
from services.face_verification import detect_and_verify_face
from services.liveness import check_liveness_placeholder
from services.consistency import check_consistency
from services.risk_engine import calculate_risk

app = FastAPI(
    title="Eclipse Sentinel — ML Prototype",
    description="AI-Based Identity & Document Screening Prototype (SIH26188)",
    version="1.0.0-prototype",
)

# Allow the frontend (any origin for demo purposes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "project": "Eclipse Sentinel",
        "team": "Team Eclipse",
        "challenge": "SIH26188",
        "status": "ML Prototype Running",
        "endpoint": "POST /screen",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "prototype": True}


@app.post("/screen")
async def screen_document(
    document: UploadFile = File(...),
    face_image: Optional[UploadFile] = File(None),
):
    """
    Main screening endpoint.

    Accepts:
        document  — The ID document image (required)
        face_image — An optional second face/live image for comparison

    Returns a full screening result with risk score, checks, and recommendation.
    """
    result = {
        "prototype_notice": "This is a prototype ML demonstration. Results are for screening support only.",
    }

    # ── 1. Read and validate the uploaded file ──────────────────────────
    allowed_types = {
        "image/jpeg", "image/jpg", "image/png", "image/webp",
        "application/pdf",
    }
    if document.content_type and document.content_type not in allowed_types:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unsupported file type: {document.content_type}. Accepted: JPG, PNG, WEBP, PDF."},
        )

    doc_bytes = await document.read()
    if len(doc_bytes) == 0:
        return JSONResponse(status_code=400, content={"error": "Empty file uploaded."})
    if len(doc_bytes) > 20 * 1024 * 1024:
        return JSONResponse(status_code=400, content={"error": "File too large (max 20 MB)."})

    # Save to temp file for processing
    suffix = os.path.splitext(document.filename or "doc.png")[1] or ".png"
    doc_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    doc_tmp.write(doc_bytes)
    doc_tmp.close()

    face_tmp_path = None
    if face_image and face_image.filename:
        face_bytes = await face_image.read()
        if len(face_bytes) > 0:
            face_suffix = os.path.splitext(face_image.filename or "face.png")[1] or ".png"
            face_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=face_suffix)
            face_tmp.write(face_bytes)
            face_tmp.close()
            face_tmp_path = face_tmp.name

    try:
        # ── 2. Preprocessing ───────────────────────────────────────────
        preprocessed_path, preprocess_info = preprocess_document(doc_tmp.name)
        result["preprocessing"] = preprocess_info

        # ── 3. OCR ─────────────────────────────────────────────────────
        ocr_result = extract_text(preprocessed_path)
        result["ocr"] = ocr_result

        # ── 4. Document Check ──────────────────────────────────────────
        doc_validation = validate_document(preprocessed_path, ocr_result)
        result["document_validation"] = doc_validation

        # ── 5. Tampering Analysis ──────────────────────────────────────
        tampering = analyse_tampering(preprocessed_path)
        result["tampering"] = tampering

        # ── 6 & 7. Face Detection & Verification ──────────────────────
        face_result = detect_and_verify_face(preprocessed_path, face_tmp_path)
        result["face_verification"] = face_result

        # ── 8. Liveness ────────────────────────────────────────────────
        liveness = check_liveness_placeholder()
        result["liveness"] = liveness

        # ── 9. Data Consistency ────────────────────────────────────────
        consistency = check_consistency(ocr_result)
        result["data_consistency"] = consistency

        # ── 10–12. Risk Engine + Explanation + Recommendation ─────────
        risk = calculate_risk(
            doc_validation=doc_validation,
            tampering=tampering,
            face_result=face_result,
            consistency=consistency,
            liveness=liveness,
        )
        result["risk_score"] = risk["risk_score"]
        result["risk_level"] = risk["risk_level"]
        result["recommended_action"] = risk["recommended_action"]
        result["explanation"] = risk["explanation"]

    except Exception as e:
        # ── 15. Demo Fallback ──────────────────────────────────────────
        traceback.print_exc()
        result["error"] = "DEMO ANALYSIS UNAVAILABLE"
        result["error_detail"] = str(e)
        result["risk_score"] = None
        result["risk_level"] = "UNAVAILABLE"
        result["recommended_action"] = "SYSTEM ERROR — MANUAL REVIEW REQUIRED"

    finally:
        # Clean up temp files
        try:
            os.unlink(doc_tmp.name)
        except OSError:
            pass
        if preprocessed_path and preprocessed_path != doc_tmp.name:
            try:
                os.unlink(preprocessed_path)
            except OSError:
                pass
        if face_tmp_path:
            try:
                os.unlink(face_tmp_path)
            except OSError:
                pass

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
