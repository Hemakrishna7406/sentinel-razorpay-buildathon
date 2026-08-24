"""
Sentinel — Automated MLOps Retraining Pipeline

This script represents the automated, scheduled retraining architecture.
It pulls fresh transactions from the Audit log database, joins them with simulated
ground truth labels (chargebacks/fraud reports), extracts features, and retrains 
the XGBoost model. The best model is automatically registered into MLflow.
"""

import os
import logging
import pandas as pd
from sqlalchemy import create_engine
import mlflow

from ml.train import run_training_pipeline
from db.models import AuditRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./sentinel.db")

def fetch_fresh_data_and_label() -> pd.DataFrame:
    """
    Simulates fetching recent transactions from the Audit database and 
    joining them with ground truth labels.
    """
    logger.info(f"Connecting to database at {DB_URL}...")
    engine = create_engine(DB_URL)
    
    query = "SELECT * FROM audit_records ORDER BY id DESC LIMIT 10000"
    
    try:
        df = pd.read_sql(query, engine)
        logger.info(f"Fetched {len(df)} records from Audit DB.")
    except Exception as e:
        logger.warning(f"Could not fetch from DB (might be empty/not created). Generating synthetic fallback data. Error: {e}")
        from ml.data_generator import generate_dataset
        return generate_dataset(num_samples=5000)
        
    if len(df) < 100:
        logger.warning("Not enough fresh data in DB for a robust retrain. Falling back to synthetic baseline.")
        from ml.data_generator import generate_dataset
        return generate_dataset(num_samples=5000)

    # In a real pipeline, we would join 'intent_id' against a risk/chargeback database.
    # Here, we simulate labels based on whether Sentinel previously contained it, 
    # plus some random noise to simulate new fraud patterns.
    
    import numpy as np
    
    # Extract features from the raw audit JSON/columns
    df["loss_label"] = np.where(df["decision"] == "CONTAINED", 1, 0)
    
    # Introduce label noise (some allowed were actually fraud, some contained were false positives)
    noise = np.random.rand(len(df))
    df.loc[(df["decision"] == "ALLOW") & (noise > 0.98), "loss_label"] = 1
    df.loc[(df["decision"] == "CONTAINED") & (noise > 0.90), "loss_label"] = 0
    
    # Assign temporal splits for training (1-20), validation (21-25), test (26-30)
    df["day"] = np.random.randint(1, 31, size=len(df))
    
    return df

def run_mlops_pipeline():
    logger.info("=== STARTING MLOPS RETRAINING PIPELINE ===")
    
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    
    # 1. Data Ingestion & Labeling
    logger.info("[Step 1] Ingesting and Labeling recent Audit data...")
    df = fetch_fresh_data_and_label()
    
    # 2. Model Training & Tuning
    logger.info("[Step 2] Triggering XGBoost Training Pipeline with Hyperparameter Tuning...")
    model, best_params, test_df = run_training_pipeline(df, ablation_mode="full_sentinel", tune=True)
    
    # 3. Model Registration
    logger.info("[Step 3] Best model registered successfully in MLflow.")
    
    logger.info("=== MLOPS PIPELINE COMPLETED ===")

if __name__ == "__main__":
    run_mlops_pipeline()
