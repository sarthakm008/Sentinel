"""Model definitions and training engine for Sentinel."""

import os
from typing import Dict, List, Tuple
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

from ml.features.extractor import BEHAVIORAL_FEATURES, GRAPH_FEATURES, TEMPORAL_FEATURES, ALL_FEATURES, GRAPH_CORE_FEATURES, GRAPH_GROWTH_FEATURES, SENTINEL_INTERACTION_FEATURES


class SentinelModelWrapper:
    """Wrapper around trained XGBoost models with metadata and feature sets."""

    def __init__(self, name: str, feature_names: List[str], model: xgb.XGBClassifier, scale_pos_weight: float):
        self.name = name
        self.feature_names = feature_names
        self.model = model
        self.scale_pos_weight = scale_pos_weight

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        X = df[self.feature_names].values
        return self.model.predict_proba(X)[:, 1]

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "SentinelModelWrapper":
        return joblib.load(filepath)


class ModelTrainer:
    """Trains the 4 model variants on the training dataset."""

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed

    def _train_single_model(
        self,
        name: str,
        feature_names: List[str],
        df_train: pd.DataFrame
    ) -> SentinelModelWrapper:
        X_train = df_train[feature_names].values
        y_train = df_train["label"].values

        # Compute scale_pos_weight STRICTLY from training labels
        n_pos = int(y_train.sum())
        n_neg = len(y_train) - n_pos
        scale_pos_weight = float(n_neg / max(1, n_pos))

        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            random_state=self.random_seed,
            n_jobs=-1,
            eval_metric="logloss"
        )
        model.fit(X_train, y_train)

        return SentinelModelWrapper(
            name=name,
            feature_names=feature_names,
            model=model,
            scale_pos_weight=scale_pos_weight
        )

    def train_all(
        self,
        df_train: pd.DataFrame,
        artifacts_dir: str = "artifacts/models"
    ) -> Dict[str, SentinelModelWrapper]:
        print(f"Training 7 model variants on {len(df_train):,} training records (Positives: {df_train['label'].sum():,})...")

        # 1. Behavioral Baseline
        print("  [1/7] Training Behavioral Baseline Model...")
        baseline = self._train_single_model("baseline", BEHAVIORAL_FEATURES, df_train)
        baseline.save(os.path.join(artifacts_dir, "baseline_model.joblib"))

        # 2. Graph-Enhanced Model (Behavioral + all Graph features)
        print("  [2/7] Training Graph-Enhanced Model...")
        graph_feats = BEHAVIORAL_FEATURES + GRAPH_FEATURES
        graph_model = self._train_single_model("graph_enhanced", graph_feats, df_train)
        graph_model.save(os.path.join(artifacts_dir, "graph_model.joblib"))

        # 3. Temporal-Enhanced Model
        print("  [3/7] Training Temporal-Enhanced Model...")
        temporal_feats = BEHAVIORAL_FEATURES + TEMPORAL_FEATURES
        temporal_model = self._train_single_model("temporal_enhanced", temporal_feats, df_train)
        temporal_model.save(os.path.join(artifacts_dir, "temporal_model.joblib"))

        # 4. Full Sentinel Model (Behavioral + Graph + Temporal)
        print("  [4/7] Training Full Sentinel Model...")
        sentinel_model = self._train_single_model("sentinel", ALL_FEATURES, df_train)
        sentinel_model.save(os.path.join(artifacts_dir, "sentinel_model.joblib"))

        # 5. Graph-Only Model (Core Graph features only)
        print("  [5/7] Training Graph-Only Model...")
        graph_only_model = self._train_single_model("graph_only", GRAPH_CORE_FEATURES, df_train)
        graph_only_model.save(os.path.join(artifacts_dir, "graph_only_model.joblib"))

        # 6. Growth-Only Model (Growth features only)
        print("  [6/7] Training Growth-Only Model...")
        growth_only_model = self._train_single_model("growth_only", GRAPH_GROWTH_FEATURES, df_train)
        growth_only_model.save(os.path.join(artifacts_dir, "growth_only_model.joblib"))

        # 7. Sentinel + Interaction Model
        print("  [7/7] Training Sentinel + Interaction Model...")
        sentinel_interaction_model = self._train_single_model("sentinel_interaction", SENTINEL_INTERACTION_FEATURES, df_train)
        sentinel_interaction_model.save(os.path.join(artifacts_dir, "sentinel_interaction_model.joblib"))

        return {
            "baseline": baseline,
            "graph_enhanced": graph_model,
            "temporal_enhanced": temporal_model,
            "sentinel": sentinel_model,
            "graph_only": graph_only_model,
            "growth_only": growth_only_model,
            "sentinel_interaction": sentinel_interaction_model,
        }
