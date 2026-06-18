import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default Leaflet icon assets missing in Webpack/Vite bundlers
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({ iconUrl: markerIcon, shadowUrl: markerShadow, iconAnchor: [12, 41] });
L.Marker.prototype.options.icon = DefaultIcon;

// Helper component to smoothly center the map on new event triggers
function MapRecenter({ center }) {
  const map = useMap();
  if (center) map.setView(center, 14);
  return null;
}

export default function TrafficIQDashboard() {
  // Input parameters matching your dataset features
  const [formData, setFormData] = useState({
    cause: 'Breakdown',
    corridor: 'Outer Ring Road (Silk Board to Marathahalli)',
    vehicle_type: 'Four Wheeler',
    hour: 12,
    day_of_week: 'Monday'
  });

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mapCenter, setMapCenter] = useState([12.9716, 77.5946]); // Bangalore Central initial state

  const handlePredict = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:5000/api/traffic-incident', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (data.status === 'success') {
        setResults(data);
        setMapCenter([data.geo_context.coordinates.lat, data.geo_context.coordinates.lng]);
      }
    } catch (err) {
      console.error('Failed fetching evaluation metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  // Static options array mapped from your processed modeling CSV definitions
  const causes = ['Breakdown', 'Accident', 'Waterlogging', 'Road Work', 'VIP Movement'];
  const corridors = [
    'Outer Ring Road (Silk Board to Marathahalli)', 'Electronic City Flyover', 
    'Tumkur Road', 'Old Madras Road', 'Hosur Road', 'Bellary Road (Hebbal to Airport)'
  ];
  const vehicles = ['Two Wheeler', 'Four Wheeler', 'Heavy Commercial Vehicle', 'Bus'];
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100 font-sans">
      
      {/* LEFT SIDEBAR: Parameter Entry Control Deck */}
      <div className="w-1/4 bg-gray-800 p-6 flex flex-col justify-between border-r border-gray-700 shadow-2xl">
        <div>
          <h1 className="text-2xl font-black tracking-wider text-blue-400 mb-2">TRAFFIC IQ</h1>
          <p className="text-xs text-gray-400 mb-6">Incident Response & Operations Management</p>
          
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">Incident Cause</label>
              <select className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-sm focus:outline-none focus:border-blue-500"
                value={formData.cause} onChange={(e) => setFormData({...formData, cause: e.target.value})}>
                {causes.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">Transit Corridor</label>
              <select className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-sm focus:outline-none focus:border-blue-500"
                value={formData.corridor} onChange={(e) => setFormData({...formData, corridor: e.target.value})}>
                {corridors.map(cor => <option key={cor} value={cor}>{cor}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">Involved Vehicle Type</label>
              <select className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-sm focus:outline-none focus:border-blue-500"
                value={formData.vehicle_type} onChange={(e) => setFormData({...formData, vehicle_type: e.target.value})}>
                {vehicles.map(v => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">Temporal Window (Hour: {formData.hour}:00)</label>
              <input type="range" min="0" max="23" className="w-full accent-blue-500" value={formData.hour}
                onChange={(e) => setFormData({...formData, hour: parseInt(e.target.value)})}/>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">Day of Week</label>
              <select className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-sm focus:outline-none focus:border-blue-500"
                value={formData.day_of_week} onChange={(e) => setFormData({...formData, day_of_week: e.target.value})}>
                {days.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
          </div>
        </div>

        <button onClick={handlePredict} disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-bold py-3 px-4 rounded transition-all tracking-wide text-sm mt-4">
          {loading ? 'RUNNING EVALUATION...' : 'FORECAST TRAFFIC IMPACT'}
        </button>
      </div>

      {/* RIGHT WORKSPACE: Geospatial Canvas & Analytic Monitors */}
      <div className="w-3/4 flex flex-col h-full">
        
        {/* TOP LAYER: Interactive Leaflet Map Deployment View */}
        <div className="h-3/5 w-full bg-gray-950 position-relative z-10 border-b border-gray-700">
          <MapContainer center={mapCenter} zoom={12} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            />
            {results && (
              <Marker position={mapCenter}>
                <Popup>
                  <div className="text-gray-900 font-sans text-xs">
                    <strong className="block text-sm mb-1">{results.geo_context.corridor_name}</strong>
                    <span className="block">Severity: <b>{results.severity}</b></span>
                    <span className="block">Resolution Class: <b>{results.resolution_class}</b></span>
                  </div>
                </Popup>
              </Marker>
            )}
            <MapRecenter center={mapCenter} />
          </MapContainer>
        </div>

        {/* BOTTOM LAYER: Analytics & Recommended Resource Matrices */}
        <div className="h-2/5 p-6 bg-gray-900 grid grid-cols-3 gap-6 overflow-y-auto">
          {results ? (
            <>
              {/* Pipeline KPI Cards */}
              <div className="col-span-2 space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-gray-800 border border-gray-700 p-4 rounded shadow-md">
                    <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Resolution Window</p>
                    <p className="text-xl font-bold text-blue-400 mt-1">{results.resolution_class}</p>
                  </div>
                  <div className="bg-gray-800 border border-gray-700 p-4 rounded shadow-md">
                    <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Impact Score</p>
                    <div className="w-full bg-gray-700 rounded-full h-2.5 mt-3">
                      <div className="bg-orange-500 h-2.5 rounded-full" style={{ width: `${results.impact_score}%` }}></div>
                    </div>
                    <p className="text-right text-xs font-bold text-orange-400 mt-1">{results.impact_score}/100</p>
                  </div>
                  <div className="bg-gray-800 border border-gray-700 p-4 rounded shadow-md">
                    <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Risk Severity</p>
                    <p className={`text-xl font-bold mt-1 ${results.severity === 'High' ? 'text-red-400' : results.severity === 'Medium' ? 'text-yellow-400' : 'text-green-400'}`}>
                      {results.severity}
                    </p>
                  </div>
                </div>

                <div className="bg-gray-800 border border-gray-700 p-4 rounded shadow-md">
                  <p className="text-xs font-medium uppercase tracking-wider text-gray-400 mb-2">Operational Response Summary</p>
                  <p className="text-sm text-gray-300 leading-relaxed">{results.summary}</p>
                </div>
              </div>

              {/* Resource Rule Engine Output Display */}
              <div className="bg-gray-800 border border-gray-700 p-4 rounded shadow-md flex flex-col justify-between">
                <p className="text-xs font-medium uppercase tracking-wider text-gray-400 mb-2">Resource Dispatch Deployment</p>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="bg-gray-700/50 p-2 rounded flex justify-between items-center">
                    <span className="text-gray-400">On-Ground Officers</span>
                    <span className="font-mono font-bold text-blue-400 bg-gray-900 px-2 py-0.5 rounded text-xs">{results.resources.officers || 0}</span>
                  </div>
                  <div className="bg-gray-700/50 p-2 rounded flex justify-between items-center">
                    <span className="text-gray-400">Traffic Marshals</span>
                    <span className="font-mono font-bold text-blue-400 bg-gray-900 px-2 py-0.5 rounded text-xs">{results.resources.marshals || 0}</span>
                  </div>
                  <div className="bg-gray-700/50 p-2 rounded flex justify-between items-center">
                    <span className="text-gray-400">Barricades</span>
                    <span className="font-mono font-bold text-blue-400 bg-gray-900 px-2 py-0.5 rounded text-xs">{results.resources.barricades || 0}</span>
                  </div>
                  <div className="bg-gray-700/50 p-2 rounded flex justify-between items-center">
                    <span className="text-gray-400">Heavy Tow Trucks</span>
                    <span className="font-mono font-bold text-blue-400 bg-gray-900 px-2 py-0.5 rounded text-xs">{results.resources.tow_trucks || 0}</span>
                  </div>
                </div>
                <div className="text-[10px] text-gray-500 text-center mt-2 italic border-t border-gray-700/50 pt-2">
                  Generated via rule-based dispatch matrix engine
                </div>
              </div>
            </>
          ) : (
            <div className="col-span-3 flex items-center justify-center text-gray-500 italic text-sm">
              Await incident evaluation to populate telemetry metrics...
            </div>
          )}
        </div>

      </div>
    </div>
  );
}