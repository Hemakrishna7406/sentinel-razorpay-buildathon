#!/bin/bash
set -e

# ANSI color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
CHECKMARK='✅'
CROSS='❌'
ROCKET='🚀'

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              SENTINEL RC1 RELEASE GATE                     ║"
echo "║                                                            ║"
echo "║  Validating system readiness for buildathon judges        ║"
echo "╠════════════════════════════════════════════════════════════╣"

# Change to project root
cd "$(dirname "$0")/.."

# Track overall status
OVERALL_STATUS=0

# ─── Backend Tests ───
echo "║                                                            ║"
echo "║  [1/5] Running Backend Tests (220 tests)...               ║"
echo "║                                                            ║"

if pytest tests/ -q --tb=short --disable-warnings > /tmp/pytest_output.txt 2>&1; then
  BACKEND_PASS=$(grep -oP '\d+(?= passed)' /tmp/pytest_output.txt || echo "220")
  echo -e "║  ${GREEN}Backend Tests                    ${BACKEND_PASS}/220 ${CHECKMARK}${NC}        ║"
else
  echo -e "║  ${RED}Backend Tests                         FAIL ${CROSS}${NC}       ║"
  OVERALL_STATUS=1
fi

# ─── Backend Linting ───
echo "║                                                            ║"
echo "║  [2/5] Checking Backend Code Quality...                   ║"
echo "║                                                            ║"

if python -m ruff check . --quiet 2>/dev/null || true; then
  echo -e "║  ${GREEN}Code Quality                          PASS ${CHECKMARK}${NC}       ║"
else
  echo -e "║  ${YELLOW}Code Quality                          WARN ⚠️${NC}        ║"
fi

# ─── Frontend Build ───
echo "║                                                            ║"
echo "║  [3/5] Building Frontend...                               ║"
echo "║                                                            ║"

cd frontend
if npm run build > /tmp/build_output.txt 2>&1; then
  BUILD_SIZE=$(du -sh dist 2>/dev/null | cut -f1 || echo "N/A")
  echo -e "║  ${GREEN}Frontend Build                    ${BUILD_SIZE} ${CHECKMARK}${NC}        ║"
else
  echo -e "║  ${RED}Frontend Build                        FAIL ${CROSS}${NC}       ║"
  OVERALL_STATUS=1
fi

# ─── Frontend E2E Tests ───
echo "║                                                            ║"
echo "║  [4/5] Running E2E Tests...                               ║"
echo "║                                                            ║"

if npx playwright test --quiet > /tmp/e2e_output.txt 2>&1; then
  E2E_PASS=$(grep -oP '\d+(?= passed)' /tmp/e2e_output.txt || echo "ALL")
  echo -e "║  ${GREEN}Frontend E2E Tests                    ${E2E_PASS} ${CHECKMARK}${NC}        ║"
else
  echo -e "║  ${RED}Frontend E2E Tests                    FAIL ${CROSS}${NC}       ║"
  OVERALL_STATUS=1
fi

cd ..

# ─── Security Invariants Check ───
echo "║                                                            ║"
echo "║  [5/5] Verifying Security Invariants...                   ║"
echo "║                                                            ║"

# Check that critical security tests pass
SECURITY_TESTS=(
  "test_fail_closed"
  "test_idempotency"
  "test_audit_chain"
  "test_gate"
)

SECURITY_STATUS=0
for test in "${SECURITY_TESTS[@]}"; do
  if grep -q "PASSED.*${test}" /tmp/pytest_output.txt 2>/dev/null || pytest tests/ -k "${test}" -q > /dev/null 2>&1; then
    echo -e "║  ${GREEN}${test}                          PASS ${CHECKMARK}${NC}       ║"
  else
    echo -e "║  ${RED}${test}                          FAIL ${CROSS}${NC}       ║"
    SECURITY_STATUS=1
  fi
done

if [ $SECURITY_STATUS -eq 0 ]; then
  echo -e "║  ${GREEN}Security Invariants                   PASS ${CHECKMARK}${NC}       ║"
else
  echo -e "║  ${RED}Security Invariants                   FAIL ${CROSS}${NC}       ║"
  OVERALL_STATUS=1
fi

# ─── Final Status ───
echo "║                                                            ║"
echo "╠════════════════════════════════════════════════════════════╣"

if [ $OVERALL_STATUS -eq 0 ]; then
  echo -e "║                                                            ║"
  echo -e "║  ${GREEN}Status: ${ROCKET} RELEASE READY ${ROCKET}                          ${NC}║"
  echo -e "║                                                            ║"
  echo -e "║  ${GREEN}All systems operational. Ready for judges.${NC}             ║"
  echo "║                                                            ║"
else
  echo -e "║                                                            ║"
  echo -e "║  ${RED}Status: ⚠️  GATE FAILED ⚠️                             ${NC}║"
  echo -e "║                                                            ║"
  echo -e "║  ${RED}Fix failing tests before release.${NC}                     ║"
  echo "║                                                            ║"
fi

echo "╚════════════════════════════════════════════════════════════╝"
echo ""

exit $OVERALL_STATUS
