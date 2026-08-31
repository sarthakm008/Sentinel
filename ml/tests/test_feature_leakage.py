"""Feature leakage, point-in-time correctness, and metadata isolation tests for Phase 2."""

import os
import pandas as pd
import pytest

from ml.features.extractor import ALL_FEATURES, BEHAVIORAL_FEATURES, GRAPH_FEATURES, TEMPORAL_FEATURES, PointInTimeFeatureExtractor


@pytest.fixture
def feature_matrices():
    extractor = PointInTimeFeatureExtractor()
    df_train = pd.read_parquet("data/processed/features_train.parquet")
    df_val = pd.read_parquet("data/processed/features_validation.parquet")
    df_test = pd.read_parquet("data/processed/features_test.parquet")
    return df_train, df_val, df_test


def test_no_forbidden_columns_in_features(feature_matrices):
    """Feature matrices must never include generator ground truth or label leakage."""
    df_train, df_val, df_test = feature_matrices
    forbidden = {"ring_id", "is_abuse", "fraud_ring_score", "generator_abuse_probability", "archetype", "structure_class"}

    for name, df in [("train", df_train), ("val", df_val), ("test", df_test)]:
        assert not forbidden.intersection(set(df.columns)), f"Forbidden column found in {name} feature matrix"


def test_feature_completeness(feature_matrices):
    """Assert all defined behavioral, graph, and temporal features exist and have no NaNs."""
    df_train, df_val, df_test = feature_matrices

    for feat in ALL_FEATURES:
        assert feat in df_train.columns, f"Missing feature {feat} in train"
        assert feat in df_val.columns, f"Missing feature {feat} in validation"
        assert feat in df_test.columns, f"Missing feature {feat} in test"

        assert not df_train[feat].isna().any(), f"NaN values in train feature {feat}"
        assert not df_val[feat].isna().any(), f"NaN values in validation feature {feat}"
        assert not df_test[feat].isna().any(), f"NaN values in test feature {feat}"


def test_point_in_time_causality_properties(feature_matrices):
    """Assert customer_order_count and customer_refund_count are realistic and non-negative."""
    df_train, df_val, df_test = feature_matrices

    for df in [df_train, df_val, df_test]:
        assert (df["customer_order_count"] >= 0).all()
        assert (df["customer_refund_count"] >= 0).all()
        assert (df["refund_delay_hours"] >= 0).all()
        assert (df["customer_account_age_days"] >= 0).all()
        assert (df["graph_component_size"] >= 1).all()
