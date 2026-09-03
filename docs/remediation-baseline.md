# Sentinel Remediation Baseline

## Git State
Branch: main
Commit Hash: 8d812d165db1c57ecb8bbda3724c7471f4e5b30c

## Test Results
*(Waiting for pytest to finish)*

## Frontend Build Result
The frontend (in `frontend/`) consists of static HTML/JS/CSS files without a bundler build step (no package.json or webpack detected in the directory). A React version exists in `frontend-react/` but the active mockup identified in the audit is the static one.

## Backend Startup Result
*(Not started yet, but previous analysis shows it uses standard FastAPI/uvicorn and containerized services.)*

## Current ML Metrics
*(Based on previously generated `experiments/ablation.md` or similar)*
- The model exhibits temporal leakage and target parameter leakage, resulting in inflated PR-AUC scores.

## Current Risk-Fusion Behavior
- The fusion engine (`ml/fusion/risk_fusion.py`) currently uses a confidence-weighted **average** of behavioral and semantic risk scores. This allows a critical semantic risk to be diluted by a benign behavioral risk.

## Current Frontend/Backend Connectivity
- The frontend dashboard is fully static. All KPIs, timelines, charts, and feed events are hardcoded in `frontend/js/data.js`. No live data fetches from the backend API are present in the core flow.
