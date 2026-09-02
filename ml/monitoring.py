"""
Sentinel — ML Model Monitoring & Drift Detection

Tracks model performance in production, detects feature drift, prediction drift,
and data quality issues. Provides alerting for model degradation.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class DriftMetrics:
    """Metrics for drift detection."""
    metric_name: str
    current_value: float
    baseline_value: float
    drift_score: float
    drift_detected: bool
    threshold: float
    timestamp: str


@dataclass
class ModelPerformanceMetrics:
    """Real-time model performance tracking."""
    timestamp: str
    total_predictions: int
    prediction_distribution: Dict[str, float]  # LOW, SUSPICIOUS, HIGH
    avg_risk_score: float
    std_risk_score: float
    escalation_rate: float
    containment_rate: float
    allow_rate: float


class ModelMonitor:
    """
    Monitors ML model performance and detects drift in production.

    Tracks:
    - Feature drift (distribution changes)
    - Prediction drift (output distribution changes)
    - Data quality issues (missing values, outliers)
    - Performance degradation
    """

    def __init__(
        self,
        baseline_data: Optional[pd.DataFrame] = None,
        feature_names: Optional[List[str]] = None,
        drift_threshold: float = 0.05,
        alert_callback: Optional[callable] = None
    ):
        """
        Initialize the model monitor.

        Args:
            baseline_data: Reference data for drift detection (training data)
            feature_names: List of feature names to monitor
            drift_threshold: p-value threshold for KS test (default 0.05)
            alert_callback: Function to call when drift is detected
        """
        self.baseline_data = baseline_data
        self.feature_names = feature_names or []
        self.drift_threshold = drift_threshold
        self.alert_callback = alert_callback

        # Compute baseline statistics
        self.baseline_stats = self._compute_baseline_stats() if baseline_data is not None else {}

        # Track metrics over time
        self.performance_history: List[ModelPerformanceMetrics] = []
        self.drift_history: List[DriftMetrics] = []

        # Counters for real-time monitoring
        self.prediction_count = 0
        self.prediction_sum = 0.0
        self.prediction_squared_sum = 0.0
        self.decision_counts = {"ALLOW": 0, "ESCALATE": 0, "CONTAIN": 0}

        logger.info(f"ModelMonitor initialized with {len(self.feature_names)} features")

    def _compute_baseline_stats(self) -> Dict[str, Dict[str, float]]:
        """Compute baseline statistics from training data."""
        stats_dict = {}

        for col in self.feature_names:
            if col not in self.baseline_data.columns:
                continue

            values = self.baseline_data[col].dropna()
            if len(values) == 0:
                continue

            stats_dict[col] = {
                "mean": float(values.mean()),
                "std": float(values.std()),
                "min": float(values.min()),
                "max": float(values.max()),
                "median": float(values.median()),
                "q25": float(values.quantile(0.25)),
                "q75": float(values.quantile(0.75)),
                "missing_rate": float(self.baseline_data[col].isna().mean())
            }

        return stats_dict

    def detect_feature_drift(
        self,
        current_data: pd.DataFrame,
        method: str = "ks"
    ) -> List[DriftMetrics]:
        """
        Detect drift in feature distributions.

        Args:
            current_data: Recent production data
            method: Statistical test method ('ks' for Kolmogorov-Smirnov, 'psi' for PSI)

        Returns:
            List of drift metrics for each feature
        """
        if self.baseline_data is None:
            logger.warning("No baseline data available for drift detection")
            return []

        drift_results = []
        timestamp = datetime.utcnow().isoformat() + "Z"

        for feature in self.feature_names:
            if feature not in current_data.columns or feature not in self.baseline_data.columns:
                continue

            baseline_values = self.baseline_data[feature].dropna()
            current_values = current_data[feature].dropna()

            if len(baseline_values) == 0 or len(current_values) == 0:
                continue

            if method == "ks":
                drift_score, p_value = self._ks_test(baseline_values, current_values)
                drift_detected = p_value < self.drift_threshold

            elif method == "psi":
                drift_score = self._population_stability_index(baseline_values, current_values)
                drift_detected = drift_score > 0.2  # PSI > 0.2 indicates significant drift
                p_value = drift_score

            else:
                raise ValueError(f"Unknown drift detection method: {method}")

            drift_metric = DriftMetrics(
                metric_name=feature,
                current_value=float(current_values.mean()),
                baseline_value=float(baseline_values.mean()),
                drift_score=drift_score,
                drift_detected=drift_detected,
                threshold=self.drift_threshold,
                timestamp=timestamp
            )

            drift_results.append(drift_metric)

            if drift_detected:
                logger.warning(
                    f"Feature drift detected in '{feature}': "
                    f"baseline={drift_metric.baseline_value:.4f}, "
                    f"current={drift_metric.current_value:.4f}, "
                    f"drift_score={drift_score:.4f}"
                )

                if self.alert_callback:
                    self.alert_callback(drift_metric)

        self.drift_history.extend(drift_results)
        return drift_results

    def _ks_test(
        self,
        baseline: pd.Series,
        current: pd.Series
    ) -> Tuple[float, float]:
        """
        Perform Kolmogorov-Smirnov test for distribution comparison.

        Returns:
            Tuple of (KS statistic, p-value)
        """
        ks_stat, p_value = stats.ks_2samp(baseline, current)
        return float(ks_stat), float(p_value)

    def _population_stability_index(
        self,
        baseline: pd.Series,
        current: pd.Series,
        n_bins: int = 10
    ) -> float:
        """
        Calculate Population Stability Index (PSI).

        PSI < 0.1: No significant change
        PSI 0.1-0.2: Moderate change
        PSI > 0.2: Significant change
        """
        # Create bins based on baseline distribution
        min_val = min(baseline.min(), current.min())
        max_val = max(baseline.max(), current.max())
        bins = np.linspace(min_val, max_val, n_bins + 1)

        # Calculate distributions
        baseline_dist = np.histogram(baseline, bins=bins)[0] / len(baseline)
        current_dist = np.histogram(current, bins=bins)[0] / len(current)

        # Avoid division by zero
        baseline_dist = np.where(baseline_dist == 0, 0.0001, baseline_dist)
        current_dist = np.where(current_dist == 0, 0.0001, current_dist)

        # Calculate PSI
        psi = np.sum((current_dist - baseline_dist) * np.log(current_dist / baseline_dist))

        return float(psi)

    def detect_prediction_drift(
        self,
        predictions: np.ndarray,
        window_size: int = 1000
    ) -> Optional[DriftMetrics]:
        """
        Detect drift in prediction distribution.

        Args:
            predictions: Array of recent predictions
            window_size: Number of predictions to use for drift detection

        Returns:
            DriftMetrics if drift detected, None otherwise
        """
        if len(self.performance_history) < 2:
            return None

        # Get baseline prediction distribution (from earliest data)
        baseline_preds = [
            m.avg_risk_score
            for m in self.performance_history[:min(10, len(self.performance_history))]
        ]

        # Get current prediction distribution
        current_preds = [
            m.avg_risk_score
            for m in self.performance_history[-min(10, len(self.performance_history)):]
        ]

        if len(baseline_preds) == 0 or len(current_preds) == 0:
            return None

        baseline_mean = np.mean(baseline_preds)
        current_mean = np.mean(current_preds)

        # Simple z-test for mean shift
        baseline_std = np.std(baseline_preds)
        if baseline_std < 1e-6:
            return None

        z_score = abs(current_mean - baseline_mean) / (baseline_std / np.sqrt(len(current_preds)))
        drift_detected = z_score > 2.0  # 95% confidence

        drift_metric = DriftMetrics(
            metric_name="prediction_mean",
            current_value=current_mean,
            baseline_value=baseline_mean,
            drift_score=z_score,
            drift_detected=drift_detected,
            threshold=2.0,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

        if drift_detected:
            logger.warning(
                f"Prediction drift detected: "
                f"baseline_mean={baseline_mean:.4f}, "
                f"current_mean={current_mean:.4f}, "
                f"z_score={z_score:.4f}"
            )

            if self.alert_callback:
                self.alert_callback(drift_metric)

        self.drift_history.append(drift_metric)
        return drift_metric

    def check_data_quality(
        self,
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Check data quality issues.

        Returns:
            Dictionary of quality metrics and issues
        """
        issues = []
        quality_metrics = {
            "total_samples": len(data),
            "missing_value_rate": {},
            "outlier_rate": {},
            "issues": issues
        }

        for feature in self.feature_names:
            if feature not in data.columns:
                issues.append(f"Missing feature: {feature}")
                continue

            # Missing values
            missing_rate = data[feature].isna().mean()
            quality_metrics["missing_value_rate"][feature] = float(missing_rate)

            if missing_rate > 0.2:
                issues.append(f"High missing rate in {feature}: {missing_rate:.2%}")

            # Outliers (using IQR method)
            if feature in self.baseline_stats:
                baseline_q25 = self.baseline_stats[feature]["q25"]
                baseline_q75 = self.baseline_stats[feature]["q75"]
                iqr = baseline_q75 - baseline_q25

                if iqr > 0:
                    lower_bound = baseline_q25 - 3 * iqr
                    upper_bound = baseline_q75 + 3 * iqr

                    outliers = data[feature].apply(
                        lambda x: x < lower_bound or x > upper_bound if not pd.isna(x) else False
                    )
                    outlier_rate = outliers.mean()
                    quality_metrics["outlier_rate"][feature] = float(outlier_rate)

                    if outlier_rate > 0.1:
                        issues.append(f"High outlier rate in {feature}: {outlier_rate:.2%}")

        return quality_metrics

    def track_prediction(
        self,
        risk_score: float,
        decision: str
    ):
        """
        Track a single prediction for real-time monitoring.

        Args:
            risk_score: Model output probability
            decision: Final decision (ALLOW, ESCALATE, CONTAIN)
        """
        self.prediction_count += 1
        self.prediction_sum += risk_score
        self.prediction_squared_sum += risk_score ** 2

        if decision in self.decision_counts:
            self.decision_counts[decision] += 1

    def get_current_metrics(self) -> ModelPerformanceMetrics:
        """Get current performance metrics and reset counters."""
        if self.prediction_count == 0:
            return ModelPerformanceMetrics(
                timestamp=datetime.utcnow().isoformat() + "Z",
                total_predictions=0,
                prediction_distribution={},
                avg_risk_score=0.0,
                std_risk_score=0.0,
                escalation_rate=0.0,
                containment_rate=0.0,
                allow_rate=0.0
            )

        avg_risk = self.prediction_sum / self.prediction_count
        variance = (self.prediction_squared_sum / self.prediction_count) - (avg_risk ** 2)
        std_risk = np.sqrt(max(0, variance))

        total = sum(self.decision_counts.values())

        metrics = ModelPerformanceMetrics(
            timestamp=datetime.utcnow().isoformat() + "Z",
            total_predictions=self.prediction_count,
            prediction_distribution={
                k: v / total if total > 0 else 0.0
                for k, v in self.decision_counts.items()
            },
            avg_risk_score=float(avg_risk),
            std_risk_score=float(std_risk),
            escalation_rate=float(self.decision_counts["ESCALATE"] / total if total > 0 else 0),
            containment_rate=float(self.decision_counts["CONTAIN"] / total if total > 0 else 0),
            allow_rate=float(self.decision_counts["ALLOW"] / total if total > 0 else 0)
        )

        self.performance_history.append(metrics)

        # Reset counters
        self.prediction_count = 0
        self.prediction_sum = 0.0
        self.prediction_squared_sum = 0.0
        self.decision_counts = {"ALLOW": 0, "ESCALATE": 0, "CONTAIN": 0}

        return metrics

    def export_report(self, output_path: Path):
        """Export monitoring report as JSON."""
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "baseline_stats": self.baseline_stats,
            "performance_history": [asdict(m) for m in self.performance_history[-100:]],
            "recent_drift_alerts": [asdict(d) for d in self.drift_history[-50:] if d.drift_detected],
            "summary": {
                "total_predictions_tracked": sum(m.total_predictions for m in self.performance_history),
                "drift_alerts_count": sum(1 for d in self.drift_history if d.drift_detected),
                "avg_escalation_rate": np.mean([m.escalation_rate for m in self.performance_history]) if self.performance_history else 0.0
            }
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Monitoring report exported to {output_path}")


def create_baseline_monitor(
    train_data_path: str,
    feature_names: List[str]
) -> ModelMonitor:
    """
    Create a ModelMonitor from training data.

    Args:
        train_data_path: Path to training data CSV or DataFrame
        feature_names: List of feature names to monitor

    Returns:
        Initialized ModelMonitor
    """
    if train_data_path.endswith('.csv'):
        baseline_data = pd.read_csv(train_data_path)
    else:
        # Assume it's a path to serialized DataFrame
        baseline_data = pd.read_pickle(train_data_path)

    return ModelMonitor(
        baseline_data=baseline_data,
        feature_names=feature_names,
        drift_threshold=0.05
    )
