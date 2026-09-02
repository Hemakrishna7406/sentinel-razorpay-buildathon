# Sentinel E2E Test Suite

End-to-end tests for Sentinel RC1 using Playwright. These tests validate the complete user journey from landing page to demo execution, ensuring the system is ready for buildathon judges.

## Test Coverage

### 1. Landing Page (`landing.spec.ts`)
- Hero section and messaging
- Animated architecture diagram
- CTA button functionality
- Performance benchmarks

### 2. Demo Scenarios (`demo-scenarios.spec.ts`)
- Normal Agent scenario (ALLOW)
- Suspicious Agent scenario (ESCALATE)
- Malicious Agent scenario (CONTAIN)
- Replay Attack scenario (REJECT)
- Redis Failure scenario (FAIL_CLOSED)
- Execution timeline visualization

### 3. Dashboard Overview (`dashboard-overview.spec.ts`)
- KPI cards
- Decision trend charts
- Risk distribution
- System health indicators
- Navigation

### 4. Live Decisions (`live-decisions.spec.ts`)
- Decision feed display
- Real-time updates
- Decision details modal
- Filtering and search
- Performance metrics

### 5. Audit Ledger (`audit-ledger.spec.ts`)
- Audit entry display
- Chain integrity verification
- Hash chain visualization
- Export functionality

### 6. Security Command Center (`security-command-center.spec.ts`) ⚠️ CRITICAL
- 5 Security Invariants (must all be 0):
  - Unauthorized executions
  - Duplicate executions (JTI replay)
  - Unsafe ALLOW decisions
  - Audit chain breaks
  - Fail-open incidents
- Release gate status (220/220 tests)
- Threat detection metrics
- System health indicators

## Running Tests

### Prerequisites

```bash
# Install dependencies (already done)
cd frontend
npm install

# Install Playwright browsers (already done)
npx playwright install
```

### Run All Tests

```bash
# From frontend directory
npm run test:e2e
```

### Run with UI Mode (Interactive)

```bash
npm run test:e2e:ui
```

### Debug Mode

```bash
npm run test:e2e:debug
```

### Run Specific Test File

```bash
npx playwright test landing.spec.ts
```

### Run Tests in Headed Mode (See Browser)

```bash
npx playwright test --headed
```

### View Test Report

```bash
npm run test:e2e:report
```

## Test Structure

Each test file follows this pattern:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/path');
    await page.waitForLoadState('networkidle');
  });

  test('should do something', async ({ page }) => {
    // Arrange
    const element = page.locator('[data-testid="element"]');
    
    // Act
    await element.click();
    
    // Assert
    await expect(element).toContainText('expected text');
  });
});
```

## Test Data Attributes

Frontend components use `data-testid` attributes for reliable test selectors:

```tsx
<div data-testid="decision-card">
  <span data-testid="decision-type">ALLOW</span>
  <span data-testid="risk-score">0.23</span>
</div>
```

## CI/CD Integration

Tests run automatically in CI via the release gate:

```bash
# Full release gate (from project root)
./scripts/release-gate.sh
```

This runs:
1. Backend tests (220 tests)
2. Frontend build
3. E2E tests (all specs)
4. Security invariants check

## Performance Benchmarks

- Landing page load: < 3 seconds
- Dashboard load: < 2 seconds
- Scenario execution: < 5 seconds
- Decision feed load: < 2 seconds

## Debugging Failed Tests

### 1. Check Screenshots

Failed tests automatically capture screenshots:

```
test-results/
  landing-spec-ts-landing-page-should-load/
    test-failed-1.png
```

### 2. View Trace

```bash
npx playwright show-trace test-results/trace.zip
```

### 3. Run in Debug Mode

```bash
npm run test:e2e:debug
```

### 4. Check Network Logs

Tests capture network activity. Check HAR files in `test-results/`.

## Common Issues

### Tests Timing Out

- Increase timeout in specific test:
  ```typescript
  test('slow test', async ({ page }) => {
    test.setTimeout(30000); // 30 seconds
  });
  ```

### Flaky Tests

- Add explicit waits:
  ```typescript
  await page.waitForSelector('[data-testid="element"]', { timeout: 10000 });
  ```

### Backend Not Running

- Tests expect backend at `http://localhost:8000`
- Start backend: `uvicorn api.main:app`
- Frontend dev server starts automatically

## Writing New Tests

1. Add test file to `tests/e2e/`
2. Use descriptive test names
3. Add `data-testid` to components
4. Follow existing patterns
5. Test critical user paths first
6. Add performance benchmarks

## Judge Readiness Checklist

Before presenting to judges, ensure:

- [ ] All E2E tests pass
- [ ] Release gate shows green
- [ ] Demo scenarios execute flawlessly
- [ ] Security invariants all show 0
- [ ] No console errors in browser
- [ ] Performance benchmarks met

## Contact

For issues with E2E tests, contact the QA Engineer (Task #16 owner).
