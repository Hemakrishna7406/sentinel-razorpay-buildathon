"""
Sentinel Analytics Pipeline

Processes audit log data and generates aggregated business metrics.
Runs as a scheduled job (hourly/daily) to populate analytics tables.

Usage:
    python -m analytics.pipeline --period hourly
    python -m analytics.pipeline --period daily
"""

import datetime
import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import statistics

from sqlalchemy import create_engine, text, select, func
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from core.config import settings
from db.models import AuditRecord

logger = logging.getLogger(__name__)


class AnalyticsPipeline:
    """Aggregates audit log data into business intelligence metrics."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.engine = create_engine(
            self.database_url, poolclass=NullPool, echo=False  # Analytics jobs don't need connection pooling
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

    def run_hourly_aggregation(self, target_hour: Optional[datetime.datetime] = None) -> Dict:
        """
        Aggregate metrics for the specified hour (or previous hour if not specified).

        Returns summary of aggregated metrics.
        """
        if target_hour is None:
            # Default to previous complete hour
            now = datetime.datetime.utcnow()
            target_hour = now.replace(minute=0, second=0, microsecond=0) - datetime.timedelta(hours=1)

        logger.info(f"Starting hourly aggregation for {target_hour}")

        with self.SessionLocal() as session:
            # Define time range
            start_time = target_hour
            end_time = target_hour + datetime.timedelta(hours=1)

            # Fetch audit records for this hour
            records = (
                session.query(AuditRecord)
                .filter(AuditRecord.timestamp >= start_time, AuditRecord.timestamp < end_time)
                .all()
            )

            if not records:
                logger.info(f"No records found for {target_hour}")
                return {"status": "no_data", "period": target_hour}

            # Aggregate decisions
            decisions_metrics = self._aggregate_decisions(records, target_hour, "hour")
            self._upsert_decisions_aggregated(session, decisions_metrics)

            # Aggregate per-agent metrics
            agent_metrics = self._aggregate_agent_metrics(records, target_hour, "hour")
            for metrics in agent_metrics:
                self._upsert_agent_metrics(session, metrics)

            # Detect and log fraud events
            fraud_events = self._detect_fraud_events(records)
            for event in fraud_events:
                self._insert_fraud_event(session, event)

            # Detect policy violations
            violations = self._detect_policy_violations(records)
            for violation in violations:
                self._insert_policy_violation(session, violation)

            # Detect anomalies
            anomalies = self._detect_anomalies(session, records, target_hour)
            for anomaly in anomalies:
                self._insert_anomaly(session, anomaly)

            session.commit()

            summary = {
                "status": "success",
                "period": target_hour,
                "records_processed": len(records),
                "agents": len(agent_metrics),
                "fraud_events": len(fraud_events),
                "violations": len(violations),
                "anomalies": len(anomalies),
            }

            logger.info(f"Hourly aggregation complete: {summary}")
            return summary

    def run_daily_aggregation(self, target_date: Optional[datetime.date] = None) -> Dict:
        """
        Aggregate metrics for the specified date (or previous date if not specified).

        Returns summary of aggregated metrics.
        """
        if target_date is None:
            target_date = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).date()

        logger.info(f"Starting daily aggregation for {target_date}")

        with self.SessionLocal() as session:
            # Define time range
            start_time = datetime.datetime.combine(target_date, datetime.time.min)
            end_time = datetime.datetime.combine(target_date, datetime.time.max)

            # Fetch audit records for this day
            records = (
                session.query(AuditRecord)
                .filter(AuditRecord.timestamp >= start_time, AuditRecord.timestamp <= end_time)
                .all()
            )

            if not records:
                logger.info(f"No records found for {target_date}")
                return {"status": "no_data", "date": str(target_date)}

            # Aggregate decisions (daily)
            decisions_metrics = self._aggregate_decisions(
                records, datetime.datetime.combine(target_date, datetime.time.min), "day"
            )
            self._upsert_decisions_aggregated(session, decisions_metrics)

            # Aggregate per-agent metrics (daily)
            agent_metrics = self._aggregate_agent_metrics(
                records, datetime.datetime.combine(target_date, datetime.time.min), "day"
            )
            for metrics in agent_metrics:
                self._upsert_agent_metrics(session, metrics)

            # Financial metrics (daily only)
            financial_metrics = self._aggregate_financial_metrics(records, target_date)
            self._upsert_financial_metrics(session, financial_metrics)

            session.commit()

            summary = {
                "status": "success",
                "date": str(target_date),
                "records_processed": len(records),
                "agents": len(agent_metrics),
                "total_value": financial_metrics.get("total_value_processed", 0),
            }

            logger.info(f"Daily aggregation complete: {summary}")
            return summary

    def _aggregate_decisions(self, records: List[AuditRecord], period: datetime.datetime, period_type: str) -> Dict:
        """Aggregate decision-level metrics."""
        metrics = {
            "aggregation_period": period,
            "period_type": period_type,
            "total_decisions": len(records),
            "allow_count": 0,
            "escalate_count": 0,
            "contain_count": 0,
            "total_value": 0,
            "allow_value": 0,
            "escalate_value": 0,
            "contain_value": 0,
            "prevented_fraud_value": 0,
            "high_risk_count": 0,
            "medium_risk_count": 0,
            "low_risk_count": 0,
            "fusion_disagreement_count": 0,
        }

        risk_scores = []
        behavioral_risks = []
        semantic_risks = []

        for record in records:
            # Decision counts
            decision = record.decision.upper()
            amount = record.amount

            if decision == "ALLOW":
                metrics["allow_count"] += 1
                metrics["allow_value"] += amount
            elif decision == "ESCALATE":
                metrics["escalate_count"] += 1
                metrics["escalate_value"] += amount
            elif decision == "CONTAIN":
                metrics["contain_count"] += 1
                metrics["contain_value"] += amount
                metrics["prevented_fraud_value"] += amount  # Assume CONTAIN = prevented fraud

            metrics["total_value"] += amount

            # Risk categorization
            if record.model_risk_score is not None:
                risk_scores.append(record.model_risk_score)
                if record.model_risk_score >= 0.7:
                    metrics["high_risk_count"] += 1
                elif record.model_risk_score >= 0.4:
                    metrics["medium_risk_count"] += 1
                else:
                    metrics["low_risk_count"] += 1

            if record.behavioral_risk_score is not None:
                behavioral_risks.append(record.behavioral_risk_score)

            if record.semantic_risk_score is not None:
                semantic_risks.append(record.semantic_risk_score)

            # Fusion disagreement
            if record.fusion_disagreement == "true":
                metrics["fusion_disagreement_count"] += 1

        # Statistical metrics
        if risk_scores:
            metrics["avg_risk_score"] = statistics.mean(risk_scores)
            metrics["max_risk_score"] = max(risk_scores)
            metrics["min_risk_score"] = min(risk_scores)

        if behavioral_risks:
            metrics["avg_behavioral_risk"] = statistics.mean(behavioral_risks)

        if semantic_risks:
            metrics["avg_semantic_risk"] = statistics.mean(semantic_risks)

        return metrics

    def _aggregate_agent_metrics(
        self, records: List[AuditRecord], period: datetime.datetime, period_type: str
    ) -> List[Dict]:
        """Aggregate per-agent metrics."""
        agent_data = defaultdict(
            lambda: {
                "agent_id": None,
                "aggregation_period": period,
                "period_type": period_type,
                "total_transactions": 0,
                "total_value": 0,
                "allow_count": 0,
                "escalate_count": 0,
                "contain_count": 0,
                "risk_scores": [],
                "recipients": set(),
                "action_types": set(),
                "transaction_times": [],
                "policy_violations": 0,
            }
        )

        for record in records:
            agent_id = record.agent_id
            data = agent_data[agent_id]
            data["agent_id"] = agent_id

            # Basic counts
            data["total_transactions"] += 1
            data["total_value"] += record.amount

            # Decision breakdown
            decision = record.decision.upper()
            if decision == "ALLOW":
                data["allow_count"] += 1
            elif decision == "ESCALATE":
                data["escalate_count"] += 1
            elif decision == "CONTAIN":
                data["contain_count"] += 1

            # Risk scores
            if record.model_risk_score is not None:
                data["risk_scores"].append(record.model_risk_score)

            # Behavioral tracking
            data["recipients"].add(record.recipient)
            data["action_types"].add(record.action_type)
            data["transaction_times"].append(record.timestamp.time())

            # Policy violations (heuristic: high risk CONTAIN decisions)
            if decision == "CONTAIN" and record.model_risk_score and record.model_risk_score >= 0.8:
                data["policy_violations"] += 1

        # Convert to list of metrics
        agent_metrics = []
        for agent_id, data in agent_data.items():
            metrics = {
                "agent_id": agent_id,
                "aggregation_period": period,
                "period_type": period_type,
                "total_transactions": data["total_transactions"],
                "total_value": data["total_value"],
                "avg_transaction_value": (
                    data["total_value"] // data["total_transactions"] if data["total_transactions"] > 0 else 0
                ),
                "allow_count": data["allow_count"],
                "escalate_count": data["escalate_count"],
                "contain_count": data["contain_count"],
                "unique_recipients": len(data["recipients"]),
                "unique_action_types": len(data["action_types"]),
                "policy_violations": data["policy_violations"],
            }

            # Risk statistics
            if data["risk_scores"]:
                metrics["avg_risk_score"] = statistics.mean(data["risk_scores"])
                metrics["max_risk_score"] = max(data["risk_scores"])

            # Activity patterns
            if data["transaction_times"]:
                times = data["transaction_times"]
                metrics["first_transaction_time"] = min(times)
                metrics["last_transaction_time"] = max(times)

                # Peak hour
                hour_counts = defaultdict(int)
                for t in times:
                    hour_counts[t.hour] += 1
                metrics["peak_hour"] = max(hour_counts, key=hour_counts.get)

            agent_metrics.append(metrics)

        return agent_metrics

    def _aggregate_financial_metrics(self, records: List[AuditRecord], date: datetime.date) -> Dict:
        """Aggregate financial metrics for a day."""
        metrics = {
            "date": date,
            "total_value_processed": 0,
            "total_transactions": len(records),
            "allowed_value": 0,
            "escalated_value": 0,
            "contained_value": 0,
            "fraud_attempts_detected": 0,
            "fraud_value_prevented": 0,
            "authorization_count": len(records),
        }

        for record in records:
            amount = record.amount
            decision = record.decision.upper()

            metrics["total_value_processed"] += amount

            if decision == "ALLOW":
                metrics["allowed_value"] += amount
            elif decision == "ESCALATE":
                metrics["escalated_value"] += amount
            elif decision == "CONTAIN":
                metrics["contained_value"] += amount
                metrics["fraud_attempts_detected"] += 1
                metrics["fraud_value_prevented"] += amount

        # Calculate derived metrics
        if metrics["total_transactions"] > 0:
            metrics["avg_transaction_value"] = metrics["total_value_processed"] // metrics["total_transactions"]

        # Cost analysis (configurable per deployment)
        cost_per_auth = 0.01  # $0.01 per authorization (default)
        metrics["cost_per_authorization"] = cost_per_auth
        metrics["total_operational_cost"] = metrics["authorization_count"] * cost_per_auth

        # ROI calculation
        # Convert fraud prevented from paise to USD (rough estimate: 1 USD = 80 INR = 8000 paise)
        fraud_prevented_usd = metrics["fraud_value_prevented"] / 8000.0
        metrics["fraud_prevention_savings"] = metrics["fraud_value_prevented"]
        metrics["net_value"] = fraud_prevented_usd - metrics["total_operational_cost"]

        if metrics["total_operational_cost"] > 0:
            metrics["roi_percentage"] = (metrics["net_value"] / metrics["total_operational_cost"]) * 100

        return metrics

    def _detect_fraud_events(self, records: List[AuditRecord]) -> List[Dict]:
        """Identify fraud events from CONTAIN decisions."""
        fraud_events = []

        for record in records:
            if record.decision.upper() == "CONTAIN":
                event = {
                    "intent_id": record.intent_id,
                    "detected_at": record.timestamp,
                    "agent_id": record.agent_id,
                    "action_type": record.action_type,
                    "amount": record.amount,
                    "currency": record.currency,
                    "recipient": record.recipient,
                    "risk_score": record.model_risk_score,
                    "behavioral_risk": record.behavioral_risk_score,
                    "semantic_risk": record.semantic_risk_score,
                    "fraud_type": self._classify_fraud_type(record),
                    "detection_method": "ml",
                    "decision": record.decision,
                    "decision_reason": record.decision_reason,
                    "prevented_loss": record.amount,
                    "investigated": False,
                }
                fraud_events.append(event)

        return fraud_events

    def _classify_fraud_type(self, record: AuditRecord) -> str:
        """Classify fraud type based on risk scores and reason."""
        reason = record.decision_reason.lower()

        if "velocity" in reason or "frequent" in reason:
            return "velocity"
        elif "anomaly" in reason or "unusual" in reason:
            return "anomaly"
        elif "policy" in reason:
            return "policy"
        else:
            return "pattern"

    def _detect_policy_violations(self, records: List[AuditRecord]) -> List[Dict]:
        """Detect policy violations from records."""
        violations = []

        for record in records:
            # Heuristic: ESCALATE or CONTAIN decisions with policy mentions
            reason = record.decision_reason.lower()
            decision = record.decision.upper()

            if decision in ["ESCALATE", "CONTAIN"] and "policy" in reason:
                violation = {
                    "intent_id": record.intent_id,
                    "violated_at": record.timestamp,
                    "policy_rule": self._extract_policy_rule(record.decision_reason),
                    "violation_type": self._classify_violation_type(record),
                    "severity": self._classify_severity(record),
                    "agent_id": record.agent_id,
                    "action_type": record.action_type,
                    "amount": record.amount,
                    "action_taken": "blocked" if decision == "CONTAIN" else "escalated",
                    "resolved": False,
                }
                violations.append(violation)

        return violations

    def _extract_policy_rule(self, reason: str) -> str:
        """Extract policy rule name from decision reason."""
        # Simple extraction - could be enhanced with NLP
        if "high-value" in reason.lower():
            return "high_value_threshold"
        elif "frequency" in reason.lower():
            return "transaction_frequency"
        elif "amount" in reason.lower():
            return "amount_threshold"
        else:
            return "unknown_policy"

    def _classify_violation_type(self, record: AuditRecord) -> str:
        """Classify violation type."""
        if record.amount > 1000000:  # > ₹10,000
            return "threshold"
        elif record.behavioral_risk_score and record.behavioral_risk_score > 0.7:
            return "velocity"
        else:
            return "pattern"

    def _classify_severity(self, record: AuditRecord) -> str:
        """Classify violation severity."""
        if record.model_risk_score and record.model_risk_score >= 0.9:
            return "critical"
        elif record.model_risk_score and record.model_risk_score >= 0.7:
            return "high"
        elif record.model_risk_score and record.model_risk_score >= 0.5:
            return "medium"
        else:
            return "low"

    def _detect_anomalies(self, session: Session, records: List[AuditRecord], period: datetime.datetime) -> List[Dict]:
        """Detect anomalies in transaction patterns."""
        anomalies = []

        # Volume anomaly: Compare to historical average
        current_volume = len(records)
        historical_avg = self._get_historical_average_volume(session, period)

        if historical_avg and current_volume > historical_avg * 2:  # 2x spike
            anomalies.append(
                {
                    "detected_at": period,
                    "anomaly_type": "volume",
                    "severity": "high" if current_volume > historical_avg * 3 else "medium",
                    "entity_type": "system",
                    "entity_id": None,
                    "description": f"Transaction volume spike: {current_volume} vs average {historical_avg:.0f}",
                    "baseline_value": historical_avg,
                    "current_value": float(current_volume),
                    "deviation_score": (current_volume - historical_avg) / historical_avg if historical_avg > 0 else 0,
                    "affected_intents": current_volume,
                    "alerted": False,
                    "acknowledged": False,
                }
            )

        return anomalies

    def _get_historical_average_volume(self, session: Session, period: datetime.datetime) -> Optional[float]:
        """Get historical average transaction volume for comparison."""
        try:
            # Look back 7 days, same hour
            lookback_start = period - datetime.timedelta(days=7)

            result = session.execute(
                text("""
                    SELECT AVG(total_decisions)
                    FROM decisions_aggregated
                    WHERE aggregation_period >= :start
                    AND aggregation_period < :end
                    AND period_type = 'hour'
                """),
                {"start": lookback_start, "end": period},
            ).scalar()

            return float(result) if result else None
        except Exception as e:
            logger.warning(f"Could not fetch historical average: {e}")
            return None

    def _upsert_decisions_aggregated(self, session: Session, metrics: Dict):
        """Insert or update decisions_aggregated table."""
        session.execute(
            text("""
                INSERT INTO decisions_aggregated (
                    aggregation_period, period_type, total_decisions,
                    allow_count, escalate_count, contain_count,
                    total_value, allow_value, escalate_value, contain_value,
                    prevented_fraud_value, avg_risk_score, max_risk_score, min_risk_score,
                    high_risk_count, medium_risk_count, low_risk_count,
                    fusion_disagreement_count, avg_behavioral_risk, avg_semantic_risk
                ) VALUES (
                    :aggregation_period, :period_type, :total_decisions,
                    :allow_count, :escalate_count, :contain_count,
                    :total_value, :allow_value, :escalate_value, :contain_value,
                    :prevented_fraud_value, :avg_risk_score, :max_risk_score, :min_risk_score,
                    :high_risk_count, :medium_risk_count, :low_risk_count,
                    :fusion_disagreement_count, :avg_behavioral_risk, :avg_semantic_risk
                )
                ON CONFLICT (aggregation_period, period_type)
                DO UPDATE SET
                    total_decisions = EXCLUDED.total_decisions,
                    allow_count = EXCLUDED.allow_count,
                    escalate_count = EXCLUDED.escalate_count,
                    contain_count = EXCLUDED.contain_count,
                    total_value = EXCLUDED.total_value,
                    allow_value = EXCLUDED.allow_value,
                    escalate_value = EXCLUDED.escalate_value,
                    contain_value = EXCLUDED.contain_value,
                    prevented_fraud_value = EXCLUDED.prevented_fraud_value,
                    avg_risk_score = EXCLUDED.avg_risk_score,
                    max_risk_score = EXCLUDED.max_risk_score,
                    min_risk_score = EXCLUDED.min_risk_score,
                    high_risk_count = EXCLUDED.high_risk_count,
                    medium_risk_count = EXCLUDED.medium_risk_count,
                    low_risk_count = EXCLUDED.low_risk_count,
                    fusion_disagreement_count = EXCLUDED.fusion_disagreement_count,
                    avg_behavioral_risk = EXCLUDED.avg_behavioral_risk,
                    avg_semantic_risk = EXCLUDED.avg_semantic_risk,
                    updated_at = CURRENT_TIMESTAMP
            """),
            metrics,
        )

    def _upsert_agent_metrics(self, session: Session, metrics: Dict):
        """Insert or update agent_metrics table."""
        session.execute(
            text("""
                INSERT INTO agent_metrics (
                    agent_id, aggregation_period, period_type,
                    total_transactions, total_value, avg_transaction_value,
                    allow_count, escalate_count, contain_count,
                    avg_risk_score, max_risk_score,
                    unique_recipients, unique_action_types,
                    policy_violations, first_transaction_time,
                    last_transaction_time, peak_hour
                ) VALUES (
                    :agent_id, :aggregation_period, :period_type,
                    :total_transactions, :total_value, :avg_transaction_value,
                    :allow_count, :escalate_count, :contain_count,
                    :avg_risk_score, :max_risk_score,
                    :unique_recipients, :unique_action_types,
                    :policy_violations, :first_transaction_time,
                    :last_transaction_time, :peak_hour
                )
                ON CONFLICT (agent_id, aggregation_period, period_type)
                DO UPDATE SET
                    total_transactions = EXCLUDED.total_transactions,
                    total_value = EXCLUDED.total_value,
                    avg_transaction_value = EXCLUDED.avg_transaction_value,
                    allow_count = EXCLUDED.allow_count,
                    escalate_count = EXCLUDED.escalate_count,
                    contain_count = EXCLUDED.contain_count,
                    avg_risk_score = EXCLUDED.avg_risk_score,
                    max_risk_score = EXCLUDED.max_risk_score,
                    unique_recipients = EXCLUDED.unique_recipients,
                    unique_action_types = EXCLUDED.unique_action_types,
                    policy_violations = EXCLUDED.policy_violations,
                    first_transaction_time = EXCLUDED.first_transaction_time,
                    last_transaction_time = EXCLUDED.last_transaction_time,
                    peak_hour = EXCLUDED.peak_hour,
                    updated_at = CURRENT_TIMESTAMP
            """),
            metrics,
        )

    def _upsert_financial_metrics(self, session: Session, metrics: Dict):
        """Insert or update financial_metrics table."""
        session.execute(
            text("""
                INSERT INTO financial_metrics (
                    date, total_value_processed, total_transactions, avg_transaction_value,
                    allowed_value, escalated_value, contained_value,
                    fraud_attempts_detected, fraud_value_prevented,
                    authorization_count, cost_per_authorization, total_operational_cost,
                    fraud_prevention_savings, net_value, roi_percentage
                ) VALUES (
                    :date, :total_value_processed, :total_transactions, :avg_transaction_value,
                    :allowed_value, :escalated_value, :contained_value,
                    :fraud_attempts_detected, :fraud_value_prevented,
                    :authorization_count, :cost_per_authorization, :total_operational_cost,
                    :fraud_prevention_savings, :net_value, :roi_percentage
                )
                ON CONFLICT (date)
                DO UPDATE SET
                    total_value_processed = EXCLUDED.total_value_processed,
                    total_transactions = EXCLUDED.total_transactions,
                    avg_transaction_value = EXCLUDED.avg_transaction_value,
                    allowed_value = EXCLUDED.allowed_value,
                    escalated_value = EXCLUDED.escalated_value,
                    contained_value = EXCLUDED.contained_value,
                    fraud_attempts_detected = EXCLUDED.fraud_attempts_detected,
                    fraud_value_prevented = EXCLUDED.fraud_value_prevented,
                    authorization_count = EXCLUDED.authorization_count,
                    total_operational_cost = EXCLUDED.total_operational_cost,
                    fraud_prevention_savings = EXCLUDED.fraud_prevention_savings,
                    net_value = EXCLUDED.net_value,
                    roi_percentage = EXCLUDED.roi_percentage,
                    updated_at = CURRENT_TIMESTAMP
            """),
            metrics,
        )

    def _insert_fraud_event(self, session: Session, event: Dict):
        """Insert fraud event (skip if duplicate)."""
        try:
            session.execute(
                text("""
                    INSERT INTO fraud_events (
                        intent_id, detected_at, agent_id, action_type, amount, currency,
                        recipient, risk_score, behavioral_risk, semantic_risk,
                        fraud_type, detection_method, decision, decision_reason,
                        prevented_loss, investigated
                    ) VALUES (
                        :intent_id, :detected_at, :agent_id, :action_type, :amount, :currency,
                        :recipient, :risk_score, :behavioral_risk, :semantic_risk,
                        :fraud_type, :detection_method, :decision, :decision_reason,
                        :prevented_loss, :investigated
                    )
                    ON CONFLICT (intent_id) DO NOTHING
                """),
                event,
            )
        except Exception as e:
            logger.warning(f"Could not insert fraud event: {e}")

    def _insert_policy_violation(self, session: Session, violation: Dict):
        """Insert policy violation."""
        try:
            session.execute(
                text("""
                    INSERT INTO policy_violations (
                        intent_id, violated_at, policy_rule, violation_type, severity,
                        agent_id, action_type, amount, action_taken, resolved
                    ) VALUES (
                        :intent_id, :violated_at, :policy_rule, :violation_type, :severity,
                        :agent_id, :action_type, :amount, :action_taken, :resolved
                    )
                """),
                violation,
            )
        except Exception as e:
            logger.warning(f"Could not insert policy violation: {e}")

    def _insert_anomaly(self, session: Session, anomaly: Dict):
        """Insert anomaly detection."""
        try:
            session.execute(
                text("""
                    INSERT INTO anomaly_detections (
                        detected_at, anomaly_type, severity, entity_type, entity_id,
                        description, baseline_value, current_value, deviation_score,
                        affected_intents, alerted, acknowledged
                    ) VALUES (
                        :detected_at, :anomaly_type, :severity, :entity_type, :entity_id,
                        :description, :baseline_value, :current_value, :deviation_score,
                        :affected_intents, :alerted, :acknowledged
                    )
                """),
                anomaly,
            )
        except Exception as e:
            logger.warning(f"Could not insert anomaly: {e}")


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser(description="Run Sentinel Analytics Pipeline")
    parser.add_argument(
        "--period", choices=["hourly", "daily"], required=True, help="Aggregation period (hourly or daily)"
    )
    parser.add_argument("--target", type=str, help="Target hour/date (ISO format). Defaults to previous period.")

    args = parser.parse_args()

    pipeline = AnalyticsPipeline()

    if args.period == "hourly":
        target_hour = datetime.datetime.fromisoformat(args.target) if args.target else None
        result = pipeline.run_hourly_aggregation(target_hour)
    else:
        target_date = datetime.date.fromisoformat(args.target) if args.target else None
        result = pipeline.run_daily_aggregation(target_date)

    print(f"Analytics pipeline completed: {result}")
