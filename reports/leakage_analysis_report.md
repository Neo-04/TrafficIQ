# Leakage Analysis Report

**Features used for training (31):**

latitude, longitude, endlatitude, endlongitude, event_cause_encoded, hour, day_of_week, month, weekend_flag, peak_hour_flag, corridor_frequency, corridor_is_hotspot, junction_frequency, junction_is_hotspot, police_station_frequency, police_station_is_hotspot, is_planned, is_authenticated, event_cause_frequency, hour_incident_rate, veh_auto, veh_bmtc_bus, veh_heavy_vehicle, veh_ksrtc_bus, veh_lcv, veh_others, veh_private_bus, veh_private_car, veh_taxi, veh_truck, veh_unknown

**Excluded columns and why:**

| Column | Reason |
|---|---|
| resolution_time_minutes | Raw source of the resolution-time target. |
| res_time_binary | Alternate form of the resolution target. |
| res_time_band | The resolution target itself (string). |
| res_time_band_code | The resolution target itself (encoded). |
| target_high_priority | Removed severity label (administrative, not predictive). |
| severity | Removed severity label. |
| severity_label | Removed severity label. |
| target_road_closure | Co-outcome decided during/after response, not known at report time. |
| historical_event_risk | Mean resolution time per cause -> aggregate of the target (leak). |
| historical_location_risk | Mean resolution time per corridor -> aggregate of the target (leak). |
| location_risk_score | Composite of priority/closure/resolution -> aggregate of targets (leak). |
| location_risk_band | Banded location_risk_score (leak). |
| event_cause | Raw text -> replaced by event_cause_encoded. |
| corridor | Raw text -> represented by corridor_frequency / hotspot. |
| police_station | Raw text -> represented by police_station_frequency / hotspot. |
| junction | Raw text -> represented by junction_frequency / hotspot. |
