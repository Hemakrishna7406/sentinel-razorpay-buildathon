import pandas as pd
from ml.data_generator import generate_dataset
from ml.train import run_training_pipeline

print("Generating synthetic data for training...")
df = generate_dataset()

print("Training model...")
run_training_pipeline(df, tune=False)
print("Model registered successfully.")
