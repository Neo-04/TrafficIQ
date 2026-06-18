# TrafficIQ — AI-Powered Event-Driven Traffic Impact Forecasting & Response Planning

TrafficIQ forecasts how long a reported Bengaluru traffic incident will take to
clear, then translates that forecast into an impact score, a severity level, and
a recommended on-ground deployment — so operators can plan a response before
congestion builds. It is built on ~8,173 real Bengaluru traffic-incident records.

## System architecture

```
User inputs (event cause, corridor, time, vehicle type)
        |
   Feature assembly
        |
   LightGBM resolution-time model      <-- the ONLY machine-learning model
        |
   Predicted class: Quick / Moderate / Prolonged
        |
   Impact score (rule)        -> 30 / 60 / 90
        |
   Derived severity (rule)    -> Low / Medium / High
        |
   Resource recommendation (rule) -> officers, barricades, marshals, tow trucks
        |
   Final traffic response plan
```

There is exactly one ML model. The impact score, severity, and resource layers
are transparent, editable rules layered on top of the prediction.

## What's completed

Data cleaning, EDA, feature engineering, target creation, leakage analysis,
model training and selection, severity investigation and removal, the three rule
engines (impact / severity / resources), and a local Streamlit dashboard.

## Model findings

**Resolution-time classification** is the only ML task. Target `res_time_band`
with classes Quick / Moderate / Prolonged. XGBoost, LightGBM and CatBoost were
compared; **LightGBM** was selected (best weighted F1, tie-broken on recall).

```
Accuracy   = 0.5849
Weighted F1 = 0.5920
CV F1      = 0.5603 ± 0.0152
```

This is genuine signal on a hard 3-class problem (well above the ~0.38 you'd get
by guessing). Top drivers are event-cause, location, and time features.

## Why severity is a rule, not a model

A severity classifier initially scored ~99.8% F1 — too high to be real.
Investigation showed severity is almost entirely determined by **location
identity**: nearly every monitored corridor is labelled High and nearly every
non-corridor location is labelled Low, so the model was just memorising a
location→severity lookup. Removing location identity collapsed severity
prediction to ~59% F1, *below* the majority-class baseline — i.e. no genuine
incident-level signal.

Conclusion: severity here is an administrative location label, not a learnable
outcome. The severity model was intentionally removed and severity is now
**derived from the predicted resolution class** via transparent rules. This
improves interpretability and trustworthiness and avoids an inflated, misleading
accuracy claim. (Full write-up: `reports/severity_removal_rationale.md`.)

## The rule layers

- **Impact score** — maps the predicted class to a 0–100 score (Quick 30,
  Moderate 60, Prolonged 90).
- **Severity** — derived from the predicted class (Quick→Low, Moderate→Medium,
  Prolonged→High).
- **Resource recommendation** — officers, barricades, marshals and tow trucks by
  severity, with a cause-based rule that guarantees a tow truck for breakdowns
  and accidents.

All thresholds live in `src/config.py`
(`IMPACT_SCORE_MAP`, `RESOLUTION_TO_SEVERITY`, `RESOURCE_RULES`,
`TOW_TRUCK_CAUSES`). Change them and re-run — no retraining needed.

## How to run

Install dependencies first:

```bash
pip install -r requirements.txt
```

Reproduce the data + model pipeline (in order):

```bash
python src/eda.py                  # data understanding
python src/feature_engineering.py  # features
python src/define_targets.py       # targets + location risk index
python src/train_models.py         # trains/compares, saves LightGBM model
python src/predict_pipeline.py     # end-to-end prediction demo (console)
```

Launch the dashboard:

```bash
streamlit run src/app.py
```

It opens at `http://localhost:8501`.

## Dashboard (TrafficIQ)

A local Streamlit app (no backend, API, database, or map). The sidebar takes
Event Cause, Corridor, Vehicle Type (all populated from the training values),
an Incident Hour slider, and Day of Week, plus a **Forecast Traffic Impact**
button. On click it runs the LightGBM model through the existing pipeline and
shows four KPI cards (Resolution Class, Impact Score, Severity, Recommended
Resources) and a readable Incident Response Summary.

The dashboard reads `data/processed/incidents_modeling.csv` at startup to
populate dropdowns and rebuild the pipeline lookups, so keep that file in place.

## Reusable components

- `predict_pipeline.py` — `TrafficImpactPipeline`: loads the model and produces
  an end-to-end prediction from raw inputs. (This is the "predictor".)
- `rules_engine.py` — the impact / severity / resource functions.
  (This is the "recommendation engine".)
- `app.py` — the Streamlit UI, which imports and reuses both unchanged.

## Scope

This phase intentionally stops at the dashboard. No deployment, API, database,
authentication, or maps — those are future work.