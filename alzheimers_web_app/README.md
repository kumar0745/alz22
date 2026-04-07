# NeuroDetect AI — Alzheimer’s MRI Web Application

A polished, production-oriented demo platform combining:
- **React + Vite** frontend with modern glassmorphism UI and brain visualization
- **FastAPI** backend serving AI-based MRI classification
- **PyTorch** model training with ResNet50 and Grad-CAM explainability

## Project Overview

This repository is built for professional demonstration and development of an Alzheimer’s MRI classification system. The app supports:
- MRI image upload and classification
- confidence scores and clinical summary text
- Grad-CAM heatmap explainability
- brain region analysis and symptom insights
- separate backend and frontend development workflows

## Repository Structure

- `frontend/` — Vite + React UI, complete with hero section, MRI upload, clinical tool, and data visualization
- `backend/` — FastAPI service for prediction, image preprocessing, model loading, and Grad-CAM support
- `training/` — PyTorch training pipeline for ResNet50 and dataset splitting
- `dataset/` — organized MRI classes for model training
- `docs/` — architecture and supporting documentation

## Local Setup

### 1. Backend

```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Default dev CORS origins are configured for `http://localhost:8080` and `http://127.0.0.1:8080`.

### 2. Frontend

```bash
cd frontend
npm ci
npm run dev
```

Open **http://localhost:8080** to view the app. The frontend proxy is configured to reach the backend API automatically.

### 3. Training (optional)

If you want to train a new model using your dataset:

```bash
cd training
pip install -r requirements.txt
python train.py
```

This generates:
- `backend/model/weights.pt`
- `backend/model/model_metadata.json`
- `backend/model/training_metrics.json`

If no trained model is found, the backend returns demo predictions so the UI remains functional.

## Environment Examples

- `backend/.env.example` — backend runtime environment variables
- `frontend/.env.example` — Vite API URL configuration

## GitHub Ready

This repository now includes a GitHub Actions workflow at `.github/workflows/ci.yml` that:
- validates Python files in `backend/` and `training/`
- installs frontend dependencies and builds the React app

## Deployment Notes

- Use `backend/model/weights.pt` for best deployment performance
- The FastAPI backend supports optional Grad-CAM explainability through `/api/predict?explain=true`
- Adjust `MAX_UPLOAD_MB` and `CORS_ORIGINS` in `backend/.env.example`

## Next Steps for GitHub

This folder is not yet a git repository. To publish to GitHub, run:

```bash
git init
git add .
git commit -m "chore: add docs and CI for NeuroDetect AI"
git remote add origin <your-github-repo-url>
git push -u origin main
```

If you provide a GitHub repository URL or credentials, I can help you connect and push from this workspace.

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — system design and data flow.

## Disclaimer

For **research and education** only — not for clinical diagnosis.
