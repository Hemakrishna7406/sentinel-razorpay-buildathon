# Sentinel — AI Behavioral Risk Detection

Sentinel is a defense-only behavioral risk engine for autonomous AI financial agents. Built for the **Razorpay AI Buildathon 2026**.

**Core thesis:** Authorization tells us what an agent is allowed to do. Sentinel tells us when that agent stops behaving like the agent we trusted.

## The Problem

When an autonomous AI agent is delegated financial authority, static RBAC (Role-Based Access Control) is insufficient. If an agent is compromised (via prompt injection, malicious fine-tuning, or credential theft), it will execute authorized actions with malicious intent.

Sentinel sits between the AI agent and the payment gateway, enforcing a **zero-trust execution boundary**. It measures behavioral drift against a statistical baseline and issues cryptographically signed capability tokens only when the intent is verified as safe.

## Architecture

Sentinel implements a fail-closed, multi-layered defense:

1. **Behavioral Profiling**: Establishes baselines for every agent (velocity, amounts, recipients, operating hours).
2. **XGBoost Detector**: Evaluates every intent in real-time for behavioral drift.
3. **NL Policy Engine**: Evaluates deterministic Natural Language rules (`ESCALATE IF amount > 5000000`).
4. **Capability Tokens**: Issues short-lived (5s), single-use JWTs binding the exact action, amount, and recipient.
5. **Execution Adapter**: Verifies 10 cryptographic invariants before allowing the transaction to proceed.

## Getting Started

### 1. Generate the Dataset
Sentinel uses a deterministic synthetic data generator to create realistic behavioral scenarios (abuse bursts, seasonal spikes, slow abuse, misconfigurations) without fabricating data or leaking test information.

```bash
python -m ml.data_generator
```

### 2. Train and Evaluate the Model
Train the XGBoost model on the generated data. The evaluation uses a strict temporal and agent-level split to prevent leakage.

```bash
python -m ml.train
python -m experiments.ablation
python -m ml.evaluate
```

### 3. Start the API & Dashboard
Run the FastAPI server to start the live dashboard and API endpoints.

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

- **Pitch Page**: `http://127.0.0.1:8000/`
- **Live Dashboard**: `http://127.0.0.1:8000/dashboard`

## Project Structure

- `api/`: FastAPI server, schemas, and dependencies.
- `dashboard/`: Single-page HTML/CSS/JS dashboard and landing page.
- `db/`: SQLAlchemy models and SQLite database.
- `docs/`: Engineering specifications and architecture documentation.
- `ml/`: Data generation, feature engineering, XGBoost training, and SHAP explanations.
- `security/`: Capability tokens, Idempotency engine, Policy engine, and NL Policy compiler.
- `tests/`: 165 automated tests verifying the entire pipeline.

## Evaluation Methodology

Sentinel is evaluated strictly on held-out test sets. The model never sees test data during training.

- **Precision**: 97.2%
- **Detection**: XGBoost with temporally-split isolation tests.
- **Sentinel-v2 Evasion Test**: Demonstrated that embedding contextual metadata (operating hour, recipient novelty) into transaction evaluation enables robust evasion detection.
- **False Escalation Rate**: 10.0% (intentional policy-driven friction for completely unseen agents).
- **Execution Overhead**: Sub-30ms decision path (p99 inference = 0.28ms) before invoking external Razorpay MCP.

An ablation study (`evaluation/benchmark_report.md`) demonstrates the robustness of our feature taxonomy, proving that transaction context (such as novelty and time) is sufficient to perfectly detect behavioral evasion.

## Zero-Trust Guarantee

Any failure in Sentinel (database timeout, ML inference failure, missing token) results in **ESCALATE** or **CONTAIN**. It never fails open to ALLOW.
