# ECLIPSE SENTINEL
## AI-Based Fake Identity & Document Screening System
**Team Eclipse | Challenge ID: SIH26188**

GitHub Repository: [https://github.com/sr-857/eclipse-sentinel.git](https://github.com/sr-857/eclipse-sentinel.git)

---

> [!IMPORTANT]
> **PROTOTYPE DISCLAIMER**
> This project is a **student / SIH working ML prototype demonstration** built for decision support.
> It does **NOT** claim government-level verification, certified fraud detection, 100% accuracy, real-time government database access, Apple Face ID integration, or production blockchain deployment.

---

## 📌 Goal & Pipeline Workflow

Eclipse Sentinel provides an explainable AI-assisted screening flow for identity document verification:

```
[ UPLOAD ID ]
     ↓
  [ READ ]           (OpenCV Image Preprocessing: Resize, Denoise, CLAHE, Deskew)
     ↓
  [ CHECK ]          (Tesseract OCR + Document Quality & Field Validation)
     ↓
  [ FACE ]           (Haar Cascade Face Detection + DeepFace Verification)
     ↓
 [ ANALYSE ]         (Prototype Tampering ELA/Edge Analysis + Consistency Checks)
     ↓
[ RISK SCORE ]       (Transparent Weighted Scoring Engine: 0–100)
     ↓
[ RECOMMENDATION ]   (CLEAR / MANUAL REVIEW / SECONDARY VERIFICATION)
```

---

## 📁 Project Structure

```
eclipse-sentinel/
├── backend/
│   ├── main.py                  # FastAPI Application & POST /screen endpoint
│   ├── Dockerfile               # Production Docker container setup
│   ├── requirements.txt          # Python dependencies
│   ├── services/
│   │   ├── preprocessing.py     # OpenCV resize, orientation, CLAHE & deskew
│   │   ├── ocr.py               # Tesseract OCR & heuristic field extraction
│   │   ├── document_check.py    # Image quality & field completeness validator
│   │   ├── tampering.py         # Prototype Tampering ELA & noise consistency
│   │   ├── face_verification.py # Haar Cascade detection & DeepFace matching
│   │   ├── liveness.py          # Prototype Liveness status module
│   │   ├── consistency.py       # Data field & format cross-checker
│   │   └── risk_engine.py       # Transparent weighted risk score calculator
│   ├── models/                  # ML Model storage directory
│   └── tests/
│       └── test_backend.py      # Automated SIH test cases suite
├── frontend/                     # React + Vite UI console
└── README.md                    # System Documentation & Deployment Guide
```

---

## 🌐 Live Production Deployment Guide

All Replit-specific plugins and environment lock-ins have been completely stripped for clean cloud deployment.

### 1. Deploying Backend (FastAPI ML Server)
Option A: **Render / Railway / Fly.io (Docker)**
- Use `backend/Dockerfile`.
- Set Environment Variables: `PORT=8000`.
- System dependencies (Tesseract OCR, OpenCV libs) are auto-installed inside the container.

Option B: **Linux VPS (Ubuntu / Debian)**
```bash
sudo apt update && sudo apt install -y tesseract-ocr libgl1-mesa-glx
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Deploying Frontend (Vite + React)
Option A: **Vercel / Netlify**
- Framework Preset: Vite
- Build Command: `pnpm build` or `npm run build`
- Output Directory: `dist`

---

## ⚙️ Requirements & Local Setup

### Prerequisites
1. **Python 3.10+**
2. **Tesseract OCR Engine**
   - Ubuntu / Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`
   - Windows: Install from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.

### Backend Python Packages (`requirements.txt`)
- `fastapi` & `uvicorn` (API Server)
- `opencv-python-headless` & `Pillow` (Image Processing)
- `pytesseract` (OCR Engine)
- `scikit-learn` & `scipy` (Numerical Analysis)
- `deepface` (Face Verification)

---

## 🚀 Local Running Instructions

### 1. Backend Startup

```bash
cd eclipse-sentinel/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be live at `http://localhost:8000`. Test interactive docs at `http://localhost:8000/docs`.

### 2. Frontend Startup

```bash
pnpm install
pnpm dev
```

The UI will open in your browser at `http://localhost:5173`.

---

## 🧪 Running Test Cases

Run the automated test cases suite covering Clean, Poor, and Suspicious documents:

```bash
cd eclipse-sentinel/backend
python3 -m unittest tests/test_backend.py
```

### Test Case Overview
- **TEST 1 (Clean document)**: High image quality + readable OCR → **LOW RISK / CLEAR**
- **TEST 2 (Poor document)**: Blurry / low contrast image → **MEDIUM RISK / MANUAL REVIEW**
- **TEST 3 (Suspicious document)**: Splicing anomalies + text errors → **HIGH RISK / SECONDARY VERIFICATION**

---

## 🔌 API Endpoint Reference

### `POST /screen`

**Request Format**: `multipart/form-data`
- `document` (File, Required): Image file (JPG, PNG, WEBP, PDF)
- `face_image` (File, Optional): Secondary live face photo for verification

**Response JSON Example**:
```json
{
  "prototype_notice": "This is a prototype ML demonstration. Results are for screening support only.",
  "risk_score": 63,
  "risk_level": "MEDIUM",
  "recommended_action": "MANUAL REVIEW",
  "document_validation": {
    "status": "PASS",
    "reason": "Document meets basic quality and content requirements"
  },
  "tampering": {
    "status": "REVIEW",
    "score": 0.42,
    "label": "Prototype Tampering Analysis",
    "reason": "Possible concerns: compression inconsistencies detected"
  },
  "face_verification": {
    "status": "MATCH",
    "similarity": 0.81,
    "model": "VGG-Face (DeepFace)"
  },
  "data_consistency": {
    "status": "WARNING",
    "reason": "Minor inconsistencies in: Date of Birth"
  },
  "liveness": {
    "status": "NOT AVAILABLE",
    "label": "PROTOTYPE LIVENESS"
  }
}
```

---

## 🗺️ Roadmap & Future Architecture

1. **Hyperledger Fabric Integration**: Verifiable tamper-proof ledger for document metadata hashes.
2. **Government Database Integration**: Direct API lookups (e.g. DigiLocker / Aadhaar / Passport portals).
3. **Multi-Frame Anti-Spoofing Liveness**: Real-time 3D depth and blink detection via web camera stream.
4. **Large-Scale Document Classifier**: Fine-tuned LayoutLMv3 for automated multi-country ID classification.

---

**TEAM ECLIPSE — SIH26188**
