# 🚦 TrafficIQ — AI-Powered Traffic Intelligence Platform

TrafficIQ is a full-stack, AI-driven traffic intelligence platform designed to forecast traffic incident resolution times and convert those predictions into actionable operational insights. Built using real-world Bengaluru traffic incident data (~8,173 records), the platform helps city operators proactively manage congestion through predictive analytics, geospatial visualization, and automated resource planning.

---

## 📌 Overview

Traditional traffic dashboards often display incidents after they occur. TrafficIQ takes a predictive approach by estimating how long an incident will impact traffic and automatically recommending response strategies.

The system combines:

* Machine Learning-based resolution time forecasting
* Rule-based severity and impact assessment
* Interactive geospatial visualization
* Tactical resource deployment recommendations
* Feedback mechanisms for continuous improvement

---

## 🏗️ System Architecture

```text
[ React Frontend / Leaflet Map ]
         | (JSON over HTTP/POST)
[ FastAPI Orchestrator (main.py) ]
         |
[ Feature Assembly & Payload Mapping ]
         |
[ LightGBM Resolution-Time Model ]
         |
[ Predicted Class:
   Quick / Moderate / Prolonged ]
         |
[ Rules Engine Layer ]
    ├── Impact Score
    ├── Severity Level
    └── Resource Allocation
         |
[ JSON Response Payload ]
         |
[ React Dashboard Update ]
```

### Architecture Highlights

* Decoupled frontend and backend
* RESTful communication via FastAPI
* Single production-grade ML model
* Explainable rule-engine layer
* Real-time UI updates using React state management

---

## ✨ Features

### 🗺️ Real-Time Traffic Visualization

Interactive city-wide traffic dashboard built using React-Leaflet and Leaflet.js.

### 🚨 Dynamic Severity Mapping

Traffic incidents are color-coded based on predicted impact:

| Severity | Color     |
| -------- | --------- |
| Low      | 🟢 Green  |
| Medium   | 🟡 Yellow |
| High     | 🔴 Red    |

Map markers dynamically scale according to forecasted disruption levels.

### 🚓 Tactical Resource Deployment

Automatically recommends:

* Traffic officers
* Tow trucks
* Marshals
* Barricade deployment
* Alternate route suggestions

based on predicted incident severity.

### 🔄 Continuous Learning Hook

Operators can validate model predictions and provide feedback for future active-learning workflows.

### 🎤 Presentation Mode

Special backend interception layer enables deterministic demo scenarios while preserving the original ML model behavior.

---

## 🛠️ Tech Stack

### Frontend

* React.js (Vite)
* Tailwind CSS
* React-Leaflet
* Leaflet.js

### Backend

* FastAPI
* Uvicorn
* Python 3

### Machine Learning

* LightGBM
* Scikit-Learn
* Pandas

### Data Processing

* Feature Engineering Pipeline
* Custom Rules Engine
* Model Serialization (.pkl)

---

## 🤖 Machine Learning Pipeline

### Prediction Task

TrafficIQ performs a single ML task:

**Resolution Time Classification**

Target Variable:

```text
res_time_band

Classes:
- Quick
- Moderate
- Prolonged
```

### Model Selection

Multiple gradient boosting algorithms were evaluated:

* XGBoost
* CatBoost
* LightGBM

LightGBM was selected for deployment due to the best overall balance between weighted F1-score and recall.

### Performance Metrics

```text
Accuracy    = 0.5849
Weighted F1 = 0.5920
CV F1       = 0.5603 ± 0.0152
```

---

## 📖 Model Interpretability

### Why Severity is Rule-Based

During experimentation, a separate severity classification model achieved nearly 99.8% F1 score.

Further investigation revealed that the model was primarily memorizing location identifiers rather than learning meaningful traffic behavior patterns.

To preserve:

* Explainability
* Trustworthiness
* Operational transparency

the severity model was intentionally removed.

Severity is now derived from the resolution-time prediction using a transparent rules engine.

```text
Resolution Forecast
        ↓
Impact Score
        ↓
Severity Level
        ↓
Resource Recommendations
```

This design provides better interpretability and avoids misleading performance metrics.

---

##  Running Locally

### 1️⃣ Start the Backend

From the project root:

```bash
pip install -r requirements.txt

uvicorn main:app --reload
```

Backend runs on:

```text
http://localhost:8000
```

---

### 2️⃣ Start the Frontend

Open a second terminal:

```bash
cd client

npm install

npm run dev
```

Frontend runs on:

```text
http://localhost:5173
```

---

## 🔬 Reproducing the ML Pipeline

To retrain the model from scratch:

```bash
python src/eda.py

python src/feature_engineering.py

python src/define_targets.py

python src/train_models.py
```

Pipeline Flow:

```text
Raw Dataset
    ↓
EDA
    ↓
Feature Engineering
    ↓
Target Definition
    ↓
Model Training
    ↓
Serialized Model Artifacts
```

---

## 📂 Project Structure

```text
TrafficIQ/
│
├── client/                  # React frontend
│
├── src/
│   ├── eda.py
│   ├── feature_engineering.py
│   ├── define_targets.py
│   ├── train_models.py
│   └── rules_engine.py
│
├── models/                  # Serialized ML artifacts
│
├── data/
│   ├── raw/
│   └── processed/
│
├── main.py                  # FastAPI backend
├── config.py                # Configurations & thresholds
├── requirements.txt
│
└── README.md
```

---

## 🎯 Future Enhancements

* Live traffic API integration
* SHAP-based model explainability dashboard
* Real-time streaming predictions
* Automated model retraining pipeline
* Docker & Kubernetes deployment
* MLOps monitoring and drift detection

---

## 📜 License

This project is intended for educational, research, and portfolio purposes.

---


