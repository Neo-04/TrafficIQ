# Modelling Readiness Report — Phase 1 & 2

Bengaluru Event-Driven Traffic Impact dataset · 8,173 rows · prepared frame: 8,173 × 39
**No models trained.** This document defines the clean feature set, the recommended
targets, the data limitations, and a ranked shortlist of models to try next.

---

## 1. Feature Inventory

Features retained in `data/processed/incidents_features.csv`.

| Feature | Type | Description | Keep/Drop | Reason |
|---|---|---|---|---|
| latitude | float | Incident start latitude | Keep | Geospatial signal; 0% missing |
| longitude | float | Incident start longitude | Keep | Geospatial signal; 0% missing |
| endlatitude | float | End-of-stretch latitude | Keep (weak) | 2% missing, many zeros; low value |
| endlongitude | float | End-of-stretch longitude | Keep (weak) | Same as above |
| event_cause | category | Real incident type (breakdown, accident, construction…) | Keep | Strongest predictor of impact |
| corridor | category | Named arterial corridor | Keep | Strong location signal |
| police_station | category | Jurisdiction (54 values) | Keep | Strong location signal |
| junction | category | Named junction | Keep | Useful but 69% missing |
| hour | int | Hour of day from start_datetime | Keep | Time-of-day pattern |
| day_of_week | int | 0=Mon … 6=Sun | Keep | Weekly pattern |
| month | int | Month of event | Keep | Seasonal pattern (limited 5-month span) |
| weekend_flag | bool | 1 if Sat/Sun | Keep | Weekend behaviour differs |
| peak_hour_flag | bool | 1 if 7–11AM or 4–9PM | Keep | Congestion-window signal |
| resolution_time_minutes | float | **closed − start** (minutes) | Keep (target A) | Core impact-length signal |
| corridor_frequency | int | Historical incident count for that corridor | Keep | Frequency encoding for trees |
| corridor_is_hotspot | bool | Corridor in top-20% by count | Keep | Hotspot indicator |
| junction_frequency | int | Incident count for that junction | Keep | Frequency encoding |
| junction_is_hotspot | bool | Junction in top-20% | Keep | Hotspot indicator |
| police_station_frequency | int | Incident count for station | Keep | Frequency encoding |
| police_station_is_hotspot | bool | Station in top-20% | Keep | Hotspot indicator |
| is_planned | bool | 1 if event_type == planned | Keep | Planned vs unplanned split |
| is_authenticated | bool | 1 if verified by officer | Keep | Mild quality/severity signal |
| event_cause_frequency | int | Frequency encoding of cause | Keep | Compact cause signal |
| veh_* (11 cols) | bool | One-hot of vehicle type | Keep | Matters for breakdown impact |
| historical_event_risk | float | Mean resolution time per cause | Keep ⚠ | Powerful — but recompute per train fold (leakage) |
| historical_location_risk | float | Mean resolution time per corridor | Keep ⚠ | Same leakage caveat |
| hour_incident_rate | float | Share of incidents at that hour | Keep | Temporal exposure signal |
| target_high_priority | bool | priority == High | Keep (target B) | Severity label |
| target_road_closure | bool | requires_road_closure | Keep (target C) | Closure label |

**Dropped (39 columns)** — three buckets:
- *100%/near-empty (>90% missing):* comment, map_file, meta_data, route_path, resolved_*, end_datetime, reason_breakdown, cargo_material, age_of_truck, direction, citizen_accident_id, assigned_to_police_id, end_address.
- *System IDs / free text (not predictive):* id, client_id, *_by_id, kgid, veh_no, description, address.
- *Raw columns replaced by engineered versions:* start/closed/created/modified datetimes (→ time + duration features), event_type/priority/requires_road_closure/authenticated (→ encoded), veh_type (→ one-hot), zone/gba_identifier/status.

⚠ **Leakage note:** `historical_event_risk` and `historical_location_risk` are aggregates of the target. When you train, recompute them **inside the training fold only** (or use cross-fitting / out-of-fold means), never on the full dataset.

---

## 2. Modelling Readiness

**Clean feature set:** 33 usable predictors (geo, time, location-frequency/hotspot, cause, vehicle one-hots, historical risk). All numeric or boolean after engineering — no raw text or unparsed dates remain.

**Recommended targets (in priority order):**
1. **Severity classification** — `target_high_priority`. 8,173 labelled rows, ~62% positive (well balanced). *Easiest, most reliable first model.*
2. **Road-closure classification** — `target_road_closure`. 8,173 rows but only ~8% positive — imbalanced; use class weighting and judge with PR-AUC/recall, not accuracy.
3. **Resolution-time regression** — `resolution_time_minutes`. Only **2,588** labelled rows (rows with a closed timestamp) and a long right tail; treat as the hardest target. Consider predicting `log(minutes)` and/or banding into buckets (e.g. <30 / 30–120 / >120 min) to make it a classification problem if regression is noisy.

**Data limitations to state openly:**
- Only ~5 months of data (Nov 2023 – Apr 2024); limited seasonality.
- 94% unplanned, dominated by vehicle breakdowns — planned crowd events (rally/concert) barely exist, so the model speaks to *incident* impact, not crowd events.
- Linear correlations with the targets are weak (|r| mostly < 0.2) → favour non-linear, tree-based models.
- Resolution time available for only a third of rows and heavily skewed.

---

## 3. Model Recommendations (ranked, not trained)

Ranked for **tabular data of ~8k rows with encoded categoricals and weak linear structure**. Tree ensembles dominate this regime; deep nets do not.

| Rank | Model | Suitability | Why |
|---|---|---|---|
| 1 | **XGBoost** | ★★★★★ | Best-in-class on tabular; handles mixed features and imbalance (`scale_pos_weight`). Start here. |
| 2 | **LightGBM** | ★★★★★ | As strong as XGBoost, faster, native categorical handling. Great for all three targets. |
| 3 | **CatBoost** | ★★★★★ | Excellent with categorical signals (corridor/cause), minimal tuning, robust on small data. |
| 4 | **HistGradientBoosting** (sklearn) | ★★★★☆ | Fast histogram GBM, handles NaNs natively, no extra dependency. Excellent default. |
| 5 | **Random Forest** | ★★★★☆ | Robust baseline, no scaling, strong feature importances, `class_weight` for imbalance. |
| 6 | **Extra Trees** | ★★★★☆ | Like RF with more randomisation; often slightly better variance, very fast. |
| 7 | **Gradient Boosting** (sklearn) | ★★★☆☆ | Solid but slower and less tunable than XGB/LGBM/Cat. |
| 8 | **Logistic Regression** (clf) / **Ridge** (reg) | ★★★☆☆ | Interpretable benchmark every model must beat; weak given non-linear data. |
| 9 | **ElasticNet / Lasso** (reg) | ★★★☆☆ | Regularised linear baselines for resolution-time regression. |
| 10 | **Decision Tree** | ★★★☆☆ | Overfits alone, but the single most explainable model — useful for demoing rules. |
| 11 | **AdaBoost** | ★★☆☆☆ | Works, but generally beaten by modern GBMs here. |
| 12 | **K-Nearest Neighbors** | ★★☆☆☆ | Needs scaling; struggles with high-dim one-hot features and imbalance. |
| 13 | **SVM / SVR (RBF)** | ★★☆☆☆ | Feasible at 8k rows but slow, scaling-sensitive, weak with sparse one-hots. |
| 14 | **Gaussian Naive Bayes** | ★★☆☆☆ | Fast, but the feature-independence assumption is badly violated here. |
| 15 | **Multi-Layer Perceptron (MLP)** | ★☆☆☆☆ | 8k rows is too little for a neural net to beat GBMs; high tuning cost. |
| 16 | **TabNet / deep tabular nets** | ★☆☆☆☆ | Designed for much larger tabular data; not worth it at this size. |
| 17 | **Gaussian Process** | ★☆☆☆☆ | Poor scaling and overkill; only viable on a tiny subset. |

**Practical recommendation:** for the prototype, train **LightGBM or CatBoost** for the two classification targets and a **LightGBM regressor (on log-minutes)** for resolution time, with **Random Forest as the sanity-check baseline** and **Logistic/Ridge as the floor**. Everything below rank 10 is for comparison/learning only.
