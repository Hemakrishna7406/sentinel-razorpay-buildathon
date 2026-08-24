import os
import json
import hashlib
import subprocess
from pathlib import Path

def create_dirs():
    dirs = [
        "evaluation/dataset",
        "evaluation/methodology",
        "evaluation/experiments",
        "evaluation/security",
        "evaluation/performance"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def generate_and_hash_dataset():
    print("Generating Sentinel v2 Challenge Dataset...")
    import pandas as pd
    from ml.data_generator import generate_dataset
    
    # 80 training agents, 20 test agents
    df = generate_dataset(seed=42, num_agents_train_val=80, num_agents_test_only=20, days=30)
    
    out_path = "evaluation/dataset/sentinel_v2.parquet"
    df.to_parquet(out_path, index=False)
    
    with open(out_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        commit = "unknown"
        
    manifest = {
        "dataset_version": "sentinel-v2",
        "seed": 42,
        "generator_commit": commit,
        "row_count": len(df),
        "sha256": file_hash,
        "date_range": "Day 1 to 30",
        "train_days": [1, 20],
        "validation_days": [21, 25],
        "test_days": [26, 30],
        "description": "Behavioral-Evasion Challenge Dataset. Normal transactions with anomalous behavior."
    }
    
    with open("evaluation/dataset/manifest_v2.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Dataset v2 generated. Hash: {file_hash}")
    return df

def write_stats(df):
    with open("evaluation/dataset/statistics_v2.md", "w", encoding="utf-8") as f:
        f.write("# Sentinel-v2 Dataset Statistics\n\n")
        f.write("## Scenario Balance\n")
        f.write(df['scenario_label'].value_counts(normalize=True).to_markdown() + "\n\n")
        
        f.write("## Loss Label Distribution\n")
        f.write(df['loss_label'].value_counts(normalize=True).to_markdown() + "\n\n")

if __name__ == "__main__":
    create_dirs()
    df = generate_and_hash_dataset()
    write_stats(df)
