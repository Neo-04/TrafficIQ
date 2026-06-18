"""
app.py  --  PHASE 5: TrafficIQ Streamlit dashboard
==================================================
A local, no-backend dashboard for traffic operators. It REUSES the existing
project logic unchanged:
  * TrafficImpactPipeline  (predict_pipeline.py)  -> LightGBM resolution model
  * rules_engine.py        -> impact score, derived severity, resources

No retraining, no API, no database, no maps. Just a UI over what already exists.

Run from the project root:
    streamlit run src/app.py
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# make sure sibling modules (config, predict_pipeline, rules_engine) import
sys.path.append(str(Path(__file__).resolve().parent))
import config
from predict_pipeline import TrafficImpactPipeline

# ----------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------
st.set_page_config(page_title="TrafficIQ", page_icon="🚦", layout="wide")

st.markdown("""
<style>
.kpi {background:#1e293b;border-radius:14px;padding:18px 20px;color:#fff;
      border:1px solid #334155;height:100%;}
.kpi .label {font-size:0.8rem;color:#94a3b8;text-transform:uppercase;
      letter-spacing:.05em;margin-bottom:6px;}
.kpi .value {font-size:1.9rem;font-weight:700;line-height:1.1;}
.kpi .sub {font-size:0.85rem;color:#cbd5e1;margin-top:6px;}
.sev-Low{color:#22c55e;} .sev-Medium{color:#f59e0b;} .sev-High{color:#ef4444;}
</style>
""", unsafe_allow_html=True)

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SEV_COLOR = {"Low": "#22c55e", "Medium": "#f59e0b", "High": "#ef4444"}


# ----------------------------------------------------------------------
# Cached loaders (load model + option lists once)
# ----------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading model & lookups…")
def get_pipeline():
    return TrafficImpactPipeline()


@st.cache_data
def get_options():
    df = pd.read_csv(config.DATA_MODELING)
    causes = sorted(df["event_cause"].dropna().unique().tolist())
    corridors = sorted(df["corridor"].dropna().unique().tolist())
    import joblib
    feats = joblib.load(config.MODELS_DIR / "feature_list.pkl")
    vehicles = [f.replace("veh_", "") for f in feats if f.startswith("veh_")]
    return causes, corridors, vehicles


def pretty(s: str) -> str:
    return s.replace("_", " ").title()


# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
st.title("🚦 TrafficIQ")
st.caption("AI-Powered Event-Driven Traffic Impact Forecasting & Response "
           "Planning System")
st.write("TrafficIQ forecasts how long a reported incident will take to clear, "
         "then translates that forecast into an impact score, a severity level, "
         "and a recommended on-ground deployment — so operators can plan a "
         "response before congestion builds.")

pipe = get_pipeline()
causes, corridors, vehicles = get_options()

# ----------------------------------------------------------------------
# Sidebar inputs
# ----------------------------------------------------------------------
with st.sidebar:
    st.header("Incident details")
    event_cause = st.selectbox("Event Cause", causes,
                               index=causes.index("vehicle_breakdown")
                               if "vehicle_breakdown" in causes else 0,
                               format_func=pretty)
    corridor = st.selectbox("Corridor", corridors, format_func=pretty)
    vehicle_type = st.selectbox("Vehicle Type", vehicles,
                                index=vehicles.index("unknown")
                                if "unknown" in vehicles else 0,
                                format_func=pretty)
    hour = st.slider("Incident Hour", 0, 23, 9)
    day_name = st.selectbox("Day of Week", DAYS)
    forecast = st.button("Forecast Traffic Impact", type="primary",
                         use_container_width=True)

# ----------------------------------------------------------------------
# Prediction + output
# ----------------------------------------------------------------------
if forecast:
    res = pipe.predict(
        event_cause=event_cause,
        corridor=corridor,
        vehicle_type=vehicle_type,
        hour=hour,
        day_of_week=DAYS.index(day_name),
        month=1,
    )
    rc = res["predicted_resolution_class"]
    score = res["impact_score"]
    sev = res["severity"]
    r = res["recommended_resources"]
    sev_hex = SEV_COLOR.get(sev, "#fff")

    st.subheader("Forecast")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='kpi'><div class='label'>Resolution Class</div>"
                f"<div class='value'>{rc}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><div class='label'>Traffic Impact Score</div>"
                f"<div class='value'>{score}/100</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><div class='label'>Severity</div>"
                f"<div class='value' style='color:{sev_hex}'>{sev}</div></div>",
                unsafe_allow_html=True)
    res_lines = "<br>".join(
        f"{v} {pretty(k)}" for k, v in r.items() if v)
    c4.markdown(f"<div class='kpi'><div class='label'>Recommended Resources</div>"
                f"<div class='sub'>{res_lines or 'None'}</div></div>",
                unsafe_allow_html=True)

    st.divider()
    st.subheader("Incident Response Summary")
    bullets = "\n".join(f"- **{v}** {pretty(k)}" for k, v in r.items() if v)
    st.markdown(f"""
**Incident Cause:** {pretty(event_cause)}  
**Location (Corridor):** {pretty(corridor)}  
**Time:** {day_name}, {hour:02d}:00  

**Expected Resolution:** {rc}  
**Traffic Impact Score:** {score}/100  
**Severity:** :{ 'green' if sev=='Low' else 'orange' if sev=='Medium' else 'red' }[{sev}]  

**Recommended Deployment:**
{bullets if bullets else '- Minimal / standby'}
""")

    with st.expander("Raw model output (JSON)"):
        st.json(res)
else:
    st.info("Set the incident details in the sidebar and click "
            "**Forecast Traffic Impact**.")