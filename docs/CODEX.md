# Sentinel — Codex Engineering Brief

## Objective

Continue development from the current verified Sentinel baseline without redesigning completed architecture.

## Current Product

Sentinel is a zero-trust governance and risk layer for autonomous financial agents.

## Core Principle

No valid Capability Token
→ no Razorpay MCP invocation.

## Verified Integration

Razorpay Remote MCP:
https://mcp.razorpay.com/mcp

Transport:
Streamable HTTP

Python MCP SDK:
2.0.0

Protocol:
2025-06-18

Environment:
Razorpay Test

## Completed Phases

1–17: architecture, backend, ML, frontend, evaluation, MCP integration
18: Production Security Hardening

## Next Phase

Phase 19 — Chaos & Failure Engineering.

## Non-negotiable constraints

- Do not fabricate metrics.
- Do not claim Vulcan integration.
- Do not claim production Razorpay payments.
- Do not bypass ExecutionGateway.
- Do not allow arbitrary MCP tools.
- Do not expose secrets to frontend.
- Preserve existing benchmark methodology.
- Preserve capability-token invariants.
- Preserve real Razorpay Test integration.
- Prefer incremental changes over architecture rewrites.

## Required next work

Chaos test:
- Redis
- PostgreSQL
- Kafka/Redpanda
- ML model
- Policy engine
- Capability signer
- Razorpay MCP

For every failure prove:
safe state
→ no unauthorized capability
→ no unauthorized MCP execution
→ recovery
→ no duplicate execution.
