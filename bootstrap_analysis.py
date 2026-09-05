import pandas as pd
import numpy as np
import json
import joblib
from sklearn.metrics import average_precision_score, roc_auc_score

df_test = pd.read_parquet('data/processed/features_test.parquet')
rings_df = pd.read_parquet('data/raw/ground_truth_rings.parquet')

type_f_rings = rings_df[rings_df['ring_type'] == 'type_f_structural_shift']
type_f_custs = set()
for _, r in type_f_rings.iterrows():
    type_f_custs.update(json.loads(r['customer_ids']))

df_test_std = df_test[~df_test['customer_id'].isin(type_f_custs)]
df_test_f = df_test[df_test['customer_id'].isin(type_f_custs)]

# Future period
t_ref_series = pd.to_datetime(df_test['timestamp_refund'], format='ISO8601')
t_min = t_ref_series.min()
day_indices = (t_ref_series - t_min).dt.total_seconds() / 86400.0
df_test_future = df_test[day_indices >= 120.0].copy()
df_test_future_std = df_test_future[~df_test_future['customer_id'].isin(type_f_custs)]
df_test_future_f = df_test_future[df_test_future['customer_id'].isin(type_f_custs)]

models = {
    'baseline': joblib.load('artifacts/models/baseline_model.joblib'),
    'graph_enhanced': joblib.load('artifacts/models/graph_model.joblib'),
    'temporal_enhanced': joblib.load('artifacts/models/temporal_model.joblib'),
    'sentinel': joblib.load('artifacts/models/sentinel_model.joblib'),
    'graph_only': joblib.load('artifacts/models/graph_only_model.joblib'),
    'growth_only': joblib.load('artifacts/models/growth_only_model.joblib'),
    'sentinel_interaction': joblib.load('artifacts/models/sentinel_interaction_model.joblib'),
)

from sklearn.metrics import average_precision_score, roc_auc_score

def bootstrap_pr_auc_diff(model1, model2, df, n_bootstrap=2000, seed=42):
    np.random.seed(seed)
    y = df['label'].values
    probs1 = model1.predict_proba(df)
    probs2 = model2.predict_proba(df)
    
    n = len(y)
    diffs = []
    for _ in range(n_bootstrap):
        idx = np.random.choice(n, n, replace=True)
        pr1 = average_precision_score(y[idx], probs1[idx])
        pr2 = average_precision_score(y[idx], probs2[idx])
        diffs.append(pr1 - pr2)
    return np.percentile(diffs, [2.5, 97.5]), np.mean(diffs)

models = {
    'baseline': joblib.load('artifacts/models/baseline_model.joblib'),
    'graph_enhanced': joblib.load('artifacts/models/graph_model.joblib'),
    'temporal_enhanced': joblib.load('artifacts/models/temporal_model.joblib'),
    'sentinel': joblib.load('artifacts/models/sentinel_model.joblib'),
    'graph_only': joblib.load('artifacts/models/graph_only_model.joblib'),
    'growth_only': joblib.load('artifacts/models/growth_only_model.joblib'),
    'sentinel_interaction': joblib.load('artifacts/models/sentinel_interaction_model.joblib'),
)

print('=== Standard A-E Test (Primary Decision Population) ===')
df_test_std = df_test[~df_test['customer_id'].isin(type_f_custs)]

# Primary comparison: Sentinel + Interaction vs Sentinel
ci, mean_diff = bootstrap_pr_auc_diff(
    models['sentinel_interaction'], models['sentinel'], df_test_std)
print('Sentinel+Interaction vs Sentinel (Standard): Delta PR-AUC = {:+.4f}, 95% CI = [{:+.4f}, {:+.4f}]'.format(mean_diff, ci[0], ci[1]))

# Sentinel vs Temporal
ci, mean_diff = bootstrap_pr_auc_diff(
    models['sentinel'], models['temporal_enhanced'], df_test_std)
print('Sentinel vs Temporal (Standard): Delta PR-AUC = {:+.4f}, 95% CI = [{:+.4f}, {:+.4f}]'.format(mean_diff, ci[0], ci[1]))

# Graph-Enhanced vs Baseline
ci, mean_diff = bootstrap_pr_auc_diff(
    models['graph_enhanced'], models['baseline'], df_test_std)
print('Graph-Enhanced vs Baseline (Standard): Delta PR-AUC = {:+.4f}, 95% CI = [{:+.4f}, {:+.4f}]'.format(mean_diff, ci[0], ci[1]))

# Growth-Only vs Baseline
ci, mean_diff = bootstrap_pr_auc_diff(
    models['growth_only'], models['baseline'], df_test_std)
print('Growth-Only vs Baseline (Standard): Delta PR-AUC = {:+.4f}, 95% CI = [{:+.4f}, {:+.4f}]'.format(mean_diff, ci[0], ci[1]))

# Sentinel vs Sentinel+Interaction (inverse comparison)
ci, mean_diff = bootstrap_pr_auc_diff(
    models['sentinel'], models['sentinel_interaction'], df_test_std)
print('Sentinel vs Sentinel+Interaction (Standard): Delta PR-AUC = {:+.4f}, 95% CI = [{:+.4f}, {:+.4f}]'.format(mean_diff, ci[0], ci[1]))

# ROC-AUC differences
from sklearn.metrics import roc_auc_score

def bootstrap_roc_auc_diff(model1, model2, df, n_bootstrap=2000, seed=42):
    np.random.seed(seed)
    y = df['label'].values
    probs1 = model1.predict_proba(df)
    probs2 = model2.predict_proba(df)
    
    n = len(y)
    diffs = []
    for _ in range(2000):
        idx = np.random.choice(len(y), len(y), replace=True)
        roc1 = roc_auc_score(y[idx], probs1[idx])
        roc2 = roc_auc_score(y[idx], probs2[idx])
        diffs.append(roc1 - roc2)
    return np.percentile(diffs, [2.5, 97.5]), np.mean(diffs)

print()
print('=== ROC-AUC Differences (Standard) ===')
ci, mean_diff = bootstrap_roc_auc_diff(models['sentinel_interaction'], models['sentinel'], df_test[~df_test['customer_id'].isin(type_f_custs)])
print('Sentinel+Interaction vs Sentinel ROC-AUC: Delta={:+.4f}, CI=[{:+.4f}, {:+.4f}]'.format(mean_diff, ci[0], ci[1]))

print()
print('=== Type F (Structural Shift) ===')
df_test_f = df_test[df_test['customer_id'].isin(type_f_custs)]
ci, mean_diff = bootstrap_pr_auc_diff(
    models['sentinel_interaction'], models['sentinel'], df_test_f)
print('Type F Sentinel+Interaction vs Sentinel: Delta PR-AUC = {:+.4f}, 95% CI = [{:+.4f}, {:+.4f}]'.format(mean_diff, ci[0], ci[1]))

ci, mean_diff = bootstrap_pr_auc_diff(
    models['growth_only'], models['baseline'], df_test_f)
print('Type F Growth-Only vs Baseline: Delta PR-AUC = {:+.4f}, 95% CI = [{:+.4f}, {:+.4f}]'.format(mean_diff, ci[0], ci[1]))

print()
print('=== Future Period (Days 120-180) ===')
t_ref_series = pd.to_datetime(df_test['timestamp_refund'], format='ISO8601')
t_min = t_ref_series.min()
day_indices = (t_ref_series - t_min).dt.total_seconds() / 86400.0
df_test_future = df_test[day_indices >= 120.0].copy()
df_test_future_std = df_test_future[~df_test_future['customer_id'].isin(type_f_custs)]

ci, mean_diff = bootstrap_pr_auc_diff(
    models['sentinel_interaction'], models['sentinel'], df_test_future_std)
print('Future Sentinel+Interaction vs Sentinel: Delta PR-AUC = {:+.4f}, 95% CI = [{:+.4f}, {:+.4f}]'.format(mean_diff, ci[0], ci[1]))

ci, mean_diff = bootstrap_pr_auc_diff(
    models['growth_only'], models['baseline'], df_test_future_std)
print('Future Growth-Only vs Baseline: Delta PR-AUC = {:+.4f}, 95% CI = [{:+.4f}, {:+.4f}]'.format(mean_diff, ci[0], ci[1]))

# Summary of all models
print()
print('=== Summary of All Models (Standard A-E) ===')
for name, model in models.items():
    probs = model.predict_proba(df_test_std)
    y = df_test_std['label'].values
    pr_auc = average_precision_score(y, probs)
    roc_auc = roc_auc_score(y, probs)
    print('  {}: PR-AUC={:.4f}, ROC-AUC={:.4f}'.format(name, pr_auc, roc_auc))