const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');

const app = express();

app.use(cors({
  origin: 'http://localhost:5173',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
  optionsSuccessStatus: 200
}));

app.use(express.json());

const PYTHON_API_URL = 'http://127.0.0.1:8000/predict';
// Path tracking back out to your global dataset file location
const CSV_DATA_PATH = path.join(__dirname, '../data/processed/incidents_modeling.csv');

// Global lookup arrays populated dynamically at runtime
let dynamicOptions = {
  causes: [],
  corridors: [],
  vehicles: ['two_wheeler', 'four_wheeler', 'heavy_commercial_vehicle', 'bus', 'unknown'] // Solid fallback list
};

// Map names to coordinates. Missing keys default gracefully to Bengaluru Center.
const corridorCoordinates = {
  "Outer Ring Road (Silk Board to Marathahalli)": { lat: 12.9237, lng: 77.6729 },
  "Electronic City Flyover": { lat: 12.8497, lng: 77.6644 },
  "Tumkur Road": { lat: 13.0358, lng: 77.5348 },
  "Old Madras Road": { lat: 12.9791, lng: 77.6528 },
  "Hosur Road": { lat: 12.9365, lng: 77.6186 },
  "Bellary Road (Hebbal to Airport)": { lat: 13.0354, lng: 77.5978 },
  "Mysore Road": { lat: 12.9538, lng: 77.5392 },
  "Bannerghatta Road": { lat: 12.8967, lng: 77.5992 }
};

// Read CSV data instantly to mimic Streamlit's lookups caching
function loadDynamicOptions() {
  const uniqueCauses = new Set();
  const uniqueCorridors = new Set();

  if (!fs.existsSync(CSV_DATA_PATH)) {
    console.warn(`⚠️ Dataset CSV not found at ${CSV_DATA_PATH}. Using standard fallback arrays.`);
    dynamicOptions.causes = ['vehicle_breakdown', 'accident', 'waterlogging', 'road_work', 'vip_movement'];
    dynamicOptions.corridors = Object.keys(corridorCoordinates);
    return;
  }

  fs.createReadStream(CSV_DATA_PATH)
    .pipe(csv())
    .on('data', (row) => {
      if (row.event_cause) uniqueCauses.add(row.event_cause.trim());
      if (row.corridor) uniqueCorridors.add(row.corridor.trim());
    })
    .on('end', () => {
      dynamicOptions.causes = Array.from(uniqueCauses).sort();
      dynamicOptions.corridors = Array.from(uniqueCorridors).sort();
      console.log(`✅ Loaded Lookups from CSV: ${dynamicOptions.causes.length} causes, ${dynamicOptions.corridors.length} corridors.`);
    });
}
loadDynamicOptions();

// NEW ENDPOINT: Serves full options checklist arrays directly to React UI
app.get('/api/options', (req, res) => {
  res.json(dynamicOptions);
});

app.post('/api/traffic-incident', async (req, res) => {
  try {
    const { cause, corridor, vehicle_type, hour, day_of_week } = req.body;

    const response = await axios.post(PYTHON_API_URL, {
      cause, corridor, vehicle_type, hour, day_of_week
    });

    const prediction = response.data;
    const defaultCoords = { lat: 12.9716, lng: 77.5946 };
    const geoData = corridorCoordinates[corridor] || defaultCoords;

    return res.json({
      ...prediction,
      geo_context: {
        corridor_name: corridor,
        coordinates: geoData
      }
    });

  } catch (error) {
    console.error('Orchestration Error:', error.message);
    const statusCode = error.response ? error.response.status : 500;
    const errorMsg = error.response ? error.response.data : 'Internal Server Orchestration Error';
    return res.status(statusCode).json({ error: errorMsg });
  }
});

const PORT = 5001;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Node.js routing engine active on port ${PORT}`);
});

setInterval(() => {}, 1000 * 60 * 60);