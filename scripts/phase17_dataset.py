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
        "evaluation/performance",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def generate_and_hash_dataset():
    print("Generating dataset...")
    import pandas as pd
    from ml.data_generator import generate_dataset

    df = generate_dataset(seed=42, num_agents_train_val=80, num_agents_test_only=20, days=30)

    out_path = "evaluation/dataset/sentinel_v1.parquet"
    df.to_parquet(out_path, index=False)

    with open(out_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        commit = "unknown"

    manifest = {
        "dataset_version": "sentinel-v1",
        "seed": 42,
        "generator_commit": commit,
        "row_count": len(df),
        "sha256": file_hash,
        "date_range": "Day 1 to 30",
        "train_days": [1, 20],
        "validation_days": [21, 25],
        "test_days": [26, 30],
        "seen_agents": ["A", "B", "C", "D", "E", "F"],
        "unseen_agents": ["G", "H"],
    }

    with open("evaluation/dataset/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Dataset generated. Hash: {file_hash}")
    return df


def write_stats(df):
    with open("evaluation/dataset/statistics.md", "w", encoding="utf-8") as f:
        f.write("# Dataset Statistics\n\n")
        f.write("## Scenario Balance\n")
        f.write(df["scenario_label"].value_counts(normalize=True).to_markdown() + "\n\n")

        f.write("## Agent Distribution\n")
        agent_counts = df.groupby(["day", "agent_id"]).size().unstack(fill_value=0)
        f.write(agent_counts.to_markdown() + "\n\n")

        f.write("## Loss Label Distribution\n")
        f.write(df["loss_label"].value_counts(normalize=True).to_markdown() + "\n\n")


if __name__ == "__main__":
    create_dirs()
    df = generate_and_hash_dataset()
    write_stats(df)
