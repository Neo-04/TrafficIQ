"""
define_targets.py  --  Target Definition (between Phase 2 and modelling)
========================================================================
Locks in the three target definitions agreed from the EDA, on top of the
feature-engineered dataset:

  1. resolution_time  -> res_time_binary  (0=Quick<=60m, 1=Prolonged)
                      -> res_time_band     (Quick / Moderate / Prolonged)
  2. severity         -> severity          (0=Low, 1=High)  [from priority]
  3. location risk    -> location_risk_score + location_risk_band
                         (a COMPUTED index per location, NOT a model target)

Reads : data/processed/incidents_features.csv
Writes: data/processed/incidents_modeling.csv      (features + targets)
        data/processed/location_risk_lookup.csv     (per-location risk table)

NO model is trained here. We only define labels.

Run from the project root (after feature_engineering.py):
    python src/define_targets.py
"""

import warnings
import numpy as np
import pandas as pd

import config

warnings.filterwarnings("ignore")


# ----------------------------------------------------------------------
def load_features():
    return pd.read_csv(config.DATA_PROCESSED)   # incidents_features.csv


# ----------------------------------------------------------------------
# TARGET 1 - Resolution time bands
# ----------------------------------------------------------------------
def add_resolution_targets(df):
    res = df["resolution_time_minutes"]

    # Binary: <=60 min -> 0 (Quick), >60 -> 1 (Prolonged). NaN stays NaN.
    binary = np.where(res.isna(), np.nan,
                      (res > config.RES_BINARY_THRESHOLD_MIN).astype(float))
    df["res_time_binary"] = pd.array(binary, dtype="Int64")

    # 3-class band (string label + integer code for modelling).
    band = pd.cut(res, bins=config.RES_BAND_EDGES,
                  labels=config.RES_BAND_LABELS, right=True)
    df["res_time_band"] = band.astype("object")
    code_map = {lab: i for i, lab in enumerate(config.RES_BAND_LABELS)}
    df["res_time_band_code"] = df["res_time_band"].map(code_map).astype("Int64")
    return df


# ----------------------------------------------------------------------
# TARGET 2 - Severity (binary High vs Low)
# ----------------------------------------------------------------------
def add_severity_target(df):
    # target_high_priority already exists (1=High, 0=Low). Expose it as
    # 'severity' with a readable label column alongside.
    df["severity"] = df["target_high_priority"].astype("Int64")
    df["severity_label"] = df["severity"].map({1: "High", 0: "Low"})
    return df


# ----------------------------------------------------------------------
# TARGET 3 - Location risk score (computed index, per location)
# ----------------------------------------------------------------------
def build_location_risk(df):
    level = config.LOCATION_RISK_LEVEL          # e.g. "corridor"
    w = config.LOCATION_RISK_WEIGHTS

    g = df.groupby(level).agg(
        frequency=(level, "size"),
        avg_resolution=("resolution_time_minutes", "mean"),
        pct_high_priority=("severity", "mean"),
        pct_road_closure=("target_road_closure", "mean"),
    )

    # drop excluded buckets and tiny locations
    g = g.drop(index=[x for x in config.EXCLUDE_LOCATIONS if x in g.index],
               errors="ignore")
    g = g[g["frequency"] >= config.MIN_INCIDENTS_FOR_RISK].copy()
    g["avg_resolution"] = g["avg_resolution"].fillna(0)

    # min-max normalise each component to 0..1
    def nrm(s):
        rng = s.max() - s.min()
        return (s - s.min()) / rng if rng > 0 else s * 0.0

    score = (
        w["frequency"]        * nrm(g["frequency"]) +
        w["avg_resolution"]   * nrm(g["avg_resolution"]) +
        w["pct_high_priority"] * nrm(g["pct_high_priority"]) +
        w["pct_road_closure"]  * nrm(g["pct_road_closure"])
    )
    g["location_risk_score"] = (score * 100).round(1)

    # quartile bands: Low / Medium / High / Critical
    g["location_risk_band"] = pd.qcut(
        g["location_risk_score"], q=4,
        labels=config.RISK_BAND_LABELS, duplicates="drop"
    ).astype("object")

    lookup = g[["frequency", "avg_resolution", "pct_high_priority",
                "pct_road_closure", "location_risk_score",
                "location_risk_band"]].reset_index()
    return lookup


def attach_location_risk(df, lookup):
    level = config.LOCATION_RISK_LEVEL
    small = lookup[[level, "location_risk_score", "location_risk_band"]]
    df = df.merge(small, on=level, how="left")
    # rows in excluded/tiny locations get NaN -> mark explicitly
    df["location_risk_band"] = df["location_risk_band"].fillna("Unscored")
    return df


# ----------------------------------------------------------------------
def main():
    df = load_features()
    df = add_resolution_targets(df)
    df = add_severity_target(df)

    lookup = build_location_risk(df)
    df = attach_location_risk(df, lookup)

    # save
    df.to_csv(config.DATA_PROCESSED_DIR / "incidents_modeling.csv", index=False)
    lookup.to_csv(config.DATA_PROCESSED_DIR / "location_risk_lookup.csv", index=False)

    # ---- report ----
    print("=" * 70)
    print("TARGET DEFINITION COMPLETE")
    print("=" * 70)
    print(f"Rows: {len(df)}   ->  data/processed/incidents_modeling.csv")

    print("\n[TARGET 1a] res_time_binary (0=Quick<=60m, 1=Prolonged)")
    print(df["res_time_binary"].value_counts(dropna=False).to_string())

    print("\n[TARGET 1b] res_time_band (3-class)")
    print(df["res_time_band"].value_counts(dropna=False).to_string())

    print("\n[TARGET 2] severity (0=Low, 1=High)")
    print(df["severity"].value_counts(dropna=False).to_string())

    print(f"\n[TARGET 3] location_risk ({config.LOCATION_RISK_LEVEL}-level), "
          f"top 8 of {len(lookup)} scored locations:")
    top = lookup.sort_values("location_risk_score", ascending=False).head(8)
    print(top[[config.LOCATION_RISK_LEVEL, "frequency", "location_risk_score",
               "location_risk_band"]].to_string(index=False))
    print("\nband distribution across scored locations:")
    print(lookup["location_risk_band"].value_counts().to_string())

    print("\nNOTE: location_risk_score is a COMPUTED index (target-derived).")
    print("      Use it as a dashboard layer / standalone score. If you feed")
    print("      it as a model FEATURE, recompute it on the training fold only")
    print("      to avoid leakage — same rule as historical_*_risk.")


if __name__ == "__main__":
    main()
