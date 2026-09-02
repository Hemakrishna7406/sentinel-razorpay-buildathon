# Dependency Audit

*Note: Requires deeper execution trace, this is an initial map based on the audit phase.*

## Python
- **Used**: `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `pydantic`, `redis`, `xgboost`, `shap`, `mcp`.
- **Action Required**: Need to segregate `requirements.txt` into production dependencies vs. dev dependencies (e.g., `pytest`, `shap`, `xgboost` if ML model is externalized).

## TypeScript (frontend/)
- **Used**: `react`, `react-dom`, `vite`, `tailwindcss`, `typescript`, `@types/*`
- **Action Required**: Need to verify `package.json` for unused generic libraries (e.g., unused UI frameworks).

## Infrastructure
- **Docker**: Requires `python:3.11-slim`.
- **Services**: Depends on `Redis` (for idempotency), `PostgreSQL` (via SQLAlchemy), `Kafka/Redpanda` (architecture mentioned but needs validation on dependencies), and `Razorpay MCP`.
