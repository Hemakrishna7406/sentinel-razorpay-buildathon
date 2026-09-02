# Sentinel — Repository Audit

## Repository Structure

- `api/` (FastAPI backend)
- `dashboard/` (Legacy frontend - KEEP for now, target for removal)
- `frontend/` (Canonical React frontend - KEEP)
- `core/`, `security/`, `ml/`, `db/` (Core application logic - KEEP)
- `benchmarks/`, `tests/` (Test suites - KEEP)
- `.agents/` (Agent Tooling - REQUIRES REVIEW, mostly personal tools)
- Root files (Dockerfile, .env.example, README.md, STATUS.md)

## Duplication & Dead Code Candidates

- **Dashboard vs Frontend**: `dashboard/` is considered legacy but currently still referenced by `api/main.py`.
- **Scripts**: Root output scripts like `gpu_output.txt`, `final_cpu_scaling_output.txt`, `scaling_output.txt`, `threading_output.txt` appear to be generated benchmarking outputs. (Target for deletion/archiving).
- **SQLite DB**: `test_sentinel.db` shouldn't be committed if it's dynamic state.
- **Agent Tooling**: `apple-design`, `animate`, `write-swift` skills are likely editor/agent-specific tools that should not be in production unless specifically requested by the project workflow.

## Dependencies

- **FastAPI / Python**: Defined in `requirements.txt`. Need a detailed audit to ensure no development-only packages are shipped to production.
- **Frontend / React**: Defined in `frontend/package.json`.

## Configuration Files

- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `alembic.ini`
- `pyproject.toml`
- `prometheus/recording_rules.yml`

## Recommendations

1. **Frontend**: Complete migration of `dashboard` features to `frontend`, then delete `dashboard`. Update `api/main.py` routing.
2. **Scripts/Outputs**: Clean up generated `.txt` benchmark outputs. 
3. **Docs**: Reorganize existing markdown files into `docs/`.
4. **Agent Tooling**: Filter out non-Sentinel specific `.agents` skills to reduce repo bloat.
