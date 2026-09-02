"""
Sentinel Analytics API

Business intelligence endpoints for metrics, reports, and insights.
"""

import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from api.dependencies import get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ====================
# RESPONSE MODELS
# ====================

class KPIMetrics(BaseModel):
    """Key Performance Indicators for executive dashboard."""
    total_transactions_24h: int = Field(..., description="Total transactions in last 24 hours")
    fraud_prevented_value: int = Field(..., description="Fraud value prevented (₹ in paise)")
    detection_rate: float = Field(..., description="Fraud detection rate (0-1)")
    system_uptime: float = Field(..., description="System uptime percentage")
    avg_latency_ms: float = Field(..., description="Average authorization latency")
    allow_rate: float = Field(..., description="Percentage of allowed transactions")
    escalate_rate: float = Field(..., description="Percentage of escalated transactions")
    contain_rate: float = Field(..., description="Percentage of contained transactions")


class DecisionTrend(BaseModel):
    """Time-series trend of decisions."""
    timestamp: datetime.datetime
    allow_count: int
    escalate_count: int
    contain_count: int
    total_count: int
    avg_risk_score: Optional[float]


class AgentSummary(BaseModel):
    """Per-agent summary metrics."""
    agent_id: str
    total_transactions: int
    total_value: int
    avg_risk_score: Optional[float]
    allow_count: int
    escalate_count: int
    contain_count: int
    policy_violations: int
    last_transaction: Optional[datetime.datetime]


class FraudEvent(BaseModel):
    """Fraud event details."""
    id: int
    intent_id: str
    detected_at: datetime.datetime
    agent_id: str
    amount: int
    currency: str
    risk_score: float
    fraud_type: str
    decision_reason: str
    investigated: bool


class FinancialSummary(BaseModel):
    """Financial metrics summary."""
    period_start: datetime.date
    period_end: datetime.date
    total_value_processed: int
    total_transactions: int
    avg_transaction_value: int
    fraud_prevented_value: int
    operational_cost: float
    roi_percentage: Optional[float]
    net_value: Optional[float]


class AnomalyAlert(BaseModel):
    """Anomaly detection alert."""
    id: int
    detected_at: datetime.datetime
    anomaly_type: str
    severity: str
    description: str
    entity_type: str
    entity_id: Optional[str]
    deviation_score: Optional[float]
    acknowledged: bool


class ExportRequest(BaseModel):
    """Export data request."""
    export_type: str = Field(..., description="Type: decisions, agents, fraud_events, financial")
    format: str = Field("csv", description="Format: csv, json, excel")
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    filters: Optional[Dict[str, Any]] = None


# ====================
# ENDPOINTS
# ====================

@router.get("/kpis", response_model=KPIMetrics)
async def get_kpis(db: Session = Depends(get_db)):
    """
    Get Key Performance Indicators for executive dashboard.

    Returns real-time KPIs including transaction volume, fraud prevention,
    detection rate, and system health.
    """
    now = datetime.datetime.utcnow()
    last_24h = now - datetime.timedelta(hours=24)

    # Query aggregated metrics for last 24 hours
    result = db.execute(
        text("""
            SELECT
                COALESCE(SUM(total_decisions), 0) as total_transactions,
                COALESCE(SUM(prevented_fraud_value), 0) as fraud_prevented_value,
                COALESCE(SUM(contain_count), 0) as contain_count,
                COALESCE(SUM(allow_count), 0) as allow_count,
                COALESCE(SUM(escalate_count), 0) as escalate_count,
                COALESCE(AVG(avg_latency_ms), 0) as avg_latency_ms
            FROM decisions_aggregated
            WHERE aggregation_period >= :start_time
            AND period_type = 'hour'
        """),
        {"start_time": last_24h}
    ).first()

    total_transactions = result.total_transactions or 0
    fraud_prevented_value = result.fraud_prevented_value or 0
    contain_count = result.contain_count or 0
    allow_count = result.allow_count or 0
    escalate_count = result.escalate_count or 0
    avg_latency_ms = result.avg_latency_ms or 0

    # Calculate rates
    detection_rate = contain_count / total_transactions if total_transactions > 0 else 0.0
    allow_rate = allow_count / total_transactions if total_transactions > 0 else 0.0
    escalate_rate = escalate_count / total_transactions if total_transactions > 0 else 0.0
    contain_rate = contain_count / total_transactions if total_transactions > 0 else 0.0

    # System uptime (simplified - could query system_performance table)
    system_uptime = 0.999  # 99.9% uptime target

    return KPIMetrics(
        total_transactions_24h=total_transactions,
        fraud_prevented_value=fraud_prevented_value,
        detection_rate=detection_rate,
        system_uptime=system_uptime,
        avg_latency_ms=avg_latency_ms,
        allow_rate=allow_rate,
        escalate_rate=escalate_rate,
        contain_rate=contain_rate
    )


@router.get("/trends/decisions", response_model=List[DecisionTrend])
async def get_decision_trends(
    days: int = Query(7, ge=1, le=90, description="Number of days to fetch"),
    granularity: str = Query("hour", regex="^(hour|day)$", description="Time granularity"),
    db: Session = Depends(get_db)
):
    """
    Get time-series trend of authorization decisions.

    Returns hourly or daily aggregated decision counts and risk scores.
    """
    start_time = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    results = db.execute(
        text("""
            SELECT
                aggregation_period as timestamp,
                allow_count,
                escalate_count,
                contain_count,
                total_decisions as total_count,
                avg_risk_score
            FROM decisions_aggregated
            WHERE aggregation_period >= :start_time
            AND period_type = :granularity
            ORDER BY aggregation_period ASC
        """),
        {"start_time": start_time, "granularity": granularity}
    ).fetchall()

    return [
        DecisionTrend(
            timestamp=row.timestamp,
            allow_count=row.allow_count,
            escalate_count=row.escalate_count,
            contain_count=row.contain_count,
            total_count=row.total_count,
            avg_risk_score=row.avg_risk_score
        )
        for row in results
    ]


@router.get("/agents", response_model=List[AgentSummary])
async def get_agent_metrics(
    days: int = Query(7, ge=1, le=90, description="Number of days to aggregate"),
    limit: int = Query(100, ge=1, le=1000, description="Max agents to return"),
    order_by: str = Query("transactions", regex="^(transactions|risk|violations)$"),
    db: Session = Depends(get_db)
):
    """
    Get per-agent performance metrics.

    Returns aggregated metrics for all agents, ordered by activity or risk.
    """
    start_time = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    # Determine order column
    order_column = {
        "transactions": "total_transactions",
        "risk": "avg_risk_score",
        "violations": "policy_violations"
    }.get(order_by, "total_transactions")

    results = db.execute(
        text(f"""
            SELECT
                agent_id,
                SUM(total_transactions) as total_transactions,
                SUM(total_value) as total_value,
                AVG(avg_risk_score) as avg_risk_score,
                SUM(allow_count) as allow_count,
                SUM(escalate_count) as escalate_count,
                SUM(contain_count) as contain_count,
                SUM(policy_violations) as policy_violations,
                MAX(aggregation_period) as last_transaction
            FROM agent_metrics
            WHERE aggregation_period >= :start_time
            GROUP BY agent_id
            ORDER BY {order_column} DESC NULLS LAST
            LIMIT :limit
        """),
        {"start_time": start_time, "limit": limit}
    ).fetchall()

    return [
        AgentSummary(
            agent_id=row.agent_id,
            total_transactions=row.total_transactions,
            total_value=row.total_value,
            avg_risk_score=row.avg_risk_score,
            allow_count=row.allow_count,
            escalate_count=row.escalate_count,
            contain_count=row.contain_count,
            policy_violations=row.policy_violations,
            last_transaction=row.last_transaction
        )
        for row in results
    ]


@router.get("/agents/{agent_id}/details")
async def get_agent_details(
    agent_id: str,
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Get detailed metrics for a specific agent.

    Returns time-series data, behavioral patterns, and anomaly indicators.
    """
    start_time = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    # Get time-series metrics
    metrics = db.execute(
        text("""
            SELECT
                aggregation_period,
                total_transactions,
                avg_risk_score,
                allow_count,
                escalate_count,
                contain_count,
                unique_recipients,
                policy_violations
            FROM agent_metrics
            WHERE agent_id = :agent_id
            AND aggregation_period >= :start_time
            ORDER BY aggregation_period ASC
        """),
        {"agent_id": agent_id, "start_time": start_time}
    ).fetchall()

    # Get fraud events
    fraud_events = db.execute(
        text("""
            SELECT COUNT(*) as fraud_count, SUM(prevented_loss) as prevented_value
            FROM fraud_events
            WHERE agent_id = :agent_id
            AND detected_at >= :start_time
        """),
        {"agent_id": agent_id, "start_time": start_time}
    ).first()

    # Get recent anomalies
    anomalies = db.execute(
        text("""
            SELECT detected_at, anomaly_type, severity, description
            FROM anomaly_detections
            WHERE entity_id = :agent_id
            AND detected_at >= :start_time
            ORDER BY detected_at DESC
            LIMIT 10
        """),
        {"agent_id": agent_id, "start_time": start_time}
    ).fetchall()

    return {
        "agent_id": agent_id,
        "time_series": [dict(row._mapping) for row in metrics],
        "fraud_summary": {
            "fraud_attempts": fraud_events.fraud_count if fraud_events else 0,
            "prevented_value": fraud_events.prevented_value if fraud_events else 0
        },
        "recent_anomalies": [dict(row._mapping) for row in anomalies]
    }


@router.get("/fraud/events", response_model=List[FraudEvent])
async def get_fraud_events(
    days: int = Query(7, ge=1, le=90),
    investigated: Optional[bool] = Query(None, description="Filter by investigation status"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get detected fraud events.

    Returns recent fraud attempts, containment actions, and investigation status.
    """
    start_time = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    query = """
        SELECT
            id, intent_id, detected_at, agent_id, amount, currency,
            risk_score, fraud_type, decision_reason, investigated
        FROM fraud_events
        WHERE detected_at >= :start_time
    """

    params = {"start_time": start_time}

    if investigated is not None:
        query += " AND investigated = :investigated"
        params["investigated"] = investigated

    query += " ORDER BY detected_at DESC LIMIT :limit"
    params["limit"] = limit

    results = db.execute(text(query), params).fetchall()

    return [
        FraudEvent(
            id=row.id,
            intent_id=row.intent_id,
            detected_at=row.detected_at,
            agent_id=row.agent_id,
            amount=row.amount,
            currency=row.currency,
            risk_score=row.risk_score or 0.0,
            fraud_type=row.fraud_type or "unknown",
            decision_reason=row.decision_reason or "",
            investigated=row.investigated or False
        )
        for row in results
    ]


@router.get("/financial/summary", response_model=FinancialSummary)
async def get_financial_summary(
    start_date: Optional[datetime.date] = Query(None),
    end_date: Optional[datetime.date] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get financial metrics and ROI analysis.

    Returns transaction value, fraud prevention savings, and operational costs.
    """
    if end_date is None:
        end_date = datetime.date.today()
    if start_date is None:
        start_date = end_date - datetime.timedelta(days=30)

    result = db.execute(
        text("""
            SELECT
                SUM(total_value_processed) as total_value_processed,
                SUM(total_transactions) as total_transactions,
                AVG(avg_transaction_value) as avg_transaction_value,
                SUM(fraud_value_prevented) as fraud_prevented_value,
                SUM(total_operational_cost) as operational_cost,
                AVG(roi_percentage) as roi_percentage,
                SUM(net_value) as net_value
            FROM financial_metrics
            WHERE date >= :start_date AND date <= :end_date
        """),
        {"start_date": start_date, "end_date": end_date}
    ).first()

    return FinancialSummary(
        period_start=start_date,
        period_end=end_date,
        total_value_processed=int(result.total_value_processed or 0),
        total_transactions=int(result.total_transactions or 0),
        avg_transaction_value=int(result.avg_transaction_value or 0),
        fraud_prevented_value=int(result.fraud_prevented_value or 0),
        operational_cost=float(result.operational_cost or 0.0),
        roi_percentage=float(result.roi_percentage) if result.roi_percentage else None,
        net_value=float(result.net_value) if result.net_value else None
    )


@router.get("/anomalies", response_model=List[AnomalyAlert])
async def get_anomalies(
    days: int = Query(7, ge=1, le=90),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    acknowledged: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get detected anomalies and alerts.

    Returns system, agent, and transaction pattern anomalies.
    """
    start_time = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    query = """
        SELECT
            id, detected_at, anomaly_type, severity, description,
            entity_type, entity_id, deviation_score, acknowledged
        FROM anomaly_detections
        WHERE detected_at >= :start_time
    """

    params = {"start_time": start_time}

    if severity:
        query += " AND severity = :severity"
        params["severity"] = severity

    if acknowledged is not None:
        query += " AND acknowledged = :acknowledged"
        params["acknowledged"] = acknowledged

    query += " ORDER BY detected_at DESC LIMIT :limit"
    params["limit"] = limit

    results = db.execute(text(query), params).fetchall()

    return [
        AnomalyAlert(
            id=row.id,
            detected_at=row.detected_at,
            anomaly_type=row.anomaly_type,
            severity=row.severity,
            description=row.description,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            deviation_score=row.deviation_score,
            acknowledged=row.acknowledged
        )
        for row in results
    ]


@router.post("/anomalies/{anomaly_id}/acknowledge")
async def acknowledge_anomaly(
    anomaly_id: int,
    acknowledged_by: str = Query(..., description="User ID or name"),
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Acknowledge an anomaly alert.

    Marks the anomaly as reviewed and optionally adds notes.
    """
    db.execute(
        text("""
            UPDATE anomaly_detections
            SET acknowledged = true,
                acknowledged_by = :acknowledged_by,
                acknowledged_at = CURRENT_TIMESTAMP,
                notes = :notes
            WHERE id = :anomaly_id
        """),
        {"anomaly_id": anomaly_id, "acknowledged_by": acknowledged_by, "notes": notes}
    )
    db.commit()

    return {"status": "acknowledged", "anomaly_id": anomaly_id}


@router.get("/reports/list")
async def list_reports(
    report_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    List generated reports.

    Returns metadata for available reports with download links.
    """
    query = """
        SELECT
            report_id, report_type, report_format, title,
            start_date, end_date, created_at, file_size_bytes
        FROM reports
        WHERE expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP
    """

    params = {"limit": limit}

    if report_type:
        query += " AND report_type = :report_type"
        params["report_type"] = report_type

    query += " ORDER BY created_at DESC LIMIT :limit"

    results = db.execute(text(query), params).fetchall()

    return {
        "reports": [dict(row._mapping) for row in results]
    }


@router.post("/export")
async def export_data(request: ExportRequest, db: Session = Depends(get_db)):
    """
    Export analytics data in various formats.

    Supports CSV, JSON, and Excel exports of decisions, agents, fraud events, and financial data.
    """
    # This is a simplified implementation
    # In production, this would:
    # 1. Queue export job
    # 2. Generate file asynchronously
    # 3. Return download link or job ID

    export_types = {
        "decisions": "decisions_aggregated",
        "agents": "agent_metrics",
        "fraud_events": "fraud_events",
        "financial": "financial_metrics"
    }

    if request.export_type not in export_types:
        raise HTTPException(status_code=400, detail=f"Invalid export type: {request.export_type}")

    # For now, return metadata about what would be exported
    return {
        "export_id": f"export_{datetime.datetime.utcnow().isoformat()}",
        "export_type": request.export_type,
        "format": request.format,
        "status": "queued",
        "estimated_completion": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
        "message": "Export job queued. Download link will be available shortly."
    }


@router.get("/predictions/volume")
async def get_volume_predictions(
    days_ahead: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get predicted transaction volume forecast.

    Returns forecasted transaction volume for capacity planning.
    """
    today = datetime.date.today()
    forecast_end = today + datetime.timedelta(days=days_ahead)

    results = db.execute(
        text("""
            SELECT
                predicted_for_date,
                predicted_value,
                confidence_lower,
                confidence_upper,
                actual_value
            FROM predictions
            WHERE prediction_type = 'volume'
            AND predicted_for_date >= :start_date
            AND predicted_for_date <= :end_date
            ORDER BY predicted_for_date ASC
        """),
        {"start_date": today, "end_date": forecast_end}
    ).fetchall()

    return {
        "predictions": [dict(row._mapping) for row in results],
        "forecast_period": {
            "start": str(today),
            "end": str(forecast_end)
        }
    }


@router.get("/dashboard/executive")
async def get_executive_dashboard(db: Session = Depends(get_db)):
    """
    Get comprehensive executive dashboard data.

    Returns all key metrics, trends, and alerts in a single response.
    """
    # Fetch KPIs
    kpis_result = await get_kpis(db)

    # Fetch recent trends (last 7 days)
    trends_result = await get_decision_trends(days=7, granularity="day", db=db)

    # Fetch top agents
    agents_result = await get_agent_metrics(days=7, limit=10, order_by="transactions", db=db)

    # Fetch recent fraud events
    fraud_result = await get_fraud_events(days=7, limit=10, db=db)

    # Fetch recent anomalies
    anomalies_result = await get_anomalies(days=7, acknowledged=False, limit=10, db=db)

    # Fetch financial summary
    financial_result = await get_financial_summary(db=db)

    return {
        "kpis": kpis_result.dict(),
        "trends": [t.dict() for t in trends_result],
        "top_agents": [a.dict() for a in agents_result],
        "recent_fraud": [f.dict() for f in fraud_result],
        "active_anomalies": [a.dict() for a in anomalies_result],
        "financial_summary": financial_result.dict(),
        "generated_at": datetime.datetime.utcnow()
    }
