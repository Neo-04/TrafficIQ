# Event-Driven Traffic Impact Forecasting & Response Planning

Predicts how long a Bengaluru traffic incident will take to clear, then layers
transparent rules on top to produce an impact score, severity, and a resource
recommendation.

## System architecture (final)

```
User inputs (event cause, location, time, vehicle type)
        |
   Feature assembly  (predict_pipeline.py)
        |
   LightGBM resolution-time model   <-- the ONLY ML model
        |
   Predicted class: Quick / Moderate / Prolonged
        |
   Impact score  (rules)      -> 30 / 60 / 90
        |
   Derived severity (rules)   -> Low / Medium / High
        |
   Resource recommendation (rules) -> officers, barricades, marshals, tow trucks
        |
   Final response
```

Severity is **not** a model — see `reports/severity_removal_rationale.md`.

## Project structure

```
traffic_impact_forecasting/
├── data/
│   ├── raw/incidents_raw.csv
│   └── processed/
│       ├── incidents_features.csv        # Phase 2 output
│       ├── incidents_modeling.csv        # Phase 2.5 output (targets added)
│       ├── feature_inventory.csv
│       └── location_risk_lookup.csv
├── src/
│   ├── config.py                 # paths, constants, AND the rule tables
│   ├── eda.py                    # Phase 1
│   ├── feature_engineering.py    # Phase 2
│   ├── define_targets.py         # Phase 2.5 (targets + location risk index)
│   ├── train_models.py           # Phase 3/4: trains/compares, saves LightGBM
│   ├── rules_engine.py           # Phase 4: impact / severity / resources
│   └── predict_pipeline.py       # Phase 4: end-to-end inference
├── models/
│   ├── resolution_time_model.pkl     # LightGBM (only model kept)
│   ├── feature_list.pkl
│   ├── label_encoders.pkl
│   └── preprocessing_objects.pkl
├── reports/   (eda, model comparison, leakage, class dist, severity rationale)
├── plots/     (resolution confusion matrix + feature importance)
├── requirements.txt
└── README.md
```

> The severity model artifacts (`severity_model.pkl`, `severity_results.csv`,
> `severity_confusion_matrix.png`, `severity_feature_importance.png`) were
> removed in Phase 4.

## How to run (in order)

```bash
pip install -r requirements.txt

python src/eda.py                  # Phase 1
python src/feature_engineering.py  # Phase 2
python src/define_targets.py       # Phase 2.5
python src/train_models.py         # Phase 3/4 -> saves LightGBM model
python src/predict_pipeline.py     # Phase 4 demo (end-to-end prediction)
```

## Editing the rules
All rule thresholds live in `src/config.py`:
`IMPACT_SCORE_MAP`, `RESOLUTION_TO_SEVERITY`, `RESOURCE_RULES`, `TOW_TRUCK_CAUSES`.
Change them and re-run the pipeline — no retraining needed.