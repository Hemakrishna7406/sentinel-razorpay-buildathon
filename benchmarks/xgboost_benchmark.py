import asyncio
import time
from typing import Dict, Any

from benchmarks.metrics import MetricsCollector
from ml.features import extract_features, get_feature_names
from ml.explain import explain_prediction
import xgboost as xgb
import pandas as pd
from api.dependencies import ModelWrapper
from security.capability_token import IntentContext

# Mock data
intent_dict = {
    "intent_id": "test_idx",
    "agent_id": "agent_bench",
    "action_type": "refund",
    "amount": 500,
    "currency": "INR",
    "recipient": "user_1",
    "velocity_1h": 5,
    "velocity_24h": 20,
    "volume_1h": 2500,
    "volume_24h": 10000,
    "unique_recipients_24h": 15,
    "has_sufficient_history": 1,
}
intent = IntentContext(
    intent_id=intent_dict["intent_id"],
    agent_id=intent_dict["agent_id"],
    action_type=intent_dict["action_type"],
    amount=intent_dict["amount"],
    currency=intent_dict["currency"],
    recipient=intent_dict["recipient"]
)
mock_context = {
    "velocity_1h": 5,
    "velocity_24h": 20,
    "volume_1h": 2500,
    "volume_24h": 10000,
    "unique_recipients_24h": 15,
    "has_sufficient_history": 1,
}

async def benchmark_inference(model_wrapper: ModelWrapper):
    print("--- A. Preloaded Model Inference Benchmark ---")
    metrics_infer = MetricsCollector()
    metrics_shap = MetricsCollector()
    
    # Pre-compute features
    features = extract_features(intent_dict)
    feat_df = pd.DataFrame([features])[model_wrapper.features]
    dmatrix = xgb.DMatrix(feat_df)
    
    WARMUP = 100
    RUNS = 1000

    print("Warming up XGBoost...")
    for _ in range(WARMUP):
        model_wrapper.model.predict(dmatrix)

    print("Running Preloaded Model Inference...")
    for i in range(RUNS):
        metrics_infer.start()
        proba = model_wrapper.model.predict(dmatrix)
        metrics_infer.stop()
        metrics_infer.record((metrics_infer.end_time - metrics_infer.start_time) * 1000)
        
        metrics_shap.start()
        shap_values = explain_prediction(model_wrapper.model, model_wrapper.features, features)
        metrics_shap.stop()
        metrics_shap.record((metrics_shap.end_time - metrics_shap.start_time) * 1000)

    metrics_infer.print_summary("Preloaded Model Inference")
    metrics_shap.print_summary("SHAP Computation")

async def benchmark_serving_path(model_wrapper: ModelWrapper):
    print("--- B. Production Model-Serving Path Benchmark ---")
    metrics_total = MetricsCollector()
    
    RUNS = 1000

    print("Running Production Model-Serving Path...")
    for i in range(RUNS):
        metrics_total.start()
        
        # 1. Feature Construction + Drift
        features = extract_features(intent_dict)
        
        # 2. DataFrame conversion (overhead)
        feat_df = pd.DataFrame([features])[model_wrapper.features]
        
        # 3. Inference
        dmatrix = xgb.DMatrix(feat_df)
        proba = model_wrapper.model.predict(dmatrix)
        
        # 4. SHAP
        shap_values = explain_prediction(model_wrapper.model, model_wrapper.features, features)
        
        metrics_total.stop()
        metrics_total.record((metrics_total.end_time - metrics_total.start_time) * 1000)

    metrics_total.print_summary("Total Production Model-Serving Path")

async def benchmark_xgboost():
    print("Initializing XGBoost Engine...")
    model_wrapper = ModelWrapper()
    # Assuming model exists, load it
    model_wrapper.load()
    if not model_wrapper.model:
        print("Model could not be loaded. Wont benchmark inference.")
        return
        
    await benchmark_inference(model_wrapper)
    await benchmark_serving_path(model_wrapper)

if __name__ == "__main__":
    asyncio.run(benchmark_xgboost())
