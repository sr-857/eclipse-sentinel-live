"""
Eclipse Sentinel — Backend Test Suite (SIH26188 Prototype)

Demonstrates the 3 test cases required by SIH specifications:

TEST 1: Clean document -> Mostly PASS -> Low risk
TEST 2: Poor / modified document -> Warning signals -> Medium risk
TEST 3: Suspicious document + face mismatch -> Multiple warnings -> High risk

Run with:
    python -m unittest tests/test_backend.py
"""

import os
import unittest
import numpy as np
import cv2
import tempfile

from services.preprocessing import preprocess_document
from services.ocr import extract_text
from services.document_check import validate_document
from services.tampering import analyse_tampering
from services.face_verification import detect_and_verify_face
from services.consistency import check_consistency
from services.risk_engine import calculate_risk
from services.liveness import check_liveness_placeholder


def create_mock_id_card(mode="clean") -> str:
    """Helper to generate mock image documents for testing."""
    h, w = (600, 950) if mode != "poor" else (200, 250)
    img = np.ones((h, w, 3), dtype=np.uint8) * 240

    if mode == "clean":
        # Clear background header
        cv2.rectangle(img, (0, 0), (w, 80), (120, 50, 20), -1)
        cv2.putText(img, "REPUBLIC IDENTITY CARD", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        # Name & ID
        cv2.putText(img, "NAME: JOHN DOE", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(img, "DOCUMENT NUMBER: ECL-26188-042", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(img, "DATE OF BIRTH: 14/09/1998", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(img, "EXPIRY DATE: 14/09/2030", (50, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    elif mode == "poor":
        # Dark, low-contrast, blurry image
        img = (img * 0.2).astype(np.uint8)
        cv2.putText(img, "blur text", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (50, 50, 50), 1)
        img = cv2.GaussianBlur(img, (15, 15), 0)
    elif mode == "suspicious":
        # Spliced / tampered regions with high contrast patches
        cv2.rectangle(img, (50, 50), (400, 200), (255, 0, 0), -1)
        cv2.rectangle(img, (450, 50), (850, 200), (0, 255, 255), -1)
        cv2.putText(img, "NAME: 123#@$%", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(img, "DOB: 99/99/9999", (50, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    cv2.imwrite(tmp.name, img)
    tmp.close()
    return tmp.name


class TestEclipseSentinelBackend(unittest.TestCase):

    def test_case_1_clean_document(self):
        """TEST 1: Clean document -> Mostly PASS -> Low risk"""
        img_path = create_mock_id_card("clean")
        try:
            prep_path, _ = preprocess_document(img_path)
            ocr = extract_text(prep_path)
            doc_val = validate_document(prep_path, ocr)
            tamp = analyse_tampering(prep_path)
            face = detect_and_verify_face(prep_path)
            cons = check_consistency(ocr)
            live = check_liveness_placeholder()

            risk = calculate_risk(doc_val, tamp, face, cons, live)

            self.assertIn(risk["risk_level"], ["LOW", "MEDIUM"])
            self.assertEqual(risk["recommended_action"], "CLEAR" if risk["risk_level"] == "LOW" else "MANUAL REVIEW")
            self.assertTrue(doc_val["status"] in ["PASS", "WARNING"])
        finally:
            os.unlink(img_path)

    def test_case_2_poor_modified_document(self):
        """TEST 2: Poor / modified document -> Warning signals -> Medium risk"""
        img_path = create_mock_id_card("poor")
        try:
            prep_path, _ = preprocess_document(img_path)
            ocr = extract_text(prep_path)
            doc_val = validate_document(prep_path, ocr)
            tamp = analyse_tampering(prep_path)
            face = detect_and_verify_face(prep_path)
            cons = check_consistency(ocr)
            live = check_liveness_placeholder()

            risk = calculate_risk(doc_val, tamp, face, cons, live)

            self.assertIn(risk["risk_level"], ["MEDIUM", "HIGH"])
            self.assertNotEqual(risk["recommended_action"], "CLEAR")
        finally:
            os.unlink(img_path)

    def test_case_3_suspicious_document(self):
        """TEST 3: Suspicious document -> Multiple warnings -> High risk"""
        img_path = create_mock_id_card("suspicious")
        try:
            prep_path, _ = preprocess_document(img_path)
            ocr = extract_text(prep_path)
            doc_val = validate_document(prep_path, ocr)
            tamp = analyse_tampering(prep_path)
            face = detect_and_verify_face(prep_path)
            cons = check_consistency(ocr)
            live = check_liveness_placeholder()

            risk = calculate_risk(doc_val, tamp, face, cons, live)

            self.assertIn(risk["risk_level"], ["MEDIUM", "HIGH"])
            self.assertEqual(risk["recommended_action"], "MANUAL REVIEW" if risk["risk_level"] == "MEDIUM" else "SECONDARY VERIFICATION")
        finally:
            os.unlink(img_path)


if __name__ == "__main__":
    unittest.main()
