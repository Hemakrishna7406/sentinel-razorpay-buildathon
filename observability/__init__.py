"""
Sentinel Observability Package

Provides structured logging, Prometheus metrics registry, and OpenTelemetry
tracing utilities. All components are strictly non-authoritative — they observe
the authorization path but never participate in it.

If any observability component raises, it must be caught and suppressed by the
caller. Authorization decisions must never depend on observability availability.
"""
