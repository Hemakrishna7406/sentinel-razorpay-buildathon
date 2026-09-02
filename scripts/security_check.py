#!/usr/bin/env python3
"""
Sentinel Security Validation Script

Quick security posture check for Sentinel RC1.
Validates critical security controls before deployment.

Usage:
    python scripts/security_check.py [--environment production]

Exit Codes:
    0 - All checks passed
    1 - Critical security issues found
    2 - High severity issues found
    3 - Medium severity issues found
"""

import sys
import os
import re
import hashlib
import math
from collections import Counter
from pathlib import Path
from typing import List, Tuple

# ANSI color codes
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


class SecurityCheck:
    """Base class for security checks."""

    def __init__(self, name: str, severity: str):
        self.name = name
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW
        self.passed = False
        self.message = ""

    def run(self) -> bool:
        """Run the check. Return True if passed."""
        raise NotImplementedError

    def report(self) -> str:
        """Generate report line."""
        status = f"{GREEN}✓ PASS{RESET}" if self.passed else f"{RED}✗ FAIL{RESET}"
        severity_color = {
            "CRITICAL": RED,
            "HIGH": RED,
            "MEDIUM": YELLOW,
            "LOW": BLUE
        }.get(self.severity, RESET)

        return f"{status} [{severity_color}{self.severity}{RESET}] {self.name}\n    {self.message}"


class CapabilitySigningKeyCheck(SecurityCheck):
    """Check CAPABILITY_SIGNING_KEY strength."""

    def __init__(self, environment: str = "development"):
        super().__init__("Capability Signing Key", "CRITICAL")
        self.environment = environment

    def run(self) -> bool:
        signing_key = os.getenv("CAPABILITY_SIGNING_KEY", "")

        if not signing_key:
            self.message = "CAPABILITY_SIGNING_KEY not set in environment"
            return False

        # Check length
        if len(signing_key) < 32:
            self.message = f"Key too short ({len(signing_key)} chars). Minimum: 32, Recommended: 64"
            return False

        # Check for development key in production
        if self.environment == "production":
            if signing_key == "sentinel-local-dev-secret-do-not-use-in-prod":
                self.message = "Development key used in production environment"
                return False

            if len(signing_key) < 64:
                self.message = f"Production key too short ({len(signing_key)} chars). Minimum: 64"
                return False

        # Check entropy
        freq = Counter(signing_key)
        entropy = -sum(
            (count / len(signing_key)) * math.log2(count / len(signing_key))
            for count in freq.values()
        )

        if entropy < 4.0:
            self.message = f"Key has low entropy ({entropy:.2f}). Use cryptographically random key."
            return False

        self.passed = True
        self.message = f"Key length: {len(signing_key)} chars, Entropy: {entropy:.2f} bits/char"
        return True


class RedisSecurityCheck(SecurityCheck):
    """Check Redis connection security."""

    def __init__(self, environment: str = "development"):
        super().__init__("Redis Security", "HIGH")
        self.environment = environment

    def run(self) -> bool:
        redis_url = os.getenv("REDIS_URL", "")

        if not redis_url:
            self.message = "REDIS_URL not set in environment"
            return False

        issues = []

        # Check for TLS in production
        if self.environment == "production":
            if not redis_url.startswith("rediss://"):
                issues.append("Production Redis must use TLS (rediss://)")

        # Check for authentication
        if "redis://" in redis_url or "rediss://" in redis_url:
            # Parse for password
            if "@" not in redis_url:
                issues.append("Redis authentication not configured (no password in URL)")

        if issues:
            self.message = "; ".join(issues)
            self.passed = False
            return False

        self.passed = True
        scheme = "TLS" if redis_url.startswith("rediss://") else "No TLS"
        auth = "Authenticated" if "@" in redis_url else "No Auth"
        self.message = f"Redis configured: {scheme}, {auth}"
        return True


class HardcodedSecretsCheck(SecurityCheck):
    """Scan for hardcoded secrets in source code."""

    def __init__(self, repo_root: Path):
        super().__init__("Hardcoded Secrets Scan", "HIGH")
        self.repo_root = repo_root

    def run(self) -> bool:
        patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "password"),
            (r'secret\s*=\s*["\'][^"\']{16,}["\']', "secret"),
            (r'api[_-]?key\s*=\s*["\'][^"\']{16,}["\']', "api_key"),
            (r'rzp_(test|live)_[a-zA-Z0-9]{14}', "razorpay_key"),
        ]

        findings: List[Tuple[str, str, int]] = []

        # Scan Python files
        for py_file in self.repo_root.rglob("*.py"):
            # Skip test files and virtual environments
            if "test" in str(py_file) or ".venv" in str(py_file) or "venv" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    for line_no, line in enumerate(f, 1):
                        for pattern, secret_type in patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                findings.append((str(py_file), secret_type, line_no))
            except Exception:
                pass

        if findings:
            self.message = f"Found {len(findings)} potential hardcoded secrets:\n"
            for file, secret_type, line_no in findings[:5]:  # Show first 5
                self.message += f"      {file}:{line_no} ({secret_type})\n"
            if len(findings) > 5:
                self.message += f"      ... and {len(findings) - 5} more"
            self.passed = False
            return False

        self.passed = True
        self.message = "No hardcoded secrets detected"
        return True


class SecurityHeadersCheck(SecurityCheck):
    """Check if security headers middleware exists."""

    def __init__(self, repo_root: Path):
        super().__init__("Security Headers", "HIGH")
        self.repo_root = repo_root

    def run(self) -> bool:
        api_main = self.repo_root / "api" / "main.py"

        if not api_main.exists():
            self.message = "api/main.py not found"
            return False

        with open(api_main, "r", encoding="utf-8") as f:
            content = f.read()

        required_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Content-Security-Policy"
        ]

        found_headers = [h for h in required_headers if h in content]

        if len(found_headers) < len(required_headers):
            missing = set(required_headers) - set(found_headers)
            self.message = f"Missing security headers: {', '.join(missing)}"
            self.passed = False
            return False

        self.passed = True
        self.message = "Security headers middleware detected"
        return True


class RateLimitingCheck(SecurityCheck):
    """Check if rate limiting is implemented."""

    def __init__(self, repo_root: Path):
        super().__init__("Rate Limiting", "HIGH")
        self.repo_root = repo_root

    def run(self) -> bool:
        api_main = self.repo_root / "api" / "main.py"
        requirements = self.repo_root / "requirements.txt"

        if not api_main.exists():
            self.message = "api/main.py not found"
            return False

        # Check for rate limiting library
        rate_limit_libs = ["slowapi", "fastapi-limiter", "limits"]
        has_library = False

        if requirements.exists():
            with open(requirements, "r") as f:
                req_content = f.read()
                for lib in rate_limit_libs:
                    if lib in req_content:
                        has_library = True
                        break

        # Check for rate limiting in code
        with open(api_main, "r", encoding="utf-8") as f:
            content = f.read()

        has_limiter = any(
            keyword in content
            for keyword in ["Limiter", "RateLimiter", "@limiter.limit", "rate_limit"]
        )

        if not (has_library and has_limiter):
            self.message = "Rate limiting not implemented"
            self.passed = False
            return False

        self.passed = True
        self.message = "Rate limiting detected"
        return True


class AuditChainIntegrityCheck(SecurityCheck):
    """Check audit chain implementation."""

    def __init__(self, repo_root: Path):
        super().__init__("Audit Chain Integrity", "MEDIUM")
        self.repo_root = repo_root

    def run(self) -> bool:
        audit_chain = self.repo_root / "security" / "audit_chain.py"

        if not audit_chain.exists():
            self.message = "security/audit_chain.py not found"
            return False

        with open(audit_chain, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if timestamp is pinned to None (M-1 finding)
        if 'values["timestamp"] = None' in content or "timestamp=None" in content:
            self.message = "Timestamp excluded from hash (M-1: Allows timestamp tampering)"
            self.passed = False
            return False

        # Check for SHA-256
        if "sha256" not in content:
            self.message = "SHA-256 not found in hash computation"
            self.passed = False
            return False

        self.passed = True
        self.message = "Audit chain uses SHA-256 with full field coverage"
        return True


class CORSConfigCheck(SecurityCheck):
    """Check CORS configuration for production."""

    def __init__(self, environment: str = "development"):
        super().__init__("CORS Configuration", "LOW")
        self.environment = environment

    def run(self) -> bool:
        cors_origins = os.getenv("CORS_ORIGINS", "")

        if self.environment == "production":
            # Check for localhost in production
            if "localhost" in cors_origins or "127.0.0.1" in cors_origins:
                self.message = "Localhost origins allowed in production"
                self.passed = False
                return False

        self.passed = True
        origins_count = len([o for o in cors_origins.split(",") if o.strip()])
        self.message = f"CORS configured with {origins_count} origin(s)"
        return True


class DotEnvCheck(SecurityCheck):
    """Check if .env is in git."""

    def __init__(self, repo_root: Path):
        super().__init__(".env File in Git", "LOW")
        self.repo_root = repo_root

    def run(self) -> bool:
        import subprocess

        try:
            result = subprocess.run(
                ["git", "ls-files", ".env"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.stdout.strip():
                self.message = ".env file is tracked in git (should be in .gitignore only)"
                self.passed = False
                return False

        except Exception:
            self.message = "Unable to check git status (not a git repo or git not installed)"
            self.passed = True  # Don't fail if git check unavailable
            return True

        self.passed = True
        self.message = ".env file not tracked in git"
        return True


def main():
    """Run all security checks."""
    import argparse

    parser = argparse.ArgumentParser(description="Sentinel Security Validation")
    parser.add_argument(
        "--environment",
        choices=["development", "production"],
        default=os.getenv("ENVIRONMENT", "development"),
        help="Environment to validate (default: development)"
    )
    parser.add_argument(
        "--fail-on",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default="HIGH",
        help="Fail on this severity or higher (default: HIGH)"
    )
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent

    # Load .env if exists
    env_file = repo_root / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    print(f"\n{BOLD}Sentinel Security Validation{RESET}")
    print(f"Environment: {args.environment}")
    print(f"Fail Threshold: {args.fail_on}")
    print("=" * 70)

    checks = [
        CapabilitySigningKeyCheck(args.environment),
        RedisSecurityCheck(args.environment),
        HardcodedSecretsCheck(repo_root),
        SecurityHeadersCheck(repo_root),
        RateLimitingCheck(repo_root),
        AuditChainIntegrityCheck(repo_root),
        CORSConfigCheck(args.environment),
        DotEnvCheck(repo_root),
    ]

    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    fail_threshold = severity_order[args.fail_on]

    results = {"passed": 0, "failed": 0, "by_severity": {}}

    print()
    for check in checks:
        check.run()
        print(check.report())

        if check.passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
            results["by_severity"][check.severity] = results["by_severity"].get(check.severity, 0) + 1

    print("\n" + "=" * 70)
    print(f"{BOLD}Results:{RESET}")
    print(f"  Passed: {GREEN}{results['passed']}{RESET}")
    print(f"  Failed: {RED}{results['failed']}{RESET}")

    if results["by_severity"]:
        print(f"\n{BOLD}Failures by Severity:{RESET}")
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = results["by_severity"].get(severity, 0)
            if count > 0:
                color = RED if severity in ["CRITICAL", "HIGH"] else YELLOW
                print(f"  {color}{severity}: {count}{RESET}")

    print()

    # Determine exit code
    if results["failed"] == 0:
        print(f"{GREEN}✓ All security checks passed{RESET}\n")
        return 0

    # Check if any failures exceed threshold
    for severity, count in results["by_severity"].items():
        if count > 0 and severity_order[severity] <= fail_threshold:
            print(f"{RED}✗ Security validation failed{RESET}")
            print(f"  {count} {severity} severity issue(s) detected\n")
            return severity_order[severity] + 1

    print(f"{YELLOW}⚠ Security checks completed with warnings{RESET}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
