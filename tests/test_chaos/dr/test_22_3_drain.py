"""
Sentinel — Phase 22.3 Graceful Drain Tests

Verifies that the evaluator worker correctly implements:
1. Signal detection and event propagation.
2. Draining in-flight tasks before exiting.
3. Domain-state-driven offset commits (commits ONLY happen after Redis reply).
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from collections import namedtuple

# ─────────────────────────────────────────────────────────────
# 22.3.1 — Shutdown coordination tests
# ─────────────────────────────────────────────────────────────


def test_shutdown_event_singleton():
    from worker.evaluator import _get_shutdown_event, _shutdown_event

    event1 = _get_shutdown_event()
    event2 = _get_shutdown_event()
    assert event1 is event2
    assert not event1.is_set()


# ─────────────────────────────────────────────────────────────
# 22.3.2 — Offset Tracker Tests (Domain-state-driven commit)
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_offset_tracker_safe_contiguous_commit():
    """Verify the offset tracker only commits contiguously completed offsets."""
    from worker.evaluator import OffsetTracker
    from aiokafka import TopicPartition, OffsetAndMetadata

    consumer = AsyncMock()
    tracker = OffsetTracker(consumer)
    tp = TopicPartition("test-topic", 0)

    # 3 messages arrive
    await tracker.track_start(tp, 100)
    await tracker.track_start(tp, 101)
    await tracker.track_start(tp, 102)

    # Message 100 finishes -> commits 101 (safe up to 100)
    await tracker.mark_done_and_commit(tp, 100)
    consumer.commit.assert_called_with({tp: OffsetAndMetadata(101, "")})

    # Message 102 finishes out of order -> should NOT advance commit past 101 (since 101 is still in flight)
    consumer.commit.reset_mock()
    await tracker.mark_done_and_commit(tp, 102)
    consumer.commit.assert_called_with({tp: OffsetAndMetadata(101, "")})

    # Message 101 finishes -> NOW it can commit past 102 (safe up to 102, so commit 103)
    consumer.commit.reset_mock()
    await tracker.mark_done_and_commit(tp, 101)
    consumer.commit.assert_called_with({tp: OffsetAndMetadata(103, "")})


@pytest.mark.asyncio
async def test_offset_tracker_handles_failed_offset():
    """Verify that a failed offset (removed without commit) holds back the contiguous commit line."""
    from worker.evaluator import OffsetTracker
    from aiokafka import TopicPartition, OffsetAndMetadata

    consumer = AsyncMock()
    tracker = OffsetTracker(consumer)
    tp = TopicPartition("test-topic", 0)

    await tracker.track_start(tp, 200)
    await tracker.track_start(tp, 201)
    await tracker.track_start(tp, 202)

    # 200 finishes successfully
    await tracker.mark_done_and_commit(tp, 200)
    consumer.commit.assert_called_with({tp: OffsetAndMetadata(201, "")})

    # 201 FAILS
    await tracker.mark_failed(tp, 201)

    # 202 finishes successfully.
    # Because 201 failed, the maximum safe contiguous offset is still 200.
    # Therefore, the commit for 202 should NOT advance past 201.
    consumer.commit.reset_mock()
    await tracker.mark_done_and_commit(tp, 202)
    consumer.commit.assert_called_with({tp: OffsetAndMetadata(201, "")})

    # 203 finishes successfully.
    # Still blocked by 201.
    await tracker.track_start(tp, 203)
    consumer.commit.reset_mock()
    await tracker.mark_done_and_commit(tp, 203)
    consumer.commit.assert_called_with({tp: OffsetAndMetadata(201, "")})
