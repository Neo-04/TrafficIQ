# Model Comparison - Resolution Time (Round 1)

Selection: highest weighted F1, tie-break weighted Recall.

| Model | Accuracy | Precision | Recall | F1 | CV F1 (mean+/-std) |
|---|---|---|---|---|---|
| CatBoost | 0.6023 | 0.6097 | 0.6023 | 0.5994 | 0.5679+/-0.0033 |
| LightGBM | 0.5849 | 0.6088 | 0.5849 | 0.5920 | 0.5603+/-0.0152 |
| XGBoost | 0.5869 | 0.5858 | 0.5869 | 0.5849 | 0.5692+/-0.0170 |

**Best: CatBoost**

> Severity is no longer a model. It is derived from the predicted resolution class via rules_engine.py. See reports/severity_removal_rationale.md.
