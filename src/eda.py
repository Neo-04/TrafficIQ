"""
eda.py  --  PHASE 1: Historical Data Understanding
==================================================
Runs a complete exploratory analysis of the raw Bengaluru incident
dataset and writes:
  - a human-readable markdown report  -> reports/eda_report.md
  - key figures (PNG)                 -> reports/figures/

NO modelling, NO training. This script only understands the data.

Run from the project root:
    python src/eda.py
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless: write PNGs, never open a window
import matplotlib.pyplot as plt

import config

warnings.filterwarnings("ignore")
pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 50)


# ----------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------
def _line(title):
    """Return a markdown H2 header and also echo a console banner."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    return f"\n## {title}\n"


def load_raw():
    df = pd.read_csv(config.DATA_RAW, low_memory=False)
    return df


# ----------------------------------------------------------------------
# 1. Dataset overview
# ----------------------------------------------------------------------
def dataset_overview(df):
    md = _line("Dataset Overview")
    n_rows, n_cols = df.shape
    mem_mb = df.memory_usage(deep=True).sum() / 1024 ** 2
    print(f"Rows           : {n_rows:,}")
    print(f"Columns        : {n_cols}")
    print(f"Memory (deep)  : {mem_mb:.2f} MB")

    md += f"- **Rows:** {n_rows:,}\n"
    md += f"- **Columns:** {n_cols}\n"
    md += f"- **Memory (deep):** {mem_mb:.2f} MB\n\n"
    md += "| Column | Dtype |\n|---|---|\n"
    for c in df.columns:
        md += f"| {c} | {df[c].dtype} |\n"
    return md


# ----------------------------------------------------------------------
# 2. Missing value analysis + keep/impute/drop classification
# ----------------------------------------------------------------------
def missing_analysis(df):
    md = _line("Missing Value Analysis")
    miss_cnt = df.isna().sum()
    miss_pct = (df.isna().mean() * 100).round(2)
    out = pd.DataFrame({"missing_count": miss_cnt, "missing_pct": miss_pct})
    out = out.sort_values("missing_pct", ascending=False)

    def classify(p):
        if p > 90:
            return "DROP (>90% missing)"
        if p >= 30:
            return "IMPUTE / use with care"
        return "KEEP"

    out["recommendation"] = out["missing_pct"].apply(classify)
    print(out.to_string())

    md += "| Column | Missing | Missing % | Recommendation |\n|---|---|---|---|\n"
    for col, row in out.iterrows():
        md += f"| {col} | {int(row.missing_count)} | {row.missing_pct} | {row.recommendation} |\n"

    drop_cols = out[out.recommendation.str.startswith("DROP")].index.tolist()

    # figure: top-20 missingness bar
    top = out.head(20)
    plt.figure(figsize=(9, 7))
    plt.barh(top.index[::-1], top.missing_pct[::-1], color="#c0392b")
    plt.xlabel("Missing %")
    plt.title("Top 20 columns by missingness")
    plt.tight_layout()
    plt.savefig(config.FIGURES_DIR / "missing_values.png", dpi=110)
    plt.close()
    return md, drop_cols


# ----------------------------------------------------------------------
# 3. Categorical analysis
# ----------------------------------------------------------------------
def categorical_analysis(df):
    md = _line("Categorical Feature Analysis")
    focus = ["event_type", "event_cause", "priority", "status",
             "police_station", "junction", "corridor", "veh_type",
             "requires_road_closure", "authenticated", "zone",
             "gba_identifier", "direction"]
    focus = [c for c in focus if c in df.columns]

    for c in focus:
        nun = df[c].nunique(dropna=True)
        print(f"\n--- {c} (unique={nun}) ---")
        vc = df[c].value_counts(dropna=False).head(8)
        print(vc.to_string())
        md += f"\n### {c}  (unique = {nun})\n\n| Value | Count |\n|---|---|\n"
        for val, cnt in vc.items():
            md += f"| {val} | {cnt} |\n"

    # figure: event_cause distribution
    if "event_cause" in df.columns:
        vc = df["event_cause"].value_counts().head(12)
        plt.figure(figsize=(9, 6))
        plt.barh(vc.index[::-1], vc.values[::-1], color="#2c3e50")
        plt.xlabel("Incident count")
        plt.title("Incidents by cause (top 12)")
        plt.tight_layout()
        plt.savefig(config.FIGURES_DIR / "event_cause.png", dpi=110)
        plt.close()
    return md


# ----------------------------------------------------------------------
# 4. Numerical analysis + outliers
# ----------------------------------------------------------------------
def numerical_analysis(df):
    md = _line("Numerical Feature Analysis")
    num = df.select_dtypes(include=[np.number])
    # drop all-empty numeric columns from this view
    num = num.loc[:, num.notna().any()]
    desc = num.describe().T
    desc["median"] = num.median()

    # IQR outlier count per column
    out_counts = {}
    for c in num.columns:
        q1, q3 = num[c].quantile(0.25), num[c].quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        out_counts[c] = int(((num[c] < lo) | (num[c] > hi)).sum())
    desc["outliers_iqr"] = pd.Series(out_counts)
    print(desc[["mean", "median", "std", "min", "max", "outliers_iqr"]].to_string())

    md += "| Column | Mean | Median | Std | Min | Max | IQR outliers |\n|---|---|---|---|---|---|---|\n"
    for c, r in desc.iterrows():
        md += (f"| {c} | {r['mean']:.4g} | {r['median']:.4g} | {r['std']:.4g} "
               f"| {r['min']:.4g} | {r['max']:.4g} | {int(r['outliers_iqr'])} |\n")
    md += ("\n*Note: most numeric columns are coordinates or system IDs, "
           "not true predictive measures. The meaningful numeric signal is "
           "created in feature engineering (resolution_time_minutes).*\n")
    return md


# ----------------------------------------------------------------------
# 5. Date / time analysis + duration feasibility
# ----------------------------------------------------------------------
def datetime_analysis(df):
    md = _line("Date and Time Analysis")
    parsed = {}
    md += "| Column | Parsed non-null | Missing % | Earliest | Latest |\n|---|---|---|---|---|\n"
    for c in config.DATETIME_COLS:
        if c not in df.columns:
            continue
        s = pd.to_datetime(df[c], errors="coerce", utc=True)
        parsed[c] = s
        miss = (s.isna().mean() * 100)
        print(f"{c:18s} non-null={s.notna().sum():5d}  miss={miss:5.1f}%  "
              f"range {s.min()} -> {s.max()}")
        md += f"| {c} | {s.notna().sum()} | {miss:.1f} | {s.min()} | {s.max()} |\n"

    start = parsed.get("start_datetime")
    closed = parsed.get("closed_datetime")
    end = parsed.get("end_datetime")

    md += "\n**Duration feasibility:**\n"
    if start is not None and closed is not None:
        res = (closed - start).dt.total_seconds() / 60
        ok = res[(res > 0) & (res < config.MAX_RESOLUTION_MINUTES)]
        msg = (f"resolution_time = closed_datetime - start_datetime is "
               f"computable for **{ok.notna().sum():,} rows** "
               f"(median {ok.median():.0f} min).")
        print("\n" + msg)
        md += f"- {msg}\n"
    if start is not None and end is not None:
        ev = (end - start).dt.total_seconds() / 60
        ok2 = ev[(ev > 0) & (ev < config.MAX_RESOLUTION_MINUTES)]
        msg2 = (f"event_duration = end_datetime - start_datetime is "
                f"computable for only **{ok2.notna().sum():,} rows** "
                f"(end_datetime is ~94% missing, so this is unreliable).")
        print(msg2)
        md += f"- {msg2}\n"
    return md


# ----------------------------------------------------------------------
# 6. Geographic / hotspot analysis
# ----------------------------------------------------------------------
def geographic_analysis(df):
    md = _line("Geographic Analysis (Hotspots)")
    for col, label in [("corridor", "Hotspot corridors"),
                       ("junction", "Hotspot junctions"),
                       ("police_station", "Busiest police stations")]:
        if col not in df.columns:
            continue
        vc = df[col].value_counts().head(10)
        print(f"\n--- {label} ---")
        print(vc.to_string())
        md += f"\n### {label}\n\n| {col} | Incidents |\n|---|---|\n"
        for v, c in vc.items():
            md += f"| {v} | {c} |\n"

    if {"latitude", "longitude"}.issubset(df.columns):
        geo = df.dropna(subset=["latitude", "longitude"])
        plt.figure(figsize=(7, 7))
        plt.scatter(geo["longitude"], geo["latitude"], s=4, alpha=0.25,
                    color="#16a085")
        plt.xlabel("Longitude"); plt.ylabel("Latitude")
        plt.title("Incident locations (Bengaluru)")
        plt.tight_layout()
        plt.savefig(config.FIGURES_DIR / "geo_scatter.png", dpi=110)
        plt.close()
    return md


# ----------------------------------------------------------------------
# 7. Planned vs unplanned + cause-level patterns
# ----------------------------------------------------------------------
def planned_unplanned(df):
    md = _line("Planned vs Unplanned Events")
    if "event_type" in df.columns:
        vc = df["event_type"].value_counts(dropna=False)
        pct = (vc / len(df) * 100).round(1)
        print(vc.to_string()); print(pct.to_string())
        md += "| event_type | Count | % |\n|---|---|---|\n"
        for k in vc.index:
            md += f"| {k} | {vc[k]} | {pct[k]} |\n"
    return md


def cause_patterns(df, res_minutes):
    md = _line("Incident Cause Analysis")
    if "event_cause" not in df.columns:
        return md
    tmp = df.copy()
    tmp["_res"] = res_minutes
    tmp["_highprio"] = (tmp.get("priority") == "High").astype(float)
    tmp["_closure"] = tmp.get("requires_road_closure").astype(float) \
        if "requires_road_closure" in tmp else np.nan
    g = tmp.groupby("event_cause").agg(
        count=("event_cause", "size"),
        avg_resolution_min=("_res", "mean"),
        pct_high_priority=("_highprio", "mean"),
        pct_road_closure=("_closure", "mean"),
    ).sort_values("count", ascending=False)
    g["avg_resolution_min"] = g["avg_resolution_min"].round(0)
    g["pct_high_priority"] = (g["pct_high_priority"] * 100).round(1)
    g["pct_road_closure"] = (g["pct_road_closure"] * 100).round(1)
    print(g.to_string())
    md += "| Cause | Count | Avg resolution (min) | % High priority | % Road closure |\n|---|---|---|---|---|\n"
    for c, r in g.iterrows():
        md += (f"| {c} | {int(r['count'])} | {r['avg_resolution_min']} "
               f"| {r['pct_high_priority']} | {r['pct_road_closure']} |\n")
    return md


# ----------------------------------------------------------------------
# 8. Correlation (numeric + a few engineered-for-EDA signals)
# ----------------------------------------------------------------------
def correlation_analysis(df, res_minutes):
    md = _line("Correlation Analysis")
    tmp = pd.DataFrame()
    tmp["resolution_min"] = res_minutes
    if "priority" in df:
        tmp["high_priority"] = (df["priority"] == "High").astype(int)
    if "requires_road_closure" in df:
        tmp["road_closure"] = df["requires_road_closure"].astype(int)
    if "authenticated" in df:
        tmp["authenticated"] = (df["authenticated"] == "yes").astype(int)
    if "event_type" in df:
        tmp["is_planned"] = (df["event_type"] == "planned").astype(int)
    start = pd.to_datetime(df.get("start_datetime"), errors="coerce", utc=True)
    tmp["hour"] = start.dt.hour
    tmp["dow"] = start.dt.dayofweek

    corr = tmp.corr(numeric_only=True)
    print(corr.round(2).to_string())
    md += "Correlation between key engineered signals:\n\n"
    md += "| | " + " | ".join(corr.columns) + " |\n"
    md += "|" + "---|" * (len(corr.columns) + 1) + "\n"
    for idx, row in corr.iterrows():
        md += f"| {idx} | " + " | ".join(f"{v:.2f}" for v in row) + " |\n"

    plt.figure(figsize=(7, 6))
    plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    plt.xticks(range(len(corr)), corr.columns, rotation=45, ha="right")
    plt.yticks(range(len(corr)), corr.columns)
    plt.colorbar(label="Pearson r")
    plt.title("Correlation matrix (key signals)")
    plt.tight_layout()
    plt.savefig(config.FIGURES_DIR / "correlation.png", dpi=110)
    plt.close()
    return md


# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------
def main():
    df = load_raw()
    start = pd.to_datetime(df.get("start_datetime"), errors="coerce", utc=True)
    closed = pd.to_datetime(df.get("closed_datetime"), errors="coerce", utc=True)
    res_minutes = (closed - start).dt.total_seconds() / 60
    res_minutes = res_minutes.where((res_minutes > 0) &
                                    (res_minutes < config.MAX_RESOLUTION_MINUTES))

    report = "# Phase 1 - EDA Report\n"
    report += "Bengaluru Event-Driven Traffic Impact dataset\n"

    report += dataset_overview(df)
    md_missing, drop_cols = missing_analysis(df)
    report += md_missing
    report += categorical_analysis(df)
    report += numerical_analysis(df)
    report += datetime_analysis(df)
    report += geographic_analysis(df)
    report += planned_unplanned(df)
    report += cause_patterns(df, res_minutes)
    report += correlation_analysis(df, res_minutes)

    # Deliverable summary block
    report += _line("Phase 1 Deliverables Summary")
    report += (
        f"- **Drop candidates (>90% missing):** {', '.join(drop_cols)}\n"
        "- **Key data-quality issues:** end_datetime ~94% missing and contains "
        "future-dated garbage; resolution_time only available for the ~38% of "
        "rows that have closed_datetime; dataset is dominated by unplanned "
        "vehicle_breakdown events; road_closure target is imbalanced (~8% positive).\n"
        "- **Strong columns to keep:** event_cause, corridor, police_station, "
        "priority, requires_road_closure, start_datetime, latitude/longitude.\n"
    )

    config.EDA_REPORT.write_text(report, encoding="utf-8")
    print(f"\n[OK] EDA report written to {config.EDA_REPORT}")
    print(f"[OK] Figures written to {config.FIGURES_DIR}")


if __name__ == "__main__":
    main()
