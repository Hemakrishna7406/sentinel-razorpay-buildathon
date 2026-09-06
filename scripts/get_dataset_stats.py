import pandas as pd
from ml.data_generator import generate_dataset

# Generate the dataset using default mix (with more agents for better distribution)
df = generate_dataset(seed=42, num_agents_train_val=80, num_agents_test_only=20)

with open("dataset_stats.md", "w", encoding="utf-8") as f:
    f.write("# Sentinel Dataset Statistics (Seed=42)\n\n")
    f.write(f"**Total rows:** {len(df)}\n")
    f.write(f"**Total agents:** {df['agent_id'].nunique()} (A-F train/val, G-H test only)\n\n")

    f.write("### 1. Scenario Distribution\n")
    f.write("```text\n")
    f.write(df["scenario_label"].value_counts(normalize=True).to_string())
    f.write("\n```\n\n")

    f.write("### 2. Loss Label Distribution\n")
    f.write("```text\n")
    f.write(df["loss_label"].value_counts(normalize=True).to_string())
    f.write("\n```\n\n")

    f.write("### 3. Loss Type Distribution\n")
    f.write("```text\n")
    f.write(df["loss_type"].value_counts(dropna=False).to_string())
    f.write("\n```\n\n")

    f.write("### 4. Amount Statistics (Paise) by Scenario\n")
    f.write("```text\n")
    stats = df.groupby("scenario_label")["amount"].describe()[["count", "mean", "std", "min", "max"]]
    # Format to int
    stats = stats.astype(int)
    f.write(stats.to_string())
    f.write("\n```\n\n")

    f.write("### 5. Daily Action Volume by Agent\n")
    f.write("Shows volume across the 30 days. Notice test agents G/H only appear Days 26-30.\n")
    f.write("```text\n")
    f.write(df.groupby(["day", "agent_id"]).size().unstack(fill_value=0).to_string())
    f.write("\n```\n")

print("Stats written to dataset_stats.md")
