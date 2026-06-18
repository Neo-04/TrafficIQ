# Phase 1 - EDA Report
Bengaluru Event-Driven Traffic Impact dataset

## Dataset Overview
- **Rows:** 8,173
- **Columns:** 46
- **Memory (deep):** 14.90 MB

| Column | Dtype |
|---|---|
| id | object |
| event_type | object |
| latitude | float64 |
| longitude | float64 |
| endlatitude | float64 |
| endlongitude | float64 |
| address | object |
| end_address | object |
| event_cause | object |
| requires_road_closure | bool |
| start_datetime | object |
| end_datetime | object |
| status | object |
| authenticated | object |
| modified_datetime | object |
| map_file | float64 |
| direction | object |
| description | object |
| veh_type | object |
| veh_no | object |
| corridor | object |
| priority | object |
| cargo_material | object |
| reason_breakdown | object |
| age_of_truck | float64 |
| created_date | object |
| route_path | object |
| client_id | int64 |
| created_by_id | object |
| last_modified_by_id | object |
| assigned_to_police_id | object |
| citizen_accident_id | object |
| comment | float64 |
| police_station | object |
| meta_data | float64 |
| kgid | object |
| resolved_at_address | object |
| resolved_at_latitude | float64 |
| resolved_at_longitude | float64 |
| closed_by_id | object |
| closed_datetime | object |
| resolved_by_id | object |
| resolved_datetime | object |
| gba_identifier | object |
| zone | object |
| junction | object |

## Missing Value Analysis
| Column | Missing | Missing % | Recommendation |
|---|---|---|---|
| meta_data | 8173 | 100.0 | DROP (>90% missing) |
| comment | 8173 | 100.0 | DROP (>90% missing) |
| map_file | 8173 | 100.0 | DROP (>90% missing) |
| direction | 8130 | 99.47 | DROP (>90% missing) |
| resolved_at_longitude | 8099 | 99.09 | DROP (>90% missing) |
| resolved_at_latitude | 8099 | 99.09 | DROP (>90% missing) |
| resolved_at_address | 8099 | 99.09 | DROP (>90% missing) |
| resolved_by_id | 8099 | 99.09 | DROP (>90% missing) |
| resolved_datetime | 8099 | 99.09 | DROP (>90% missing) |
| citizen_accident_id | 8045 | 98.43 | DROP (>90% missing) |
| assigned_to_police_id | 8045 | 98.43 | DROP (>90% missing) |
| route_path | 8036 | 98.32 | DROP (>90% missing) |
| cargo_material | 7897 | 96.62 | DROP (>90% missing) |
| age_of_truck | 7897 | 96.62 | DROP (>90% missing) |
| reason_breakdown | 7897 | 96.62 | DROP (>90% missing) |
| end_datetime | 7683 | 94.0 | DROP (>90% missing) |
| end_address | 7486 | 91.59 | DROP (>90% missing) |
| junction | 5663 | 69.29 | IMPUTE / use with care |
| closed_by_id | 5032 | 61.57 | IMPUTE / use with care |
| closed_datetime | 5032 | 61.57 | IMPUTE / use with care |
| zone | 4729 | 57.86 | IMPUTE / use with care |
| gba_identifier | 4729 | 57.86 | IMPUTE / use with care |
| veh_no | 3287 | 40.22 | IMPUTE / use with care |
| veh_type | 3286 | 40.21 | IMPUTE / use with care |
| description | 1360 | 16.64 | KEEP |
| kgid | 259 | 3.17 | KEEP |
| endlongitude | 169 | 2.07 | KEEP |
| endlatitude | 169 | 2.07 | KEEP |
| corridor | 20 | 0.24 | KEEP |
| address | 3 | 0.04 | KEEP |
| last_modified_by_id | 3 | 0.04 | KEEP |
| created_by_id | 2 | 0.02 | KEEP |
| priority | 2 | 0.02 | KEEP |
| latitude | 0 | 0.0 | KEEP |
| longitude | 0 | 0.0 | KEEP |
| requires_road_closure | 0 | 0.0 | KEEP |
| event_cause | 0 | 0.0 | KEEP |
| police_station | 0 | 0.0 | KEEP |
| start_datetime | 0 | 0.0 | KEEP |
| status | 0 | 0.0 | KEEP |
| client_id | 0 | 0.0 | KEEP |
| authenticated | 0 | 0.0 | KEEP |
| created_date | 0 | 0.0 | KEEP |
| modified_datetime | 0 | 0.0 | KEEP |
| event_type | 0 | 0.0 | KEEP |
| id | 0 | 0.0 | KEEP |

## Categorical Feature Analysis

### event_type  (unique = 2)

| Value | Count |
|---|---|
| unplanned | 7706 |
| planned | 467 |

### event_cause  (unique = 17)

| Value | Count |
|---|---|
| vehicle_breakdown | 4896 |
| others | 638 |
| pot_holes | 537 |
| construction | 480 |
| water_logging | 458 |
| accident | 365 |
| tree_fall | 284 |
| road_conditions | 170 |

### priority  (unique = 2)

| Value | Count |
|---|---|
| High | 5030 |
| Low | 3141 |
| nan | 2 |

### status  (unique = 3)

| Value | Count |
|---|---|
| closed | 7095 |
| active | 1007 |
| resolved | 71 |

### police_station  (unique = 54)

| Value | Count |
|---|---|
| Yelahanka | 377 |
| HAL Old Airport | 361 |
| Sadashivanagar | 302 |
| Halasuru Gate | 297 |
| Byatarayanapura | 297 |
| Yeshwanthpura | 280 |
| Hennuru | 276 |
| Kodigehalli | 272 |

### junction  (unique = 294)

| Value | Count |
|---|---|
| nan | 5663 |
| MekhriCircle | 64 |
| AyyappaTempleJunc | 49 |
| SatteliteBusStandJunc | 43 |
| YeshwanthpuraCircle | 38 |
| YelhankaCircle | 34 |
| toll gate mysore road | 33 |
| SilkBoardJunc | 33 |

### corridor  (unique = 22)

| Value | Count |
|---|---|
| Non-corridor | 3124 |
| Mysore Road | 743 |
| Bellary Road 1 | 610 |
| Tumkur Road | 458 |
| Bellary Road 2 | 379 |
| Hosur Road | 298 |
| ORR North 1 | 275 |
| Old Madras Road | 263 |

### veh_type  (unique = 10)

| Value | Count |
|---|---|
| nan | 3286 |
| bmtc_bus | 1466 |
| heavy_vehicle | 965 |
| lcv | 678 |
| others | 449 |
| private_bus | 359 |
| private_car | 345 |
| truck | 276 |

### requires_road_closure  (unique = 2)

| Value | Count |
|---|---|
| False | 7497 |
| True | 676 |

### authenticated  (unique = 2)

| Value | Count |
|---|---|
| yes | 7166 |
| no | 1007 |

### zone  (unique = 10)

| Value | Count |
|---|---|
| nan | 4729 |
| Central Zone 2 | 623 |
| West Zone 1 | 433 |
| North Zone 2 | 413 |
| West Zone 2 | 358 |
| South Zone 2 | 354 |
| North Zone 1 | 318 |
| Central Zone 1 | 269 |

### gba_identifier  (unique = 5)

| Value | Count |
|---|---|
| nan | 4729 |
| Bengaluru Central Corporation | 892 |
| Bengaluru West Corporation | 791 |
| Bengaluru North Corporation | 731 |
| Bengaluru South Corporation | 587 |
| Bengaluru East Corporation | 443 |

### direction  (unique = 8)

| Value | Count |
|---|---|
| nan | 8130 |
| south_west | 12 |
| north_west | 10 |
| west | 8 |
| south | 7 |
| north | 2 |
| north_east | 2 |
| east | 1 |

## Numerical Feature Analysis
| Column | Mean | Median | Std | Min | Max | IQR outliers |
|---|---|---|---|---|---|---|
| latitude | 12.99 | 12.98 | 0.06011 | 12.8 | 13.27 | 145 |
| longitude | 77.6 | 77.59 | 0.06119 | 77.31 | 77.77 | 312 |
| endlatitude | 1.128 | 0 | 3.737 | 0 | 59.86 | 689 |
| endlongitude | 6.678 | 0 | 21.76 | 0 | 80.72 | 689 |
| age_of_truck | 235.5 | 10 | 634.1 | 0 | 2026 | 37 |
| client_id | 1.01 | 1 | 0.09846 | 1 | 2 | 80 |
| resolved_at_latitude | 13 | 12.98 | 0.09138 | 12.84 | 13.26 | 8 |
| resolved_at_longitude | 77.57 | 77.56 | 0.05725 | 77.39 | 77.71 | 12 |

*Note: most numeric columns are coordinates or system IDs, not true predictive measures. The meaningful numeric signal is created in feature engineering (resolution_time_minutes).*

## Date and Time Analysis
| Column | Parsed non-null | Missing % | Earliest | Latest |
|---|---|---|---|---|
| start_datetime | 8057 | 1.4 | 2023-11-09 19:24:48.154000+00:00 | 2024-04-08 17:11:42.780000+00:00 |
| end_datetime | 475 | 94.2 | 2023-11-12 02:05:46+00:00 | 2027-11-09 11:35:46+00:00 |
| closed_datetime | 3141 | 61.6 | 2023-11-09 22:48:37.836256+00:00 | 2024-04-20 06:16:08.118135+00:00 |
| resolved_datetime | 74 | 99.1 | 2023-11-10 07:21:41.463359+00:00 | 2024-04-02 22:33:50.469479+00:00 |
| created_date | 8171 | 0.0 | 2023-09-29 23:38:19.342539+00:00 | 2024-04-08 17:22:58.849385+00:00 |
| modified_datetime | 8173 | 0.0 | 2023-11-09 20:35:47.789399+00:00 | 2024-04-20 06:16:08.264418+00:00 |

**Duration feasibility:**
- resolution_time = closed_datetime - start_datetime is computable for **2,588 rows** (median 49 min).
- event_duration = end_datetime - start_datetime is computable for only **286 rows** (end_datetime is ~94% missing, so this is unreliable).

## Geographic Analysis (Hotspots)

### Hotspot corridors

| corridor | Incidents |
|---|---|
| Non-corridor | 3124 |
| Mysore Road | 743 |
| Bellary Road 1 | 610 |
| Tumkur Road | 458 |
| Bellary Road 2 | 379 |
| Hosur Road | 298 |
| ORR North 1 | 275 |
| Old Madras Road | 263 |
| Magadi Road | 245 |
| ORR East 1 | 244 |

### Hotspot junctions

| junction | Incidents |
|---|---|
| MekhriCircle | 64 |
| AyyappaTempleJunc | 49 |
| SatteliteBusStandJunc | 43 |
| YeshwanthpuraCircle | 38 |
| YelhankaCircle | 34 |
| toll gate mysore road | 33 |
| SilkBoardJunc | 33 |
| JalahalliCross(SM Circle) | 32 |
| Nagavara-ORR Junction | 32 |
| K R Circle | 31 |

### Busiest police stations

| police_station | Incidents |
|---|---|
| Yelahanka | 377 |
| HAL Old Airport | 361 |
| Sadashivanagar | 302 |
| Halasuru Gate | 297 |
| Byatarayanapura | 297 |
| Yeshwanthpura | 280 |
| Hennuru | 276 |
| Kodigehalli | 272 |
| Banaswadi | 245 |
| K.R. Pura | 228 |

## Planned vs Unplanned Events
| event_type | Count | % |
|---|---|---|
| unplanned | 7706 | 94.3 |
| planned | 467 | 5.7 |

## Incident Cause Analysis
| Cause | Count | Avg resolution (min) | % High priority | % Road closure |
|---|---|---|---|---|
| vehicle_breakdown | 4896 | 50.0 | 66.2 | 4.3 |
| others | 638 | 554.0 | 59.6 | 8.6 |
| pot_holes | 537 | 1121.0 | 55.7 | 2.4 |
| construction | 480 | 799.0 | 62.9 | 26.5 |
| water_logging | 458 | 847.0 | 59.2 | 8.5 |
| accident | 365 | 48.0 | 46.0 | 3.0 |
| tree_fall | 284 | 636.0 | 32.7 | 39.4 |
| road_conditions | 170 | 654.0 | 54.7 | 12.4 |
| congestion | 136 | 75.0 | 69.1 | 4.4 |
| public_event | 84 | nan | 50.0 | 46.4 |
| procession | 72 | 55.0 | 31.9 | 26.4 |
| vip_movement | 20 | nan | 35.0 | 80.0 |
| protest | 15 | 24.0 | 40.0 | 40.0 |
| Debris | 12 | nan | 66.7 | 8.3 |
| test_demo | 3 | 2.0 | 33.3 | 0.0 |
| Fog / Low Visibility | 2 | nan | 50.0 | 0.0 |
| debris | 1 | nan | 100.0 | 100.0 |

## Correlation Analysis
Correlation between key engineered signals:

| | resolution_min | high_priority | road_closure | authenticated | is_planned | hour | dow |
|---|---|---|---|---|---|---|---|
| resolution_min | 1.00 | -0.06 | 0.04 | 0.17 | 0.02 | 0.04 | -0.02 |
| high_priority | -0.06 | 1.00 | -0.11 | -0.01 | -0.01 | -0.02 | 0.00 |
| road_closure | 0.04 | -0.11 | 1.00 | 0.01 | 0.25 | -0.01 | 0.00 |
| authenticated | 0.17 | -0.01 | 0.01 | 1.00 | 0.05 | 0.08 | -0.01 |
| is_planned | 0.02 | -0.01 | 0.25 | 0.05 | 1.00 | 0.07 | -0.02 |
| hour | 0.04 | -0.02 | -0.01 | 0.08 | 0.07 | 1.00 | -0.13 |
| dow | -0.02 | 0.00 | 0.00 | -0.01 | -0.02 | -0.13 | 1.00 |

## Phase 1 Deliverables Summary
- **Drop candidates (>90% missing):** meta_data, comment, map_file, direction, resolved_at_longitude, resolved_at_latitude, resolved_at_address, resolved_by_id, resolved_datetime, citizen_accident_id, assigned_to_police_id, route_path, cargo_material, age_of_truck, reason_breakdown, end_datetime, end_address
- **Key data-quality issues:** end_datetime ~94% missing and contains future-dated garbage; resolution_time only available for the ~38% of rows that have closed_datetime; dataset is dominated by unplanned vehicle_breakdown events; road_closure target is imbalanced (~8% positive).
- **Strong columns to keep:** event_cause, corridor, police_station, priority, requires_road_closure, start_datetime, latitude/longitude.
