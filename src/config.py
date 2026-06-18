"""
config.py
---------
Central place for paths and constants used across the EDA and
feature-engineering scripts. Keeping these here means no other file
hard-codes a path, so the project still runs if you move it.
"""

from pathlib import Path

# ---- Paths -----------------------------------------------------------
# PROJECT_ROOT resolves to the traffic_impact_forecasting/ folder
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = PROJECT_ROOT / "data" / "raw" / "incidents_raw.csv"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_PROCESSED = DATA_PROCESSED_DIR / "incidents_features.csv"
DATA_MODELING = DATA_PROCESSED_DIR / "incidents_modeling.csv"

MODELS_DIR = PROJECT_ROOT / "models"
PLOTS_DIR = PROJECT_ROOT / "plots"

# Reproducibility / split settings for Phase 3
RANDOM_STATE = 42
TEST_SIZE = 0.20
CV_SPLITS = 5

# ---- Phase 4: rule-based layers (replace the removed severity model) ----
# ---- Phase 4: rule-based layers ----
IMPACT_SCORE_MAP = {"Quick": 30, "Moderate": 60, "Prolonged": 90}
RESOLUTION_TO_SEVERITY = {"Quick": "Low", "Moderate": "Medium", "Prolonged": "High"}
RESOURCE_RULES = {
    "Low":    {"officers": 2, "barricades": 2,  "marshals": 1, "tow_trucks": 0},
    "Medium": {"officers": 4, "barricades": 6,  "marshals": 3, "tow_trucks": 1},
    "High":   {"officers": 8, "barricades": 12, "marshals": 6, "tow_trucks": 2},
}
TOW_TRUCK_CAUSES = ["vehicle_breakdown", "accident"]

REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
EDA_REPORT = REPORTS_DIR / "eda_report.md"

# ---- Analysis constants ---------------------------------------------
# Columns that are >90% empty are dropped automatically in FE.
DROP_THRESHOLD = 0.90

# Peak-hour windows (24h clock) as given in the project spec.
PEAK_MORNING = (7, 11)    # 7 AM - 11 AM inclusive of start, exclusive of end
PEAK_EVENING = (16, 21)   # 4 PM - 9 PM

# Columns we already know are pure system identifiers / free text and
# are never used as model features. Listed here so both scripts agree.
ID_AND_TEXT_COLS = [
    "id", "client_id", "created_by_id", "last_modified_by_id",
    "assigned_to_police_id", "citizen_accident_id", "closed_by_id",
    "resolved_by_id", "kgid", "veh_no", "description",
    "address", "end_address", "resolved_at_address", "map_file",
    "comment", "meta_data", "route_path",
]

# Datetime columns to attempt parsing.
DATETIME_COLS = [
    "start_datetime", "end_datetime", "closed_datetime",
    "resolved_datetime", "created_date", "modified_datetime",
]

# A sane upper bound on resolution time (minutes). Anything above this is
# treated as a data error (e.g. a record left open for weeks). 3 days.
MAX_RESOLUTION_MINUTES = 3 * 24 * 60

# ---- Target definitions ---------------------------------------------
# These were chosen from the EDA to maximise learnability. Edit here if
# you want to re-band or re-weight; both scripts read from this file.

# TARGET 1 - Resolution time.
# Binary split (most balanced / most accurate first model):
RES_BINARY_THRESHOLD_MIN = 60          # <=60 min -> Quick, else Prolonged
# 3-class band (more operationally useful):
RES_BAND_EDGES = [0, 60, 240, float("inf")]
RES_BAND_LABELS = ["Quick", "Moderate", "Prolonged"]   # <=1h / 1-4h / >4h

# TARGET 3 - Location risk score (a COMPUTED index, not a model target).
# Aggregation level and component weights (must sum to 1.0).
LOCATION_RISK_LEVEL = "corridor"       # could be "junction" or "police_station"
LOCATION_RISK_WEIGHTS = {
    "frequency": 0.40,                 # how often incidents happen here
    "avg_resolution": 0.25,            # how long they take to clear
    "pct_high_priority": 0.20,         # how severe they tend to be
    "pct_road_closure": 0.15,          # how often they force a closure
}
MIN_INCIDENTS_FOR_RISK = 10            # ignore locations with too few incidents
# Catch-all / non-real location buckets to exclude from the risk index.
EXCLUDE_LOCATIONS = ["Non-corridor"] 
RISK_BAND_LABELS = ["Low", "Medium", "High", "Critical"]   # quartile bands
