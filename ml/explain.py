"""
Sentinel — SHAP Explanation Engine

Provides per-decision feature importance explanations using SHAP (TreeExplainer).
Every ALLOW/ESCALATE decision can be accompanied by a human-readable explanation
of which features contributed most to the ML risk score.

Enhanced with:
- SHAP waterfall plots for visual explanations
- Per-decision feature contribution analysis
- Batch explanation support
- Global feature importance tracking
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import xgboost as xgb

logger = logging.getLogger(__name__)

# Lazy-loaded SHAP explainer
_explainer = None
_model_ref = None


def _get_explainer(model: xgb.Booster):
    """Lazy-initialize the SHAP TreeExplainer (expensive, do once)."""
    global _explainer, _model_ref
    if _explainer is None or _model_ref is not model:
        try:
            import shap
            _explainer = shap.TreeExplainer(model)
            _model_ref = model
            logger.info("SHAP TreeExplainer initialized.")
        except ImportError:
            logger.warning("SHAP not installed. Falling back to gain-based importance.")
            return None
        except Exception as e:
            logger.warning(f"SHAP init failed: {e}. Falling back to gain-based importance.")
            return None
    return _explainer


def explain_prediction(
    model: xgb.Booster,
    feature_names: List[str],
    feature_values: Dict[str, Any],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Explain a single prediction using SHAP values.
    
    Args:
        model: Trained XGBoost Booster.
        feature_names: Ordered list of feature names the model expects.
        feature_values: Dict of feature_name → value for this sample.
        top_k: Number of top contributing features to return.
        
    Returns:
        List of dicts with keys: feature, value, shap_value, direction.
        Sorted by absolute SHAP contribution (descending).
    """
    # Build the input DataFrame
    row = {f: feature_values.get(f, 0) for f in feature_names}
    df = pd.DataFrame([row])[feature_names]
    
    explainer = _get_explainer(model)
    
    if explainer is not None:
        try:
            shap_values = explainer.shap_values(df)
            # shap_values is an array of shape (1, n_features)
            sv = shap_values[0] if isinstance(shap_values, np.ndarray) else shap_values
            if hasattr(sv, 'values'):
                sv = sv.values[0]
            elif len(sv.shape) > 1:
                sv = sv[0]
                
            contributions = []
            for i, fname in enumerate(feature_names):
                contributions.append({
                    "feature": fname,
                    "value": float(row[fname]) if not pd.isna(row[fname]) else None,
                    "shap_value": float(sv[i]),
                    "direction": "increases_risk" if sv[i] > 0 else "decreases_risk",
                })
            
            # Sort by absolute SHAP value
            contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
            return contributions[:top_k]
            
        except Exception as e:
            logger.warning(f"SHAP explanation failed: {e}. Falling back to gain-based.")
    
    # Fallback: gain-based feature importance
    return _gain_fallback(model, feature_names, feature_values, top_k)


def _gain_fallback(
    model: xgb.Booster,
    feature_names: List[str],
    feature_values: Dict[str, Any],
    top_k: int,
) -> List[Dict[str, Any]]:
    """Fallback using XGBoost's built-in gain importance."""
    try:
        importance = model.get_score(importance_type="gain")
    except Exception:
        return []

    contributions = []
    for fname in feature_names:
        xgb_key = fname
        gain = importance.get(xgb_key, 0.0)
        val = feature_values.get(fname, 0)
        contributions.append({
            "feature": fname,
            "value": float(val) if not pd.isna(val) else None,
            "shap_value": float(gain),
            "direction": "model_uses_feature" if gain > 0 else "unused",
        })

    contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
    return contributions[:top_k]


def generate_waterfall_plot(
    model: xgb.Booster,
    feature_names: List[str],
    feature_values: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Optional[str]:
    """
    Generate SHAP waterfall plot for a single prediction.

    Args:
        model: Trained XGBoost model
        feature_names: List of feature names
        feature_values: Dict of feature values for this prediction
        output_path: Optional path to save plot image

    Returns:
        Path to saved plot, or None if SHAP not available
    """
    try:
        import shap
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("SHAP or matplotlib not installed. Cannot generate waterfall plot.")
        return None

    explainer = _get_explainer(model)
    if explainer is None:
        return None

    # Build the input DataFrame
    row = {f: feature_values.get(f, 0) for f in feature_names}
    df = pd.DataFrame([row])[feature_names]

    try:
        shap_values = explainer.shap_values(df)

        # Handle different SHAP value formats
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        if hasattr(shap_values, 'values'):
            shap_values = shap_values.values[0]
        elif len(shap_values.shape) > 1:
            shap_values = shap_values[0]

        # Create waterfall plot
        plt.figure(figsize=(10, 6))

        # Get base value (expected value)
        base_value = explainer.expected_value
        if isinstance(base_value, np.ndarray):
            base_value = base_value[0]

        # Create SHAP Explanation object
        explanation = shap.Explanation(
            values=shap_values,
            base_values=base_value,
            data=df.values[0],
            feature_names=feature_names
        )

        shap.plots.waterfall(explanation, show=False)

        if output_path:
            plt.savefig(output_path, bbox_inches='tight', dpi=150)
            plt.close()
            logger.info(f"Waterfall plot saved to {output_path}")
            return str(output_path)
        else:
            plt.close()

    except Exception as e:
        logger.warning(f"Failed to generate waterfall plot: {e}")
        return None


def explain_batch(
    model: xgb.Booster,
    feature_names: List[str],
    feature_df: pd.DataFrame,
    top_k: int = 5
) -> List[List[Dict[str, Any]]]:
    """
    Explain multiple predictions in batch.

    Args:
        model: Trained XGBoost model
        feature_names: List of feature names
        feature_df: DataFrame with features for multiple samples
        top_k: Number of top features per sample

    Returns:
        List of explanations (one per sample)
    """
    explainer = _get_explainer(model)

    if explainer is None:
        logger.warning("SHAP not available. Using gain fallback for batch.")
        return [
            _gain_fallback(model, feature_names, row.to_dict(), top_k)
            for _, row in feature_df.iterrows()
        ]

    try:
        shap_values = explainer.shap_values(feature_df[feature_names])

        # Handle different formats
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        if hasattr(shap_values, 'values'):
            shap_values = shap_values.values

        explanations = []
        for i in range(len(feature_df)):
            contributions = []
            for j, fname in enumerate(feature_names):
                contributions.append({
                    "feature": fname,
                    "value": float(feature_df.iloc[i][fname]) if not pd.isna(feature_df.iloc[i][fname]) else None,
                    "shap_value": float(shap_values[i, j]),
                    "direction": "increases_risk" if shap_values[i, j] > 0 else "decreases_risk",
                })

            contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
            explanations.append(contributions[:top_k])

        return explanations

    except Exception as e:
        logger.warning(f"Batch SHAP explanation failed: {e}")
        return [
            _gain_fallback(model, feature_names, row.to_dict(), top_k)
            for _, row in feature_df.iterrows()
        ]


def get_global_feature_importance(
    model: xgb.Booster,
    feature_names: List[str],
    sample_data: pd.DataFrame,
    importance_type: str = "shap"
) -> List[Dict[str, float]]:
    """
    Calculate global feature importance across entire dataset.

    Args:
        model: Trained XGBoost model
        feature_names: List of feature names
        sample_data: Sample data for SHAP value computation
        importance_type: 'shap' or 'gain'

    Returns:
        List of dicts with feature importance scores
    """
    if importance_type == "shap":
        explainer = _get_explainer(model)

        if explainer is not None:
            try:
                shap_values = explainer.shap_values(sample_data[feature_names])

                # Handle formats
                if isinstance(shap_values, list):
                    shap_values = shap_values[0]
                if hasattr(shap_values, 'values'):
                    shap_values = shap_values.values

                # Calculate mean absolute SHAP value for each feature
                mean_abs_shap = np.abs(shap_values).mean(axis=0)

                importance_list = [
                    {"feature": fname, "importance": float(mean_abs_shap[i])}
                    for i, fname in enumerate(feature_names)
                ]

                importance_list.sort(key=lambda x: x["importance"], reverse=True)
                return importance_list

            except Exception as e:
                logger.warning(f"SHAP global importance failed: {e}. Using gain.")

    # Fallback to gain-based importance
    try:
        importance = model.get_score(importance_type="gain")
        importance_list = [
            {"feature": fname, "importance": float(importance.get(fname, 0.0))}
            for fname in feature_names
        ]
        importance_list.sort(key=lambda x: x["importance"], reverse=True)
        return importance_list

    except Exception as e:
        logger.error(f"Failed to compute feature importance: {e}")
        return []


def generate_human_readable_explanation(
    contributions: List[Dict[str, Any]],
    risk_score: float,
    decision: str
) -> str:
    """
    Generate human-readable explanation text.

    Args:
        contributions: List of feature contributions from explain_prediction
        risk_score: Model risk score
        decision: Final decision (ALLOW, ESCALATE, CONTAIN)

    Returns:
        Human-readable explanation string
    """
    explanation_parts = [
        f"Decision: {decision} (Risk Score: {risk_score:.2%})",
        "",
        "Top Contributing Factors:"
    ]

    for i, contrib in enumerate(contributions[:5], 1):
        feature = contrib["feature"]
        value = contrib["value"]
        shap_val = contrib["shap_value"]
        direction = "increased" if shap_val > 0 else "decreased"

        # Format value based on feature type
        if value is None:
            value_str = "N/A"
        elif feature.endswith("_missing"):
            value_str = "Missing" if value == 1 else "Present"
        elif isinstance(value, float):
            value_str = f"{value:.2f}"
        else:
            value_str = str(value)

        explanation_parts.append(
            f"{i}. {feature} = {value_str} ({direction} risk by {abs(shap_val):.4f})"
        )

    return "\n".join(explanation_parts)
