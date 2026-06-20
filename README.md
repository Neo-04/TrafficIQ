# 🚦 TrafficIQ — AI-Powered Traffic Intelligence Platform

TrafficIQ is a full-stack, AI-driven traffic intelligence platform that forecasts traffic incident resolution times and converts those predictions into actionable operational insights. Built on real-world Bengaluru traffic incident data (~8,173 records), the platform helps city operators proactively manage congestion through predictive analytics, geospatial visualization, and automated resource planning.

---

## 🔗 Live Deployment

| Layer | Service | URL |
| ----- | ------- | --- |
| Frontend | React (Vercel) | https://traffic-iq-pi.vercel.app |
| Orchestrator | Node/Express (Render) | https://trafficiq-node.onrender.com |
| ML Engine | FastAPI (Render) | https://trafficiq-fastapi.onrender.com |

> **Note:** The backend services run on Render's free tier, which sleeps after inactivity. The first request after an idle period may take 30–60 seconds while the services wake up — subsequent requests are fast.

**Try it:** open the [live app](https://traffic-iq-pi.vercel.app), choose an incident scenario, and click **Forecast Traffic Impact**.

---

## 📌 Overview

Traditional traffic dashboards display incidents only after they occur. TrafficIQ takes a predictive approach: it estimates how long an incident will impact traffic and automatically recommends a response strategy.

The system combines:

* Machine Learning–based resolution time forecasting
* Rule-based severity and impact assessment
* Interactive geospatial visualization
* Tactical resource deployment recommendations
* A feedback hook for continuous improvement

---

## 🏗️ System Architecture

TrafficIQ is deployed as **three independent services** that communicate over HTTP:

```text
[ React Frontend (Vercel) ]
        | JSON over HTTPS / POST
        v
[ Node/Express Orchestrator (Render) ]
        | forwards request, adds geo context
        v
[ FastAPI ML Engine (Render) ]
        |
[ Feature Assembly & Payload Mapping ]
        |
[ LightGBM Resolution-Time Model ]
        |
[ Predicted Class: Quick / Moderate / Prolonged ]
        |
[ Rules Engine Layer ]
    ├── Impact Score
    ├── Severity Level
    └── Resource Allocation
        |
[ JSON Response Payload ]
        |
        v
[ Node Orchestrator -> React Dashboard Update ]
```

### Architecture Highlights

* **Three decoupled, independently deployable services** (frontend, orchestrator, ML engine)
* Node/Express orchestration layer that forwards prediction requests and enriches them with geospatial context
* Single production-grade ML model (LightGBM)
* Explainable rule-engine layer for severity, impact, and resources
* Real-time UI updates using React state management
* Environment-variable–driven configuration and CORS for safe cross-service communication

---

## ✨ Features

### 🗺️ Real-Time Traffic Visualization

Interactive city-wide traffic dashboard built with React-Leaflet and Leaflet.js.

### 🚨 Dynamic Severity Mapping

Incidents are color-coded based on predicted impact:

| Severity | Color     |
| -------- | --------- |
| Low      | 🟢 Green  |
| Medium   | 🟡 Yellow |
| High     | 🔴 Red    |

Map markers scale dynamically with the forecasted disruption level.

### 🚓 Tactical Resource Deployment

Automatically recommends a resource matrix per incident:

* Traffic officers
* Tow trucks
* Marshals
* Barricade deployment
* (Scenario-specific) water pumps and alternate-route guidance

scaled to predicted incident severity.

### 🔄 Continuous Learning Hook

Operators can validate predictions and log outcomes, laying the groundwork for future active-learning / retraining workflows.

### 🎤 Presentation Mode

A backend interception layer enables deterministic demo scenarios while preserving the underlying ML model's natural behavior.

---

## 🛠️ Tech Stack

### Frontend

* React.js (Vite)
* Tailwind CSS
* React-Leaflet
* Leaflet.js
* Deployed on **Vercel**

### Orchestration Layer

* Node.js
* Express
* Deployed on **Render**

### ML Backend

* FastAPI
* Uvicorn
* Python 3
* Deployed on **Render**

### Machine Learning

* LightGBM
* Scikit-Learn
* Pandas / NumPy

### Data Processing

* Feature Engineering Pipeline
* Custom Rules Engine
* Model Serialization (.pkl)

---

## 🤖 Machine Learning Pipeline

### Prediction Task

TrafficIQ performs a single ML task:

**Resolution Time Classification**

```text
Target: resolution_time_class

Classes:
- Quick      (≤ 60 min)
- Moderate   (1–4 hours)
- Prolonged  (> 4 hours)
```

### Model Selection

Three gradient boosting algorithms were evaluated — **XGBoost**, **CatBoost**, and **LightGBM**. LightGBM was selected for deployment based on the best overall balance between weighted F1-score and recall (tie-broken on recall).

### Performance Metrics

```text
Accuracy    = 0.5849
Weighted F1 = 0.5920
CV F1       = 0.5603 ± 0.0152
```

These results reflect genuine signal well above the naive-guess baseline.

---

## 📖 Model Interpretability

### Why Severity is Rule-Based

During experimentation, a separate severity classification model achieved a suspiciously high ~99.8% F1 score.

Investigation revealed the model was **memorizing location identifiers** (priority is administratively assigned by corridor) rather than learning meaningful traffic behavior. Once location identity was removed, its performance collapsed below the always-"High" baseline — confirming zero genuine signal.

To preserve **explainability, trustworthiness, and operational transparency**, the severity model was intentionally removed. Severity is now *derived* from the resolution-time prediction through a transparent rules engine:

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

## ▶️ Running Locally

The app runs as three local processes. Start them in this order.

### 1️⃣ FastAPI ML Engine

From the project root:

```bash
pip install -r requirements-api.txt
uvicorn src.predict_api:app --reload --port 8000
```

Runs on `http://localhost:8000` (interactive docs at `/docs`).

### 2️⃣ Node Orchestrator

```bash
cd server
npm install
npm start
```

Runs on `http://localhost:5001`.

### 3️⃣ React Frontend

```bash
cd client
npm install
npm run dev
```

Runs on `http://localhost:5173`.

> Create `client/.env.local` with `VITE_API_URL=http://localhost:5001` so the frontend points at your local Node service.

---

## 🔬 Reproducing the ML Pipeline

To retrain the model from scratch (uses the full `requirements.txt`):

```bash
pip install -r requirements.txt

python src/eda.py
python src/feature_engineering.py
python src/define_targets.py
python src/train_models.py
```

Pipeline flow:

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
Serialized Model Artifacts (.pkl)
```

---

## 📂 Project Structure

```text
TrafficIQ/
│
├── client/                      # React frontend (Vercel)
│   ├── src/
│   │   └── App.jsx
│   └── ...
│
├── server/                      # Node/Express orchestrator (Render)
│   ├── server.js
│   └── package.json
│
├── src/                         # Python ML engine (Render)
│   ├── predict_api.py           # FastAPI app (entry point)
│   ├── predict_pipeline.py      # End-to-end inference pipeline
│   ├── rules_engine.py          # Impact / severity / resource rules
│   ├── config.py                # Paths, thresholds, rule maps
│   ├── eda.py
│   ├── feature_engineering.py
│   ├── define_targets.py
│   └── train_models.py
│
├── models/                      # Serialized ML artifacts (.pkl)
├── data/
│   ├── raw/
│   └── processed/
│
├── requirements.txt             # Full deps (training + Streamlit)
├── requirements-api.txt         # Slim deps (production API only)
└── README.md
```

---

## ☁️ Deployment Notes

* **Frontend (Vercel):** root directory `client`, framework Vite, build `npm run build`, output `dist`. Env var `VITE_API_URL` points to the Node service.
* **Orchestrator (Render):** root directory `server`, build `npm install`, start `npm start`. Env vars: `PYTHON_API_URL` (FastAPI `/predict` endpoint) and `FRONTEND_URL` (Vercel origin, used for CORS).
* **ML Engine (Render):** root directory blank, build `pip install -r requirements-api.txt`, start `uvicorn src.predict_api:app --host 0.0.0.0 --port $PORT`. A slim requirements file keeps the build lightweight by excluding training-only dependencies.

---

## 🎯 Future Enhancements

* Live traffic API integration
* SHAP-based model explainability dashboard
* Real-time streaming predictions
* Persistent storage + automated retraining pipeline
* Docker & Kubernetes deployment
* MLOps monitoring and drift detection

---

## 📜 License

This project is intended for educational, research, and portfolio purposes.