with open('ml/evaluation/evaluator.py', 'r') as f:
    content = f.read()

# Update the primary comparison table
old_section = """            f"| **Graph-Only** | {test_results['graph_only']['pr_auc']:.4f} | {test_results['graph_only']['roc_auc']:.4f} | {test_results['graph_only']['precision']:.4f} | {test_results['graph_only']['recall']:.4f} | {test_results['graph_only']['f1']:.4f} | INR {test_results['graph_only']['financial_metrics']['total_expected_loss']:,.2f} | INR {test_results['graph_only']['loss_avoided_vs_baseline_inr']:,.2f} |\",
            "",
            "---",
            "",
            "## 2. Out-of-Distribution Generalization: Ring Type F (Structural Shift)", """

new_section = """            f"| **Graph-Only** | {test_results['graph_only']['pr_auc']:.4f} | {test_results['graph_only']['roc_auc']:.4f} | {test_results['graph_only']['precision']:.4f} | {test_results['graph_only']['recall']:.4f} | {test_results['graph_only']['f1']:.4f} | INR {test_results['graph_only']['financial_metrics']['total_expected_loss']:,.2f} | INR {test_results['graph_only']['loss_avoided_vs_baseline_inr']:,.2f} |\",
            f"| **Growth-Only** | {test_results['growth_only']['pr_auc']:.4f} | {test_results['growth_only']['roc_auc']:.4f} | {test_results['growth_only']['precision']:.4f} | {test_results['growth_only']['recall']:.4f} | {test_results['growth_only']['f1']:.4f} | INR {test_results['growth_only']['financial_metrics']['total_expected_loss']:,.2f} | INR {test_results['growth_only']['loss_avoided_vs_baseline_inr']:,.2f} |\",
            "",
            "---",
            "",
            "## 2. Out-of-Distribution Generalization: Ring Type F (Structural Shift)", """

content = content.replace(old_section, new_section)

# Update Type F table
old_typef = """            f"| **Graph-Only** | {type_f_eval['graph_only']['pr_auc']:.4f} | {type_f_eval['graph_only']['precision']:.4f} | {type_f_eval['graph_only']['recall']:.4f} | {type_f_eval['graph_only']['f1']:.4f} |\",
            "",
            "---",
            "",
            "## 3. Future-Period Temporal Holdout (Days 120\u2013180)", """

new_typef = """            f"| **Graph-Only** | {type_f_eval['graph_only']['pr_auc']:.4f} | {type_f_eval['graph_only']['precision']:.4f} | {type_f_eval['graph_only']['recall']:.4f} | {type_f_eval['graph_only']['f1']:.4f} |\",
            f"| **Growth-Only** | {type_f_eval['growth_only']['pr_auc']:.4f} | {type_f_eval['growth_only']['precision']:.4f} | {type_f_eval['growth_only']['recall']:.4f} | {type_f_eval['growth_only']['f1']:.4f} |\",
            "",
            "---",
            "",
            "## 3. Future-Period Temporal Holdout (Days 120\u2013180)", """

content = content.replace(old_typef, new_typef)

# Future period table
old_future = """            f"| **Graph-Only** | {future_eval['graph_only']['pr_auc']:.4f} | {future_eval['graph_only']['precision']:.4f} | {future_eval['graph_only']['recall']:.4f} | {future_eval['graph_only']['f1']:.4f} |\",
            "",
            "---",
            "",
            "## 4. Frozen Validation Thresholds & Cost Model Parameters", """

new_future = """            f"| **Graph-Only** | {future_eval['graph_only']['pr_auc']:.4f} | {future_eval['graph_only']['precision']:.4f} | {future_eval['graph_only']['recall']:.4f} | {future_eval['graph_only']['f1']:.4f} |\",
            f"| **Growth-Only** | {future_eval['growth_only']['pr_auc']:.4f} | {future_eval['growth_only']['precision']:.4f} | {future_eval['growth_only']['recall']:.4f} | {future_eval['growth_only']['f1']:.4f} |\",
            "",
            "---",
            "",
            "## 4. Frozen Validation Thresholds & Cost Model Parameters", """

content = content.replace(old_future, new_future)

# Update thresholds
old_thresholds = """            f"  - Graph-Only: {thresholds['graph_only']:.2f}\",
            ""
        ]"""

new_thresholds = """            f"  - Graph-Only: {thresholds['graph_only']:.2f}",
            f"  - Growth-Only: {thresholds['growth_only']:.2f}",
            ""
        ]"""

content = content.replace(old_thresholds, new_thresholds)

with open('ml/evaluation/evaluator.py', 'w') as f:
    f.write(content)

print('Done')