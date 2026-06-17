# Model Comparison - Resolution Time (Round 1)

Selection: highest weighted F1, tie-break weighted Recall.

| Model | Accuracy | Precision | Recall | F1 | CV F1 (mean+/-std) |
|---|---|---|---|---|---|
| LightGBM | 0.5849 | 0.6088 | 0.5849 | 0.5920 | 0.5603+/-0.0152 |
| CatBoost | 0.5946 | 0.5991 | 0.5946 | 0.5906 | 0.5632+/-0.0084 |
| XGBoost | 0.5907 | 0.5862 | 0.5907 | 0.5864 | 0.5721+/-0.0148 |

**Best: LightGBM**

> Severity is no longer a model. It is derived from the predicted resolution class via rules_engine.py. See reports/severity_removal_rationale.md.
