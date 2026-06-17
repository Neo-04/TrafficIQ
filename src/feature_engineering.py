"""
feature_engineering.py  --  PHASE 2: Feature Engineering
=========================================================
Builds a clean, modelling-ready dataframe from the raw incident data and
writes it to data/processed/incidents_features.csv.

NO model is trained here. We only create features + candidate targets and
report how usable each target is.

Run from the project root (after eda.py):
    python src/feature_engineering.py
"""

import warnings
import numpy as np
import pandas as pd

import config

warnings.filterwarnings("ignore")


# ----------------------------------------------------------------------
def load_raw():
    return pd.read_csv(config.DATA_RAW, low_memory=False)


# ----------------------------------------------------------------------
# 1. Time features from start_datetime
# ----------------------------------------------------------------------
def add_time_features(df):
    start = pd.to_datetime(df["start_datetime"], errors="coerce", utc=True)
    df["hour"] = start.dt.hour
    df["day_of_week"] = start.dt.dayofweek          # 0=Mon .. 6=Sun
    df["month"] = start.dt.month
    df["weekend_flag"] = (df["day_of_week"] >= 5).astype("Int64")

    pm0, pm1 = config.PEAK_MORNING
    pe0, pe1 = config.PEAK_EVENING
    is_peak = (((df["hour"] >= pm0) & (df["hour"] < pm1)) |
               ((df["hour"] >= pe0) & (df["hour"] < pe1)))
    df["peak_hour_flag"] = is_peak.astype("Int64")
    return df, start


# ----------------------------------------------------------------------
# 2. Duration features
# ----------------------------------------------------------------------
def add_duration_features(df, start):
    closed = pd.to_datetime(df["closed_datetime"], errors="coerce", utc=True)
    end = pd.to_datetime(df["end_datetime"], errors="coerce", utc=True)

    # resolution_time = closed - start  (our main impact-length signal)
    res = (closed - start).dt.total_seconds() / 60
    res = res.where((res > 0) & (res < config.MAX_RESOLUTION_MINUTES))
    df["resolution_time_minutes"] = res.round(1)

    # event_duration = end - start  (unreliable: end_datetime ~94% missing)
    ev = (end - start).dt.total_seconds() / 60
    ev = ev.where((ev > 0) & (ev < config.MAX_RESOLUTION_MINUTES))
    df["event_duration_minutes"] = ev.round(1)
    return df


# ----------------------------------------------------------------------
# 3. Location frequency encoding + hotspot flags
# ----------------------------------------------------------------------
def add_location_features(df):
    for col in ["corridor", "junction", "police_station"]:
        if col not in df.columns:
            continue
        freq = df[col].value_counts(dropna=True)
        df[f"{col}_frequency"] = df[col].map(freq).fillna(0).astype(int)
        # hotspot = location in the top 20% by incident count
        if len(freq) > 0:
            thresh = freq.quantile(0.80)
            hot = set(freq[freq >= thresh].index)
            df[f"{col}_is_hotspot"] = df[col].isin(hot).astype("Int64")
    return df


# ----------------------------------------------------------------------
# 4. Event feature encoding
#    - event_type   (2 vals)  -> binary label
#    - veh_type     (10 vals) -> one-hot (low cardinality)
#    - event_cause  (17 vals) -> frequency encoding (some rare classes)
# ----------------------------------------------------------------------
def add_event_encodings(df):
    # binary
    if "event_type" in df.columns:
        df["is_planned"] = (df["event_type"] == "planned").astype("Int64")
    if "authenticated" in df.columns:
        df["is_authenticated"] = (df["authenticated"] == "yes").astype("Int64")

    # frequency encoding for event_cause
    if "event_cause" in df.columns:
        cause_freq = df["event_cause"].value_counts()
        df["event_cause_frequency"] = df["event_cause"].map(cause_freq).fillna(0).astype(int)

    # one-hot for veh_type (fill missing with 'unknown' first)
    if "veh_type" in df.columns:
        vt = df["veh_type"].fillna("unknown")
        dummies = pd.get_dummies(vt, prefix="veh").astype("Int64")
        df = pd.concat([df, dummies], axis=1)
    return df


# ----------------------------------------------------------------------
# 5. Historical risk features (aggregation)
#    NOTE ON LEAKAGE: these use whole-dataset aggregates. When you move to
#    modelling you MUST recompute them on the training fold only (or use
#    cross-fitting), otherwise target information leaks into features.
#    For Phase-2 preparation we compute them and flag this clearly.
# ----------------------------------------------------------------------
def add_risk_features(df):
    # historical_event_risk: mean resolution time per cause
    if "event_cause" in df.columns:
        cause_risk = df.groupby("event_cause")["resolution_time_minutes"].transform("mean")
        df["historical_event_risk"] = cause_risk.round(1)

    # historical_location_risk: mean resolution time per corridor
    if "corridor" in df.columns:
        loc_risk = df.groupby("corridor")["resolution_time_minutes"].transform("mean")
        df["historical_location_risk"] = loc_risk.round(1)

    # peak_hour_incident_rate: share of incidents at each hour that fall in peak
    if "hour" in df.columns:
        hourly = df.groupby("hour").size()
        rate = (hourly / hourly.sum())
        df["hour_incident_rate"] = df["hour"].map(rate).round(4)
    return df


# ----------------------------------------------------------------------
# 6. Candidate targets + feasibility
# ----------------------------------------------------------------------
def build_targets(df):
    report = {}

    # Target A: resolution time (regression) -- already in df
    a = df["resolution_time_minutes"].notna().sum()
    report["A_resolution_time_regression"] = {
        "column": "resolution_time_minutes",
        "usable_rows": int(a),
        "note": "Available only where closed_datetime exists (~32% of rows).",
    }

    # Target B: severity classification (priority High/Low)
    if "priority" in df.columns:
        df["target_high_priority"] = (df["priority"] == "High").astype("Int64")
        b = df["target_high_priority"].notna().sum()
        pos = int((df["target_high_priority"] == 1).sum())
        report["B_severity_classification"] = {
            "column": "target_high_priority",
            "usable_rows": int(b),
            "positive_(High)": pos,
            "note": "Almost fully populated; well balanced (~62% High).",
        }

    # Target C: road closure classification
    if "requires_road_closure" in df.columns:
        df["target_road_closure"] = df["requires_road_closure"].astype("Int64")
        c = df["target_road_closure"].notna().sum()
        pos = int((df["target_road_closure"] == 1).sum())
        report["C_road_closure_classification"] = {
            "column": "target_road_closure",
            "usable_rows": int(c),
            "positive_(closure)": pos,
            "note": f"Fully populated but imbalanced (~{pos/len(df)*100:.0f}% positive).",
        }
    return df, report


# ----------------------------------------------------------------------
# 7. Drop unusable columns and assemble final modelling frame
# ----------------------------------------------------------------------
def finalize(df):
    # drop >90% missing
    drop_missing = [c for c in df.columns if df[c].isna().mean() > config.DROP_THRESHOLD]
    # drop known id/text/system columns that survived
    drop_ids = [c for c in config.ID_AND_TEXT_COLS if c in df.columns]
    # drop raw datetime strings (we extracted what we need)
    drop_dt = [c for c in config.DATETIME_COLS if c in df.columns]
    # raw categorical kept as *_frequency / encodings; drop the raw text ones
    drop_raw_cat = [c for c in ["zone", "gba_identifier", "status",
                                "cargo_material", "reason_breakdown", "veh_type",
                                "event_type", "authenticated", "priority",
                                "requires_road_closure", "direction"]
                    if c in df.columns]

    drop_all = sorted(set(drop_missing + drop_ids + drop_dt + drop_raw_cat))
    model_df = df.drop(columns=drop_all, errors="ignore")

    return model_df, drop_all, drop_missing


# ----------------------------------------------------------------------
def main():
    df = load_raw()
    df, start = add_time_features(df)
    df = add_duration_features(df, start)
    df = add_location_features(df)
    df = add_event_encodings(df)
    df = add_risk_features(df)
    df, target_report = build_targets(df)
    model_df, dropped, drop_missing = finalize(df)

    config.DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    model_df.to_csv(config.DATA_PROCESSED, index=False)

    print("=" * 70)
    print("FEATURE ENGINEERING COMPLETE")
    print("=" * 70)
    print(f"Raw shape         : {df.shape}")
    print(f"Modelling shape   : {model_df.shape}")
    print(f"Saved to          : {config.DATA_PROCESSED}")
    print(f"\nColumns dropped ({len(dropped)}):")
    print("  " + ", ".join(dropped))
    print(f"\nFinal modelling columns ({model_df.shape[1]}):")
    print("  " + ", ".join(model_df.columns))

    print("\n--- TARGET FEASIBILITY ---")
    for k, v in target_report.items():
        print(f"\n{k}")
        for kk, vv in v.items():
            print(f"   {kk}: {vv}")

    # Save a feature inventory CSV
    inv = pd.DataFrame({
        "feature": model_df.columns,
        "dtype": [str(model_df[c].dtype) for c in model_df.columns],
        "missing_pct": [(model_df[c].isna().mean() * 100).round(1) for c in model_df.columns],
        "n_unique": [model_df[c].nunique() for c in model_df.columns],
    })
    inv_path = config.DATA_PROCESSED_DIR / "feature_inventory.csv"
    inv.to_csv(inv_path, index=False)
    print(f"\n[OK] Feature inventory written to {inv_path}")


if __name__ == "__main__":
    main()
