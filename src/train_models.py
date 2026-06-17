"""
train_models.py  --  PHASE 3 (revised in Phase 4): Resolution-Time Model
========================================================================
Round-1 baseline training for the ONLY machine-learning target:

  * resolution_time_class  (Quick / Moderate / Prolonged)  -- multiclass

The severity model was intentionally removed (see
reports/severity_removal_rationale.md): severity turned out to be an
administrative location label, not a learnable outcome. Severity is now a
rule derived from the predicted resolution class (see rules_engine.py).

Models compared (no ensembling, no AutoML): XGBoost, LightGBM, CatBoost.
Selection rule: highest weighted F1, tie-break weighted Recall.

Reads : data/processed/incidents_modeling.csv
Writes:
  models/  resolution_time_model.pkl, feature_list.pkl,
           label_encoders.pkl, preprocessing_objects.pkl
  reports/ resolution_time_results.csv, model_comparison.md,
           class_distribution_report.md, leakage_analysis_report.md
  plots/   resolution_confusion_matrix.png, resolution_feature_importance.png

Run from the project root (after define_targets.py):
    python src/train_models.py
"""

import warnings
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, classification_report, confusion_matrix,
                             ConfusionMatrixDisplay)

from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

import config

warnings.filterwarnings("ignore")
RS = config.RANDOM_STATE

# Features known at the moment an incident is first reported (legit inputs).
FEATURES = [
    "latitude", "longitude", "endlatitude", "endlongitude",
    "event_cause_encoded",
    "hour", "day_of_week", "month", "weekend_flag", "peak_hour_flag",
    "corridor_frequency", "corridor_is_hotspot",
    "junction_frequency", "junction_is_hotspot",
    "police_station_frequency", "police_station_is_hotspot",
    "is_planned", "is_authenticated", "event_cause_frequency",
    "hour_incident_rate",
    "veh_auto", "veh_bmtc_bus", "veh_heavy_vehicle", "veh_ksrtc_bus",
    "veh_lcv", "veh_others", "veh_private_bus", "veh_private_car",
    "veh_taxi", "veh_truck", "veh_unknown",
]

# Columns excluded from features, with reasons (for the leakage report).
LEAKAGE = {
    "resolution_time_minutes": "Raw source of the resolution-time target.",
    "res_time_binary": "Alternate form of the resolution target.",
    "res_time_band": "The resolution target itself (string).",
    "res_time_band_code": "The resolution target itself (encoded).",
    "target_high_priority": "Removed severity label (administrative, not predictive).",
    "severity": "Removed severity label.",
    "severity_label": "Removed severity label.",
    "target_road_closure": "Co-outcome decided during/after response, not known at report time.",
    "historical_event_risk": "Mean resolution time per cause -> aggregate of the target (leak).",
    "historical_location_risk": "Mean resolution time per corridor -> aggregate of the target (leak).",
    "location_risk_score": "Composite of priority/closure/resolution -> aggregate of targets (leak).",
    "location_risk_band": "Banded location_risk_score (leak).",
    "event_cause": "Raw text -> replaced by event_cause_encoded.",
    "corridor": "Raw text -> represented by corridor_frequency / hotspot.",
    "police_station": "Raw text -> represented by police_station_frequency / hotspot.",
    "junction": "Raw text -> represented by junction_frequency / hotspot.",
}


def build_models(n_classes):
    objective = "binary:logistic" if n_classes == 2 else "multi:softprob"
    xgb = XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.1,
        subsample=0.9, colsample_bytree=0.9, tree_method="hist",
        objective=objective, eval_metric="logloss",
        random_state=RS, n_jobs=-1,
    )
    lgbm = LGBMClassifier(
        n_estimators=300, num_leaves=31, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9,
        class_weight="balanced", random_state=RS, n_jobs=-1, verbose=-1,
    )
    cat = CatBoostClassifier(
        iterations=300, depth=6, learning_rate=0.1,
        loss_function="Logloss" if n_classes == 2 else "MultiClass",
        auto_class_weights="Balanced", random_seed=RS, verbose=0,
    )
    return {"XGBoost": xgb, "LightGBM": lgbm, "CatBoost": cat}


def cv_f1(model_ctor, X, y):
    skf = StratifiedKFold(n_splits=config.CV_SPLITS, shuffle=True, random_state=RS)
    scores = []
    for tr, va in skf.split(X, y):
        m = model_ctor()
        w = compute_sample_weight("balanced", y[tr])
        m.fit(X[tr], y[tr], sample_weight=w)
        scores.append(f1_score(y[va], m.predict(X[va]), average="weighted"))
    return float(np.mean(scores)), float(np.std(scores))


def importance_plot(model, mname, feats, path, title, top=20):
    if mname == "XGBoost":
        score = model.get_booster().get_score(importance_type="gain")
        imp = np.array([score.get(f"f{i}", 0.0) for i in range(len(feats))])
    elif mname == "LightGBM":
        imp = model.booster_.feature_importance(importance_type="gain")
    else:
        imp = np.array(model.get_feature_importance())
    order = np.argsort(imp)[::-1][:top]
    plt.figure(figsize=(8, 7))
    plt.barh([feats[i] for i in order][::-1], imp[order][::-1], color="#2c3e50")
    plt.xlabel("Gain importance"); plt.title(title)
    plt.tight_layout(); plt.savefig(path, dpi=120); plt.close()


def write_leakage_report():
    md = "# Leakage Analysis Report\n\n"
    md += f"**Features used for training ({len(FEATURES)}):**\n\n" + ", ".join(FEATURES) + "\n\n"
    md += "**Excluded columns and why:**\n\n| Column | Reason |\n|---|---|\n"
    for c, r in LEAKAGE.items():
        md += f"| {c} | {r} |\n"
    (config.REPORTS_DIR / "leakage_analysis_report.md").write_text(md, encoding="utf-8")


def main():
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    config.PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(config.DATA_MODELING)
    cause_enc = LabelEncoder()
    df["event_cause_encoded"] = cause_enc.fit_transform(df["event_cause"].astype(str))
    write_leakage_report()

    # ---- Resolution-time target only ----
    data = df.dropna(subset=["res_time_band"]).copy()
    y_enc = LabelEncoder()
    y = y_enc.fit_transform(data["res_time_band"].astype(str))
    X = data[FEATURES].astype(float).values

    counts = pd.Series(y).value_counts().sort_index()
    dist = {y_enc.classes_[i]: int(counts.get(i, 0)) for i in range(len(y_enc.classes_))}
    ratio = max(dist.values()) / max(1, min(dist.values()))
    print("Resolution class distribution:", dist, f"| imbalance ratio = {ratio:.2f}:1")

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=config.TEST_SIZE, random_state=RS, stratify=y)

    n_classes = len(y_enc.classes_)
    models = build_models(n_classes)
    ctors = {k: (lambda k=k: build_models(n_classes)[k]) for k in models}

    rows, fitted = [], {}
    for mname, model in models.items():
        cv_mean, cv_std = cv_f1(ctors[mname], X_tr, y_tr)
        w = compute_sample_weight("balanced", y_tr)
        model.fit(X_tr, y_tr, sample_weight=w)
        pred = model.predict(X_te)
        rows.append({"Model": mname,
                     "Accuracy": accuracy_score(y_te, pred),
                     "Precision": precision_score(y_te, pred, average="weighted"),
                     "Recall": recall_score(y_te, pred, average="weighted"),
                     "F1": f1_score(y_te, pred, average="weighted"),
                     "CV_F1_mean": cv_mean, "CV_F1_std": cv_std})
        fitted[mname] = model
        print(f"\n[{mname}] test F1={rows[-1]['F1']:.4f} recall={rows[-1]['Recall']:.4f} "
              f"CV F1={cv_mean:.4f}+/-{cv_std:.4f}")
        print(classification_report(y_te, pred, target_names=y_enc.classes_, digits=3))

    results = pd.DataFrame(rows).round(4)
    ranked = results.sort_values(["F1", "Recall"], ascending=False).reset_index(drop=True)
    best_name = ranked.loc[0, "Model"]
    best_model = fitted[best_name]
    print(f">>> BEST resolution model: {best_name} "
          f"(F1={ranked.loc[0,'F1']:.4f}, Recall={ranked.loc[0,'Recall']:.4f})")

    # confusion matrix + importance for the winner
    cm = confusion_matrix(y_te, best_model.predict(X_te))
    disp = ConfusionMatrixDisplay(cm, display_labels=y_enc.classes_)
    fig, ax = plt.subplots(figsize=(5.5, 5))
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title(f"Resolution Time - {best_name}")
    plt.tight_layout()
    plt.savefig(config.PLOTS_DIR / "resolution_confusion_matrix.png", dpi=120); plt.close()
    importance_plot(best_model, best_name, FEATURES,
                    config.PLOTS_DIR / "resolution_feature_importance.png",
                    title=f"Resolution Time - {best_name} top-20 features")

    # reports
    results.to_csv(config.REPORTS_DIR / "resolution_time_results.csv", index=False)
    cls = "# Class Distribution Report\n\n## Resolution Time\n\n| Class | Count |\n|---|---|\n"
    for k, v in dist.items():
        cls += f"| {k} | {v} |\n"
    cls += (f"\nImbalance ratio = **{ratio:.2f} : 1**, handled with balanced "
            "sample weights (no SMOTE in Round 1).\n")
    (config.REPORTS_DIR / "class_distribution_report.md").write_text(cls, encoding="utf-8")

    cmp = "# Model Comparison - Resolution Time (Round 1)\n\n"
    cmp += "Selection: highest weighted F1, tie-break weighted Recall.\n\n"
    cmp += "| Model | Accuracy | Precision | Recall | F1 | CV F1 (mean+/-std) |\n|---|---|---|---|---|---|\n"
    for _, r in ranked.iterrows():
        cmp += (f"| {r.Model} | {r.Accuracy:.4f} | {r.Precision:.4f} | {r.Recall:.4f} "
                f"| {r.F1:.4f} | {r.CV_F1_mean:.4f}+/-{r.CV_F1_std:.4f} |\n")
    cmp += f"\n**Best: {best_name}**\n\n"
    cmp += ("> Severity is no longer a model. It is derived from the predicted "
            "resolution class via rules_engine.py. See "
            "reports/severity_removal_rationale.md.\n")
    (config.REPORTS_DIR / "model_comparison.md").write_text(cmp, encoding="utf-8")

    # artifacts (resolution only)
    joblib.dump(best_model, config.MODELS_DIR / "resolution_time_model.pkl")
    joblib.dump(FEATURES, config.MODELS_DIR / "feature_list.pkl")
    joblib.dump({"event_cause": cause_enc, "resolution_time_class": y_enc},
                config.MODELS_DIR / "label_encoders.pkl")
    joblib.dump({"features": FEATURES, "feature_dtype": "float",
                 "resolution_target_col": "res_time_band",
                 "best_model": best_name,
                 "random_state": RS, "test_size": config.TEST_SIZE},
                config.MODELS_DIR / "preprocessing_objects.pkl")

    print("\n" + "=" * 70)
    print(f"PHASE 3/4 COMPLETE - single ML model: {best_name} (resolution time)")
    print("Severity removed -> derived by rules_engine.py")
    print("=" * 70)


if __name__ == "__main__":
    main()