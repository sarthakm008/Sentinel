"""CLI script to extract point-in-time features and train Sentinel model suite."""

import argparse
import os
import time
import pandas as pd

from ml.features.extractor import PointInTimeFeatureExtractor
from ml.models.trainer import ModelTrainer


def run_training(data_dir: str = "data", artifacts_dir: str = "artifacts"):
    start_time = time.time()
    print("=== Sentinel Training Pipeline ===")

    # 1. Feature Extraction (or load cached)
    processed_train = os.path.join(data_dir, "processed", "features_train.parquet")
    processed_val = os.path.join(data_dir, "processed", "features_validation.parquet")
    processed_test = os.path.join(data_dir, "processed", "features_test.parquet")

    if os.path.exists(processed_train) and os.path.exists(processed_val) and os.path.exists(processed_test):
        print("Loading cached point-in-time feature matrices from data/processed/...")
        df_train = pd.read_parquet(processed_train)
        df_val = pd.read_parquet(processed_val)
        df_test = pd.read_parquet(processed_test)
    else:
        print("Extracting point-in-time features...")
        extractor = PointInTimeFeatureExtractor(data_dir=data_dir)
        df_train, df_val, df_test = extractor.extract_features()

    # 2. Train all 4 model variants
    models_dir = os.path.join(artifacts_dir, "models")
    trainer = ModelTrainer(random_seed=42)
    models = trainer.train_all(df_train, artifacts_dir=models_dir)

    duration = time.time() - start_time
    print(f"=== Model Training Complete in {duration:.2f}s ===")
    return models, df_val, df_test


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Sentinel Model Suite")
    parser.add_argument("--data-dir", type=str, default="data")
    parser.add_argument("--artifacts-dir", type=str, default="artifacts")
    args = parser.parse_args()

    run_training(data_dir=args.data_dir, artifacts_dir=args.artifacts_dir)
