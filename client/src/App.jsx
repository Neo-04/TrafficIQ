import React, { useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap, ZoomControl, Circle } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

const DefaultIcon = L.icon({
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

// --- FRONTEND DATA LOOKUPS (Expanded Bangalore Dataset) ---
const corridorCoordinates = {
  "Outer Ring Road (Silk Board to Marathahalli)": [12.9237, 77.6729],
  "Electronic City Flyover": [12.8497, 77.6644],
  "Tumkur Road": [13.0358, 77.5348],
  "Old Madras Road": [12.9791, 77.6528],
  "Hosur Road": [12.9365, 77.6186],
  "Bellary Road (Hebbal to Airport)": [13.0354, 77.5978],
  "Mysore Road (Kengeri to Nayandahalli)": [12.9228, 77.4996],
  "Bannerghatta Road (Dairy Circle to Meenakshi Mall)": [12.9048, 77.5971],
  "Inner Ring Road (Domlur to Koramangala)": [12.9554, 77.6385],
  "Sarjapur Road (Koramangala to Carmelaram)": [12.9150, 77.6508],
  "Whitefield Main Road (Marathahalli to Hope Farm)": [12.9822, 77.7360],
  "Old Airport Road (Domlur to Marathahalli)": [12.9575, 77.6627],
  "Kanakapura Road (Banashankari to NICE Road)": [12.8872, 77.5658],
  "Hennur Main Road (Lingarajapuram to Hennur Cross)": [13.0238, 77.6335],
  "West of Chord Road (Rajajinagar to Yeshwanthpur)": [13.0035, 77.5492]
};

const alternateRoutes = {
  "Outer Ring Road (Silk Board to Marathahalli)": ["Inner Ring Road via Koramangala", "Sarjapur Road to HSR Layout"],
  "Electronic City Flyover": ["NICE Road", "Underneath Toll Road (Hosur Rd)"],
  "Tumkur Road": ["Magadi Road", "Outer Ring Road via Peenya"],
  "Old Madras Road": ["Swami Vivekananda Road", "Indiranagar 100ft Road"],
  "Hosur Road": ["Bannerghatta Road", "Koramangala 80ft Road"],
  "Bellary Road (Hebbal to Airport)": ["Hennur Main Road", "Thanisandra Main Road"],
  "Mysore Road (Kengeri to Nayandahalli)": ["NICE Road", "Chord Road via Vijayanagar"],
  "Bannerghatta Road (Dairy Circle to Meenakshi Mall)": ["Hosur Road via BTM Layout", "JP Nagar Ring Road"],
  "Inner Ring Road (Domlur to Koramangala)": ["100ft Road Indiranagar", "Trinity Circle to MG Road"],
  "Sarjapur Road (Koramangala to Carmelaram)": ["Outer Ring Road via Bellandur", "Harlur Road"],
  "Whitefield Main Road (Marathahalli to Hope Farm)": ["ITPL Main Road", "Hoodi Main Road", "Varthur Road"],
  "Old Airport Road (Domlur to Marathahalli)": ["Suranjandas Road", "Indiranagar 100ft Road"],
  "Kanakapura Road (Banashankari to NICE Road)": ["Banashankari Outer Ring Road", "Kumaraswamy Layout Main Road"],
  "Hennur Main Road (Lingarajapuram to Hennur Cross)": ["Thanisandra Main Road", "Kalyan Nagar Outer Ring Road"],
  "West of Chord Road (Rajajinagar to Yeshwanthpur)": ["Magadi Road", "Malleshwaram 8th Main"]
};

// Map component for smooth panning
function MapRecenter({ center }) {
  const map = useMap();
  if (center) map.flyTo(center, 14, { duration: 1.5 }); 
  return null;
}

export default function App() {
  const [formData, setFormData] = useState({
    cause: "Breakdown",
    corridor: "Outer Ring Road (Silk Board to Marathahalli)",
    vehicle_type: "Four Wheeler",
    hour: 12,
    day_of_week: "Monday",
  });

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mapCenter, setMapCenter] = useState(corridorCoordinates["Outer Ring Road (Silk Board to Marathahalli)"]);
  
  // MLOps Notification State
  const [showToast, setShowToast] = useState(false);

  // Instant map jump on dropdown change
  const handleCorridorChange = (e) => {
    const newCorridor = e.target.value;
    setFormData({ ...formData, corridor: newCorridor });
    if (corridorCoordinates[newCorridor]) {
      setMapCenter(corridorCoordinates[newCorridor]);
      setResults(null); 
    }
  };

  const handlePredict = async () => {
    setLoading(true);
    setError(null); 
    try {
      // 1. Data mapping so ML pipeline understands the UI strings
      const causeMap = {
        "Breakdown": "vehicle_breakdown",
        "Accident": "accident", 
        "Waterlogging": "water_logging",
        "Road Work": "construction",
        "VIP Movement": "vip_movement"
      };

      const vehicleMap = {
        "Two Wheeler": "unknown",
        "Four Wheeler": "private_car",
        "Heavy Commercial Vehicle": "heavy_vehicle",
        "Bus": "bmtc_bus"
      };

      const corridorMap = {
        "Outer Ring Road (Silk Board to Marathahalli)": "ORR East 1",
        "Bellary Road (Hebbal to Airport)": "Bellary Road 1",
        "Electronic City Flyover": "Hosur Road", 
        "Tumkur Road": "Tumkur Road",
        "Old Madras Road": "Old Madras Road",
        "Hosur Road": "Hosur Road",
        "Mysore Road (Kengeri to Nayandahalli)": "Mysore Road",
        "Bannerghatta Road (Dairy Circle to Meenakshi Mall)": "Bannerghatta Road",
        "Inner Ring Road (Domlur to Koramangala)": "Inner Ring Road",
        "Sarjapur Road (Koramangala to Carmelaram)": "Sarjapur Road",
        "Whitefield Main Road (Marathahalli to Hope Farm)": "Whitefield", 
        "Old Airport Road (Domlur to Marathahalli)": "Old Airport Road",
        "Kanakapura Road (Banashankari to NICE Road)": "Kanakapura Road",
        "Hennur Main Road (Lingarajapuram to Hennur Cross)": "Hennur Main Road",
        "West of Chord Road (Rajajinagar to Yeshwanthpur)": "West of Chord Road"
      };

      const apiPayload = {
        ...formData,
        cause: causeMap[formData.cause] || formData.cause,
        vehicle_type: vehicleMap[formData.vehicle_type] || formData.vehicle_type,
        corridor: corridorMap[formData.corridor] || formData.corridor
      };

      // 2. Fetch with mapped payload (Updated port to 8000 to match main.py)
      const res = await fetch("http://localhost:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(apiPayload),
      });

      const responseData = await res.json();

      if (!res.ok) {
        console.error("Backend Error Details:", responseData);
        throw new Error(responseData.error?.detail || responseData.error || "Backend connection failed.");
      }

      if (responseData.status === "success") {
        setResults(responseData);
        if (responseData.geo_context?.coordinates) {
            setMapCenter([
            responseData.geo_context.coordinates.lat,
            responseData.geo_context.coordinates.lng,
            ]);
        }
      } else {
        setError(responseData.error || "Prediction failed.");
      }
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Simulates sending validated data to an active learning DB
  const handleFeedback = () => {
    setShowToast(true);
    setTimeout(() => {
      setShowToast(false);
    }, 3500);
  };

  const getSeverityColor = (severity) => {
    if (!severity) return "#3b82f6"; 
    const s = severity.toLowerCase();
    if (s.includes("high") || s.includes("critical")) return "#ef4444"; 
    if (s.includes("medium") || s.includes("moderate")) return "#eab308"; 
    if (s.includes("low") || s.includes("minor") || s.includes("quick")) return "#22c55e"; 
    return "#3b82f6"; 
  };

  const causes = ["Breakdown", "Accident", "Waterlogging", "Road Work", "VIP Movement"];
  const corridors = Object.keys(corridorCoordinates);
  const vehicles = ["Two Wheeler", "Four Wheeler", "Heavy Commercial Vehicle", "Bus"];
  const days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];

  const inputStyle = "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm focus:ring-2 focus:ring-blue-500 outline-none";

  return (
    <div className="h-screen w-screen flex bg-gradient-to-br from-sky-50 via-white to-blue-100 overflow-hidden relative">
      <aside className="w-80 bg-white/80 backdrop-blur-xl border-r border-blue-100 shadow-xl p-6 flex flex-col justify-between shrink-0 z-10">
        <div>
          <h1 className="text-3xl font-black bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
            TRAFFIC IQ
          </h1>
          <p className="text-slate-500 text-sm mt-2 mb-6">AI Powered Traffic Intelligence Platform</p>

          <div className="space-y-4">
            <select className={inputStyle} value={formData.cause} onChange={(e)=>setFormData({...formData,cause:e.target.value})}>
              {causes.map(c=><option key={c}>{c}</option>)}
            </select>
            <select className={inputStyle} value={formData.corridor} onChange={handleCorridorChange}>
              {corridors.map(c=><option key={c}>{c}</option>)}
            </select>
            <select className={inputStyle} value={formData.vehicle_type} onChange={(e)=>setFormData({...formData,vehicle_type:e.target.value})}>
              {vehicles.map(v=><option key={v}>{v}</option>)}
            </select>
            <div className="bg-white rounded-xl p-4 border border-slate-200">
              <p className="text-sm font-medium text-slate-600 mb-2">Hour: {formData.hour}:00</p>
              <input type="range" min="0" max="23" className="w-full accent-blue-600" value={formData.hour} onChange={(e)=>setFormData({...formData,hour:Number(e.target.value)})} />
            </div>
            <select className={inputStyle} value={formData.day_of_week} onChange={(e)=>setFormData({...formData,day_of_week:e.target.value})}>
              {days.map(d=><option key={d}>{d}</option>)}
            </select>
          </div>
        </div>

        <div className="space-y-2 flex flex-col">
          {error && <p className="text-xs text-red-500 text-center font-medium bg-red-50 py-2 rounded-lg">{error}</p>}
          <button
            onClick={handlePredict}
            disabled={loading}
            className="w-full rounded-xl py-4 text-white font-semibold bg-gradient-to-r from-blue-600 to-cyan-500 hover:scale-[1.02] transition-all shadow-lg disabled:opacity-50"
          >
            {loading ? "ANALYZING..." : "FORECAST TRAFFIC IMPACT"}
          </button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col overflow-y-auto">
        
        {/* --- TOP 4 STATUS CARDS --- */}
        <div className="grid grid-cols-4 gap-4 p-5 bg-white/60 shrink-0">
          <div className="bg-white rounded-2xl shadow-md border border-blue-100 p-4">
            <p className="text-slate-500 text-sm">Status</p>
            <h2 className="text-2xl font-bold text-blue-600 mt-1">{results ? "Live Response" : "--"}</h2>
          </div>
          
          {/* FIXED: Top Impact Score is back to just text */}
          <div className="bg-white rounded-2xl shadow-md border border-blue-100 p-4">
            <p className="text-slate-500 text-sm">Impact Score</p>
            <h2 className="text-2xl font-bold text-blue-600 mt-1">
              {results?.impact_score !== undefined && results?.impact_score !== null ? `${results.impact_score}%` : "--"}
            </h2>
          </div>
          
          <div className="bg-white rounded-2xl shadow-md border border-blue-100 p-4">
            <p className="text-slate-500 text-sm">Resolution Window</p>
            <h2 className="text-2xl font-bold text-blue-600 mt-1">{results?.resolution_class || "--"}</h2>
          </div>
          <div className="bg-white rounded-2xl shadow-md border border-blue-100 p-4">
            <p className="text-slate-500 text-sm">Risk Level</p>
            <h2 className="text-2xl font-bold mt-1" style={{ color: getSeverityColor(results?.severity) }}>
              {results?.severity || "--"}
            </h2>
          </div>
        </div>

        {/* --- MAP SECTION --- */}
        <div className="h-[40%] relative shrink-0">
          <div className="absolute top-4 right-4 z-[1000] bg-white/90 rounded-2xl shadow-xl px-5 py-3 border border-blue-50">
            <h3 className="font-bold">Live Traffic Intelligence</h3>
            <p className="text-xs text-slate-500">Real-time monitoring dashboard</p>
          </div>

          <MapContainer center={mapCenter} zoom={13} zoomControl={false} style={{height:"100%",width:"100%"}}>
            <ZoomControl position="bottomright" />
            <TileLayer url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png" />
            <Marker position={mapCenter}>
              <Popup><b>{formData.corridor}</b></Popup>
            </Marker>
            {results && (
              <Circle
                center={mapCenter}
                radius={(results.impact_score || 50) * 15}
                pathOptions={{
                  color: getSeverityColor(results.severity),
                  fillColor: getSeverityColor(results.severity),
                  fillOpacity: 0.3,
                  weight: 2
                }}
              />
            )}
            <MapRecenter center={mapCenter} />
          </MapContainer>
        </div>

        {/* --- BOTTOM DASHBOARD SECTION --- */}
        <div className="flex-1 p-6 bg-slate-50 shrink-0">
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2 space-y-5">
              
              {/* --- MIDDLE 3 CARDS --- */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white rounded-2xl shadow-lg p-5">
                  <p className="text-slate-500 text-sm font-semibold">Resolution Window</p>
                  <h2 className="text-2xl font-bold text-blue-600 mt-2">{results?.resolution_class || "--"}</h2>
                </div>
                
                {/* FIXED: Middle Impact Score now has the bar + the w-12 number */}
                <div className="bg-white rounded-2xl shadow-lg p-5 flex flex-col justify-center">
                  <p className="text-slate-500 text-sm font-semibold mb-3">Impact Score</p>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-slate-200 rounded-full h-3">
                      <div
                        className="h-3 rounded-full transition-all duration-1000"
                        style={{ 
                          width: `${results?.impact_score || 0}%`,
                          backgroundColor: getSeverityColor(results?.severity)
                        }}
                      />
                    </div>
                    <span className="font-bold text-slate-700 text-lg w-12 text-right">
                      {results?.impact_score !== undefined && results?.impact_score !== null ? `${results.impact_score}%` : "0%"}
                    </span>
                  </div>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-5">
                  <p className="text-slate-500 text-sm font-semibold">Traffic Severity</p>
                  <h2 className="text-2xl font-bold mt-2" style={{ color: getSeverityColor(results?.severity) }}>
                    {results?.severity || "--"}
                  </h2>
                </div>
              </div>

              {/* --- SUMMARY & DIVERSIONS --- */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white rounded-2xl shadow-lg p-5 border-l-4 border-blue-500 flex flex-col justify-between">
                  <div>
                    <h3 className="font-semibold mb-3 text-slate-800">Operational Summary</h3>
                    <p className="text-slate-600 text-sm leading-relaxed">
                      {results?.summary || "Run a prediction to view tactical recommendations and operational summary."}
                    </p>
                  </div>
                </div>
                
                <div className="bg-white rounded-2xl shadow-lg p-5 border-l-4 border-green-500 flex flex-col justify-between">
                  <div>
                    <h3 className="font-semibold mb-3 text-slate-800">Suggested Diversions</h3>
                    {results ? (
                      <ul className="space-y-2">
                        {alternateRoutes[formData.corridor]?.map((route, i) => (
                          <li key={i} className="flex items-center text-sm text-slate-600 bg-green-50 px-3 py-2 rounded-lg border border-green-100">
                            <span className="w-2 h-2 rounded-full bg-green-500 mr-2"></span>
                            {route}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-slate-400 text-sm italic">Routes will generate post-analysis.</p>
                    )}
                  </div>
                  
                  {/* Validation Feedback Button */}
                  {results && (
                    <button 
                      onClick={handleFeedback}
                      className="mt-6 w-full py-2 bg-slate-50 hover:bg-slate-100 text-slate-600 text-xs font-bold rounded-lg border border-slate-300 transition-colors flex items-center justify-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                      VALIDATE & LOG FOR RETRAINING
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* --- RESOURCES CARD --- */}
            <div className="bg-white rounded-2xl shadow-lg p-5 flex flex-col">
              <h3 className="font-semibold mb-4 text-slate-800">Resource Deployment</h3>
              <div className="flex-1 overflow-y-auto pr-2">
                {results?.resources && Object.keys(results.resources).length > 0 ? (
                  Object.entries(results.resources).map(([key, value]) => (
                    <div key={key} className="flex justify-between items-center bg-slate-50 border border-slate-100 rounded-xl p-3 mb-3">
                      <span className="capitalize text-sm font-medium text-slate-700">{key.replace(/_/g," ")}</span>
                      <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-xs font-bold shadow-sm">
                        {value}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-400 text-sm text-center">No resource data generated yet.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* --- MLOps Toast Notification --- */}
      {showToast && (
        <div className="fixed bottom-6 right-6 bg-slate-900 text-white px-6 py-4 rounded-xl shadow-2xl z-[9999] flex items-center space-x-4 border border-slate-700 animate-bounce">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.8)]"></div>
          <div>
            <h4 className="font-bold text-sm text-slate-100">Pipeline Updated</h4>
            <p className="text-xs text-slate-400">Instance logged to Active Learning Database.</p>
          </div>
        </div>
      )}
    </div>
  );
}