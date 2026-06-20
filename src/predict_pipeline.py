"""
predict_pipeline.py  --  PHASE 4: End-to-end inference
======================================================
User inputs -> feature assembly -> LightGBM resolution model
            -> impact score -> derived severity -> resource recommendation
            -> final response dict.

Lookups (corridor/junction/station frequencies, hotspot flags, hour rate,
event-cause encoding, corridor centroids) are rebuilt from the prepared
modelling CSV so the pipeline is self-contained and executable.

Run a demo from the project root (after train_models.py):
    python src/predict_pipeline.py
"""

import joblib
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

import config
import rules_engine


class TrafficImpactPipeline:
    def __init__(self):
        self.model = joblib.load(config.MODELS_DIR / "resolution_time_model.pkl")
        self.features = joblib.load(config.MODELS_DIR / "feature_list.pkl")
        enc = joblib.load(config.MODELS_DIR / "label_encoders.pkl")
        self.cause_enc = enc["event_cause"]
        self.res_enc = enc["resolution_time_class"]
        self._build_lookups()

    # ---- build inference lookups from the prepared dataset ----
    def _build_lookups(self):
        df = pd.read_csv(config.DATA_MODELING)
        self.defaults = {f: float(np.nanmedian(pd.to_numeric(df[f], errors="coerce")))
                         if f in df.columns else 0.0 for f in self.features}

        def first_map(key, val):
            return df.dropna(subset=[key]).groupby(key)[val].first().to_dict()

        self.corr_freq = first_map("corridor", "corridor_frequency")
        self.corr_hot = first_map("corridor", "corridor_is_hotspot")
        self.junc_freq = first_map("junction", "junction_frequency")
        self.junc_hot = first_map("junction", "junction_is_hotspot")
        self.ps_freq = first_map("police_station", "police_station_frequency")
        self.ps_hot = first_map("police_station", "police_station_is_hotspot")
        self.cause_freq = first_map("event_cause", "event_cause_frequency")
        self.hour_rate = df.dropna(subset=["hour"]).groupby("hour")["hour_incident_rate"].first().to_dict()
        # corridor centroids for lat/long fallback
        self.corr_lat = df.groupby("corridor")["latitude"].mean().to_dict()
        self.corr_lng = df.groupby("corridor")["longitude"].mean().to_dict()
        self.glob_lat = float(df["latitude"].mean())
        self.glob_lng = float(df["longitude"].mean())

    def _encode_cause(self, cause):
        classes = list(self.cause_enc.classes_)
        return int(self.cause_enc.transform([cause])[0]) if cause in classes else -1

    def _peak(self, hour):
        pm0, pm1 = config.PEAK_MORNING
        pe0, pe1 = config.PEAK_EVENING
        return int((pm0 <= hour < pm1) or (pe0 <= hour < pe1))

    # ---- main entry point ----
    def predict(self, event_cause, corridor=None, police_station=None,
                junction=None, hour=9, day_of_week=0, month=1,
                vehicle_type=None, latitude=None, longitude=None,
                is_planned=0, is_authenticated=1):
        row = dict(self.defaults)  # start from sensible medians

        row["event_cause_encoded"] = self._encode_cause(event_cause)
        row["event_cause_frequency"] = self.cause_freq.get(event_cause, 0)
        row["hour"] = hour
        row["day_of_week"] = day_of_week
        row["month"] = month
        row["weekend_flag"] = int(day_of_week >= 5)
        row["peak_hour_flag"] = self._peak(hour)
        row["hour_incident_rate"] = self.hour_rate.get(float(hour), self.defaults.get("hour_incident_rate", 0))
        row["is_planned"] = int(is_planned)
        row["is_authenticated"] = int(is_authenticated)

        row["corridor_frequency"] = self.corr_freq.get(corridor, 0)
        row["corridor_is_hotspot"] = self.corr_hot.get(corridor, 0)
        row["junction_frequency"] = self.junc_freq.get(junction, 0)
        row["junction_is_hotspot"] = self.junc_hot.get(junction, 0)
        row["police_station_frequency"] = self.ps_freq.get(police_station, 0)
        row["police_station_is_hotspot"] = self.ps_hot.get(police_station, 0)

        row["latitude"] = latitude if latitude is not None else self.corr_lat.get(corridor, self.glob_lat)
        row["longitude"] = longitude if longitude is not None else self.corr_lng.get(corridor, self.glob_lng)
        row["endlatitude"] = row["latitude"]
        row["endlongitude"] = row["longitude"]

        # vehicle one-hots
        for f in self.features:
            if f.startswith("veh_"):
                row[f] = 0
        vt = f"veh_{vehicle_type}" if vehicle_type else "veh_unknown"
        if vt in row:
            row[vt] = 1
        elif "veh_unknown" in row:
            row["veh_unknown"] = 1

        x = np.array([[float(row[f]) for f in self.features]])
        preds = self.model.predict(x)
        cls_idx = int(np.argmax(preds[0]))
        resolution_class = self.res_enc.inverse_transform([cls_idx])[0]

        response = rules_engine.build_response(resolution_class, event_cause=event_cause)
        response["inputs"] = {
            "event_cause": event_cause, "corridor": corridor,
            "police_station": police_station, "hour": hour,
            "day_of_week": day_of_week, "vehicle_type": vehicle_type,
        }
        return response


if __name__ == "__main__":
    pipe = TrafficImpactPipeline()
    examples = [
        dict(event_cause="vehicle_breakdown", corridor="Mysore Road",
             police_station=None, hour=18, day_of_week=2, vehicle_type="heavy_vehicle"),
        dict(event_cause="construction", corridor="ORR East 1",
             hour=10, day_of_week=5, vehicle_type=None),
        dict(event_cause="water_logging", corridor="Bellary Road 1",
             hour=8, day_of_week=1, vehicle_type=None),
        dict(event_cause="vehicle_breakdown", corridor="Mysore Road",
             police_station="Yeshwanthpura", hour=18, day_of_week=2,
             vehicle_type="heavy_vehicle"),
    ]
    import json
    for ex in examples:
        print(json.dumps(pipe.predict(**ex), indent=2, default=str))
        print("-" * 60)