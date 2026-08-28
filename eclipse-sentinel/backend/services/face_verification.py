"""
Eclipse Sentinel — Face Detection & Verification Service

Uses OpenCV Haar cascades for face detection and DeepFace for
face embedding comparison when a second face image is provided.

Face detection:  FACE DETECTED / FACE NOT DETECTED
Face comparison:  MATCH / REVIEW / MISMATCH  (with similarity score)
"""

import cv2
import numpy as np
from typing import Optional


# Use OpenCV's built-in Haar cascade for face detection (no extra model download)
_FACE_CASCADE = None


def _get_face_cascade():
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _FACE_CASCADE = cv2.CascadeClassifier(cascade_path)
    return _FACE_CASCADE


def _detect_faces(image_path: str) -> dict:
    """Detect faces in the image using Haar cascade."""
    image = cv2.imread(image_path)
    if image is None:
        return {"detected": False, "count": 0, "reason": "Could not read image"}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    cascade = _get_face_cascade()
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )

    count = len(faces)
    return {
        "detected": count > 0,
        "count": count,
        "regions": [
            {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}
            for (x, y, w, h) in faces
        ] if count > 0 else [],
    }


def _compare_faces_deepface(doc_path: str, face_path: str) -> dict:
    """
    Compare faces using DeepFace embeddings.
    Falls back gracefully if DeepFace is not available.
    """
    try:
        from deepface import DeepFace

        result = DeepFace.verify(
            img1_path=doc_path,
            img2_path=face_path,
            model_name="VGG-Face",
            enforce_detection=False,
            detector_backend="opencv",
        )

        distance = result.get("distance", 1.0)
        threshold = result.get("threshold", 0.4)
        verified = result.get("verified", False)

        # Convert distance to similarity (0–1, higher = more similar)
        similarity = max(0.0, 1.0 - distance)

        if verified or similarity > 0.65:
            status = "MATCH"
        elif similarity > 0.45:
            status = "REVIEW"
        else:
            status = "MISMATCH"

        return {
            "comparison_available": True,
            "similarity": round(similarity, 3),
            "status": status,
            "model": "VGG-Face (DeepFace)",
            "reason": f"Face similarity: {similarity:.0%}",
        }

    except ImportError:
        return _compare_faces_histogram(doc_path, face_path)
    except Exception as e:
        # If DeepFace fails, fall back to histogram comparison
        return _compare_faces_histogram(doc_path, face_path)


def _compare_faces_histogram(doc_path: str, face_path: str) -> dict:
    """
    Fallback face comparison using histogram correlation.
    Less accurate but always works without extra models.
    """
    img1 = cv2.imread(doc_path)
    img2 = cv2.imread(face_path)

    if img1 is None or img2 is None:
        return {
            "comparison_available": False,
            "status": "REVIEW",
            "reason": "Could not read one or both images for comparison",
        }

    cascade = _get_face_cascade()

    def extract_face_region(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
        if len(faces) > 0:
            x, y, w, h = faces[0]
            return img[y:y+h, x:x+w]
        return img  # Use full image if no face found

    face1 = extract_face_region(img1)
    face2 = extract_face_region(img2)

    # Resize both to same size
    size = (128, 128)
    face1 = cv2.resize(face1, size)
    face2 = cv2.resize(face2, size)

    # Compare histograms
    hist1 = cv2.calcHist([face1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist2 = cv2.calcHist([face2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])

    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)

    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    similarity = max(0.0, min(1.0, float(similarity)))

    if similarity > 0.7:
        status = "MATCH"
    elif similarity > 0.45:
        status = "REVIEW"
    else:
        status = "MISMATCH"

    return {
        "comparison_available": True,
        "similarity": round(similarity, 3),
        "status": status,
        "model": "Histogram Correlation (Fallback)",
        "reason": f"Face similarity: {similarity:.0%} (fallback method)",
    }


def detect_and_verify_face(
    document_path: str,
    face_image_path: Optional[str] = None,
) -> dict:
    """
    Main face detection and verification function.

    1. Detect if a face exists in the document
    2. If a second face image is provided, compare them

    Returns combined result.
    """
    # Step 1: Face detection in document
    detection = _detect_faces(document_path)

    result = {
        "face_detected": detection["detected"],
        "face_count": detection["count"],
        "status": "FACE DETECTED" if detection["detected"] else "FACE NOT DETECTED",
    }

    if detection["detected"] and detection.get("regions"):
        result["face_regions"] = detection["regions"]

    # Step 2: Face comparison if second image provided
    if face_image_path and detection["detected"]:
        # Also check if face exists in the reference image
        ref_detection = _detect_faces(face_image_path)
        if ref_detection["detected"]:
            comparison = _compare_faces_deepface(document_path, face_image_path)
            result["comparison"] = comparison
            result["status"] = comparison["status"]
        else:
            result["comparison"] = {
                "comparison_available": False,
                "status": "REVIEW",
                "reason": "No face detected in reference image",
            }
            result["status"] = "REVIEW"
    elif face_image_path and not detection["detected"]:
        result["comparison"] = {
            "comparison_available": False,
            "status": "REVIEW",
            "reason": "No face found in document to compare against",
        }

    return result
