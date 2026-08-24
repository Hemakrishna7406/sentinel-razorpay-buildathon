"""
Sentinel — SHAP Explanation Engine

Provides per-decision feature importance explanations using SHAP (TreeExplainer).
Every ALLOW/ESCALATE decision can be accompanied by a human-readable explanation
of which features contributed most to the ML risk score.
"""

import logging
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
