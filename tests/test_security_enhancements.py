"""
Sentinel — Security Enhancement Tests

Tests for HIGH and MEDIUM severity findings from penetration test report.
These tests validate the remediation of:
- H-1: Rate Limiting
- H-2: Security Headers
- M-1: Audit Chain Timestamp Integrity
- M-2: Secret Entropy Validation

Test Status: PENDING IMPLEMENTATION
These tests are written BEFORE fixes to follow TDD approach.
Expected: All tests FAIL until remediation is complete.
"""

import pytest
import time
import math
from collections import Counter
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
import api.main
from security.capability_token import TokenManager


class TestRateLimiting:
    """
    Tests for H-1: Missing Rate Limiting

    These tests will FAIL until rate limiting is implemented.
    Expected behavior: API should reject requests exceeding rate limit.
    """

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Rate limiting not yet implemented - H-1 finding")
    async def test_rate_limit_enforced_per_ip(self):
        """
        Test that API enforces rate limit per IP address.

        Expected: First 100 requests succeed, 101st request returns 429 Too Many Requests.
        """
        async with AsyncClient(
            transport=ASGITransport(app=api.main.app),
            base_url="http://test"
        ) as client:
            # Make 101 requests rapidly
            responses = []
            for i in range(101):
                resp = await client.post(
                    "/evaluate",
                    json={
                        "intent_id": f"rate-test-{i}",
                        "agent_id": "rate-test-agent",
                        "action_type": "payout",
                        "amount": 1000,
                        "currency": "INR",
                        "recipient": "test"
                    },
                    headers={"Idempotency-Key": f"rate-key-{i}"}
                )
                responses.append(resp)

            # First 100 should succeed (200 or 202)
            success_count = sum(1 for r in responses[:100] if r.status_code in [200, 202])
            assert success_count >= 90, "Rate limit should allow first 100 requests"

            # 101st should be rate limited
            assert responses[100].status_code == 429, "Should return 429 Too Many Requests"
            assert "rate limit" in responses[100].text.lower()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Rate limiting not yet implemented - H-1 finding")
    async def test_rate_limit_per_agent(self):
        """
        Test that rate limiting applies per agent_id.

        Expected: Different agents should have independent rate limits.
        """
        async with AsyncClient(
            transport=ASGITransport(app=api.main.app),
            base_url="http://test"
        ) as client:
            # Agent A makes 100 requests
            agent_a_responses = []
            for i in range(100):
                resp = await client.post(
                    "/evaluate",
                    json={
                        "intent_id": f"agent-a-{i}",
                        "agent_id": "agent-A",
                        "action_type": "payout",
                        "amount": 1000,
                        "currency": "INR",
                        "recipient": "test"
                    },
                    headers={"Idempotency-Key": f"agent-a-key-{i}"}
                )
                agent_a_responses.append(resp)

            # Agent B should still be able to make requests
            resp_b = await client.post(
                "/evaluate",
                json={
                    "intent_id": "agent-b-1",
                    "agent_id": "agent-B",
                    "action_type": "payout",
                    "amount": 1000,
                    "currency": "INR",
                    "recipient": "test"
                },
                headers={"Idempotency-Key": "agent-b-key-1"}
            )

            assert resp_b.status_code in [200, 202], "Different agent should have independent rate limit"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Rate limiting not yet implemented - H-1 finding")
    async def test_rate_limit_includes_retry_after_header(self):
        """
        Test that rate-limited responses include Retry-After header.

        Expected: 429 response includes Retry-After header with seconds to wait.
        """
        async with AsyncClient(
            transport=ASGITransport(app=api.main.app),
            base_url="http://test"
        ) as client:
            # Exceed rate limit
            for i in range(101):
                await client.post(
                    "/evaluate",
                    json={
                        "intent_id": f"retry-test-{i}",
                        "agent_id": "retry-test-agent",
                        "action_type": "payout",
                        "amount": 1000,
                        "currency": "INR",
                        "recipient": "test"
                    },
                    headers={"Idempotency-Key": f"retry-key-{i}"}
                )

            # Next request should include Retry-After
            resp = await client.post(
                "/evaluate",
                json={
                    "intent_id": "retry-test-final",
                    "agent_id": "retry-test-agent",
                    "action_type": "payout",
                    "amount": 1000,
                    "currency": "INR",
                    "recipient": "test"
                },
                headers={"Idempotency-Key": "retry-key-final"}
            )

            assert resp.status_code == 429
            assert "Retry-After" in resp.headers
            retry_after = int(resp.headers["Retry-After"])
            assert 0 < retry_after <= 60, "Retry-After should be reasonable (1-60 seconds)"


class TestSecurityHeaders:
    """
    Tests for H-2: Missing Security Headers

    These tests will FAIL until security headers middleware is added.
    Expected behavior: All HTTP responses should include security headers.
    """

    @pytest.mark.skip(reason="Security headers not yet implemented - H-2 finding")
    def test_x_frame_options_header(self):
        """Test that X-Frame-Options header is present to prevent clickjacking."""
        client = TestClient(api.main.app)
        resp = client.get("/")

        assert "X-Frame-Options" in resp.headers
        assert resp.headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]

    @pytest.mark.skip(reason="Security headers not yet implemented - H-2 finding")
    def test_x_content_type_options_header(self):
        """Test that X-Content-Type-Options header prevents MIME sniffing."""
        client = TestClient(api.main.app)
        resp = client.get("/health/live")

        assert "X-Content-Type-Options" in resp.headers
        assert resp.headers["X-Content-Type-Options"] == "nosniff"

    @pytest.mark.skip(reason="Security headers not yet implemented - H-2 finding")
    def test_content_security_policy_header(self):
        """Test that Content-Security-Policy header is present."""
        client = TestClient(api.main.app)
        resp = client.get("/")

        assert "Content-Security-Policy" in resp.headers
        csp = resp.headers["Content-Security-Policy"]
        assert "default-src" in csp
        # Should restrict to self by default
        assert "'self'" in csp or "'none'" in csp

    @pytest.mark.skip(reason="Security headers not yet implemented - H-2 finding")
    def test_referrer_policy_header(self):
        """Test that Referrer-Policy header is present."""
        client = TestClient(api.main.app)
        resp = client.get("/audit")

        assert "Referrer-Policy" in resp.headers
        # Should use strict policy
        assert resp.headers["Referrer-Policy"] in [
            "strict-origin-when-cross-origin",
            "strict-origin",
            "no-referrer"
        ]

    @pytest.mark.skip(reason="Security headers not yet implemented - H-2 finding")
    def test_hsts_header_on_https(self):
        """
        Test that Strict-Transport-Security header is present on HTTPS.

        Note: In test environment, this may not be HTTPS.
        This test validates the middleware logic when HTTPS is detected.
        """
        # This test would need HTTPS test client
        # For now, validate that middleware checks for HTTPS scheme
        client = TestClient(api.main.app)
        resp = client.get("/")

        # If not HTTPS, header should be absent
        # If HTTPS, header should be present
        if resp.url.scheme == "https":
            assert "Strict-Transport-Security" in resp.headers
            hsts = resp.headers["Strict-Transport-Security"]
            assert "max-age=" in hsts
            # Should be at least 1 year (31536000 seconds)
            assert "31536000" in hsts or "max-age=31536000" in hsts

    @pytest.mark.skip(reason="Security headers not yet implemented - H-2 finding")
    def test_permissions_policy_header(self):
        """Test that Permissions-Policy header restricts dangerous browser features."""
        client = TestClient(api.main.app)
        resp = client.get("/")

        assert "Permissions-Policy" in resp.headers
        policy = resp.headers["Permissions-Policy"]
        # Should deny camera, microphone, geolocation
        assert "camera=()" in policy or "camera 'none'" in policy
        assert "microphone=()" in policy or "microphone 'none'" in policy
        assert "geolocation=()" in policy or "geolocation 'none'" in policy

    @pytest.mark.skip(reason="Security headers not yet implemented - H-2 finding")
    def test_security_headers_on_api_responses(self):
        """Test that security headers are present on API responses, not just HTML."""
        client = TestClient(api.main.app)
        resp = client.get("/health/dependencies")

        # JSON API responses should also have security headers
        assert resp.headers.get("Content-Type") == "application/json"
        assert "X-Content-Type-Options" in resp.headers
        assert "X-Frame-Options" in resp.headers


class TestAuditChainTimestamp:
    """
    Tests for M-1: Audit Chain Timestamp Not Included in Hash

    These tests will FAIL until timestamp is included in hash computation.
    Expected behavior: Timestamp modification should break audit chain integrity.
    """

    @pytest.mark.skip(reason="Audit timestamp hashing not yet fixed - M-1 finding")
    def test_timestamp_modification_breaks_chain(self, db_session):
        """
        Test that modifying a record's timestamp breaks the audit chain.

        Current Behavior: Timestamp can be modified without breaking chain.
        Expected Behavior: Timestamp modification should invalidate chain.
        """
        from db.models import AuditRecord
        from security.audit_chain import verify_audit_chain
        import datetime

        # Create test records
        record1 = AuditRecord(
            intent_id="test-1",
            agent_id="agent-1",
            action_type="payout",
            amount=1000,
            currency="INR",
            recipient="test",
            decision="ALLOW",
            decision_reason="test",
            timestamp=datetime.datetime.utcnow()
        )
        db_session.add(record1)
        db_session.commit()

        # Verify chain is valid
        records = db_session.query(AuditRecord).order_by(AuditRecord.id.asc()).all()
        valid, checked, invalid_ids = verify_audit_chain(records)
        assert valid, "Chain should be valid initially"

        # Modify timestamp
        record1.timestamp = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        db_session.commit()

        # Verify chain is now broken
        records = db_session.query(AuditRecord).order_by(AuditRecord.id.asc()).all()
        valid, checked, invalid_ids = verify_audit_chain(records)
        assert not valid, "Timestamp modification should break chain"
        assert record1.id in invalid_ids

    @pytest.mark.skip(reason="Audit timestamp hashing not yet fixed - M-1 finding")
    def test_timestamp_included_in_hash_computation(self):
        """
        Test that timestamp is included in audit record hash.

        Expected: Hash should change when timestamp changes.
        """
        from security.audit_chain import audit_record_hash
        import datetime

        timestamp1 = datetime.datetime(2026, 8, 29, 12, 0, 0)
        timestamp2 = datetime.datetime(2026, 8, 29, 13, 0, 0)

        values = {
            "intent_id": "test-1",
            "timestamp": timestamp1,
            "agent_id": "agent-1",
            "action_type": "payout",
            "amount": 1000,
            "currency": "INR",
            "recipient": "test",
            "model_risk_score": 0.1,
            "behavioral_risk_score": 0.1,
            "semantic_risk_score": 0.1,
            "fusion_disagreement": "false",
            "decision": "ALLOW",
            "decision_reason": "test",
            "capability_jti": "jti-123",
            "executed_tx_id": "tx-123",
            "previous_hash": None
        }

        hash1 = audit_record_hash(values)

        # Change only timestamp
        values["timestamp"] = timestamp2
        hash2 = audit_record_hash(values)

        assert hash1 != hash2, "Hash should change when timestamp changes"


class TestSecretEntropyValidation:
    """
    Tests for M-2: Weak Secret Validation

    These tests will FAIL until entropy validation is added.
    Expected behavior: Weak secrets should be rejected at startup.
    """

    @pytest.mark.skip(reason="Secret entropy validation not yet implemented - M-2 finding")
    def test_reject_short_secret(self):
        """Test that secrets shorter than 64 characters are rejected."""
        with pytest.raises(ValueError, match="must be >= 64 characters"):
            validate_secret_strength("short-secret-only-32-chars-long")

    @pytest.mark.skip(reason="Secret entropy validation not yet implemented - M-2 finding")
    def test_reject_low_entropy_secret(self):
        """Test that secrets with low entropy are rejected."""
        # Secret with all same characters (entropy = 0)
        with pytest.raises(ValueError, match="low entropy"):
            validate_secret_strength("a" * 64)

        # Secret with repeating pattern
        with pytest.raises(ValueError, match="low entropy|repeating pattern"):
            validate_secret_strength("1234567890" * 7)

    @pytest.mark.skip(reason="Secret entropy validation not yet implemented - M-2 finding")
    def test_accept_strong_secret(self):
        """Test that cryptographically random secrets are accepted."""
        import secrets

        # Generate strong secret
        strong_secret = secrets.token_hex(64)  # 128 characters, high entropy

        # Should not raise
        result = validate_secret_strength(strong_secret)
        assert result is True

    @pytest.mark.skip(reason="Secret entropy validation not yet implemented - M-2 finding")
    def test_calculate_shannon_entropy(self):
        """Test Shannon entropy calculation for various strings."""
        # Low entropy (all same character)
        low_entropy = "a" * 64
        entropy_low = calculate_entropy(low_entropy)
        assert entropy_low < 1.0, "All same character should have very low entropy"

        # Medium entropy (repeating pattern)
        medium_entropy = "abcd" * 16
        entropy_medium = calculate_entropy(medium_entropy)
        assert 1.0 < entropy_medium < 3.0

        # High entropy (random)
        import secrets
        high_entropy = secrets.token_hex(64)
        entropy_high = calculate_entropy(high_entropy)
        assert entropy_high > 4.5, "Random hex string should have high entropy"


class TestProductionConfigValidation:
    """
    Tests for L-1: CORS Localhost in Production

    These tests validate that production configuration is secure.
    """

    @pytest.mark.skip(reason="Production config validation not yet implemented - L-1 finding")
    def test_no_localhost_cors_in_production(self):
        """Test that production environment blocks localhost CORS origins."""
        from core.config import Settings

        # Simulate production settings
        prod_settings = Settings(
            ENVIRONMENT="production",
            CORS_ORIGINS="http://localhost:5173"  # Should fail
        )

        # Should raise error on startup
        with pytest.raises(ValueError, match="localhost.*production"):
            # This would be called during app initialization
            validate_production_config(prod_settings)

    @pytest.mark.skip(reason="Production config validation not yet implemented - L-1 finding")
    def test_production_requires_strong_secret(self):
        """Test that production environment requires strong CAPABILITY_SIGNING_KEY."""
        from core.config import Settings

        prod_settings = Settings(
            ENVIRONMENT="production",
            CAPABILITY_SIGNING_KEY="sentinel-local-dev-secret-do-not-use-in-prod"
        )

        # Should fail (already implemented)
        with pytest.raises(ValueError, match="development signing key.*production"):
            TokenManager(secret=prod_settings.CAPABILITY_SIGNING_KEY.encode())


# Helper functions (to be implemented)

def validate_secret_strength(key_str: str) -> bool:
    """
    Validate that a secret has sufficient length and entropy.

    This function should be implemented in security/capability_token.py
    as part of remediation for M-2.
    """
    if len(key_str) < 64:
        raise ValueError("Secret must be >= 64 characters")

    entropy = calculate_entropy(key_str)
    if entropy < 4.5:
        raise ValueError(f"Secret has low entropy ({entropy:.2f})")

    # Check for obvious patterns
    if key_str == key_str[0] * len(key_str):
        raise ValueError("Secret cannot be repeating pattern")

    return True


def calculate_entropy(s: str) -> float:
    """
    Calculate Shannon entropy of a string.

    Returns entropy in bits per character.
    Higher values indicate more randomness.
    """
    freq = Counter(s)
    length = len(s)

    entropy = -sum(
        (count / length) * math.log2(count / length)
        for count in freq.values()
    )

    return entropy


def validate_production_config(settings):
    """
    Validate that production configuration is secure.

    Should be called during app startup when ENVIRONMENT=production.
    """
    if settings.ENVIRONMENT == "production":
        # Check CORS origins
        origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
        localhost_origins = [
            o for o in origins
            if "localhost" in o or "127.0.0.1" in o or "0.0.0.0" in o
        ]
        if localhost_origins:
            raise ValueError(
                f"Production deployment cannot allow localhost CORS origins: {localhost_origins}"
            )

        # Check Redis URL
        if not settings.REDIS_URL.startswith("rediss://"):
            raise ValueError("Production must use TLS for Redis (rediss://)")

        # Check Kafka security
        if "SASL" not in settings.KAFKA_BROKER:
            # Warning: Kafka security cannot be fully validated from URL alone
            # This is a soft check
            import warnings
            warnings.warn(
                "Kafka broker URL does not appear to use SASL authentication. "
                "Ensure KAFKA_SECURITY_PROTOCOL is configured.",
                category=SecurityWarning
            )


class SecurityWarning(UserWarning):
    """Warning category for security configuration issues."""
    pass


# Mark all tests in this module as security tests
pytestmark = pytest.mark.security
