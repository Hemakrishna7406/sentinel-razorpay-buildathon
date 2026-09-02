# Sentinel — Repository Cleanup Plan

## Proposed Cleanup

### 1. File Categorization

**KEEP**
- `api/`, `core/`, `security/`, `ml/`, `db/`, `alembic/`, `observability/`, `benchmarks/`, `tests/`, `frontend/`, `docs/`
- `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `.env.example`, `.gitignore`

**MOVE**
- Move loose root documentation (e.g., `CODEX.md`, `dataset.md`, `dataset_stats.md`, `evaluation.md`, `threat-model.md`, `STATUS.md` eventually) into `docs/`.
- Consolidate root test scripts into `tests/`.

**MERGE**
- Features from `dashboard/` into `frontend/`.

**ARCHIVE/DELETE**
- Generated benchmark output files: `gpu_output.txt`, `scaling_output.txt`, `threading_output.txt`, `final_cpu_scaling_output.txt`.
- Generated databases: `test_sentinel.db`.
- Extraneous root scripts: `get_dataset_stats.py`, `verify_audit_chain.py` (move to `scripts/` or delete if obsolete).

**UNKNOWN — REQUIRES REVIEW**
- `.agents/`: Determine which skills are essential for the workflow. Unused design and animation skills might be deleted.

## Cleanup Execution Sequence

**Commit 1: Safe Cleanup**
- Move loose documentation into `docs/`.
- Delete `.txt` output artifacts.
- Move utility scripts into `scripts/`.
- Ensure `.gitignore` covers local test databases.

**Commit 2: Agent Tooling Review**
- Prune `.agents/` folder of unused skills.

**Commit 3: Frontend Canonicalization**
- Remove `dashboard/` from root.
- Remove references to `dashboard/` from `api/main.py`.
- Configure `api/main.py` to route to `frontend/dist/` or treat them as separate deployment units.

**Commit 4: Documentation Normalization**
- Rewrite `README.md` to reflect `frontend/` as canonical UI and link to `docs/` architecture documents.

**Commit 5: Production-hardening Changes**
- Verify tests and Docker configuration works with new structure.
