"use client";

import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect } from 'react';

// Fix for default marker icon
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface Agent {
    name: string;
    region: string;
    location: {
        lat: number;
        lon: number;
    };
    available_capacity: number;
    energy_data: {
        carbon_intensity: number;
        price: number;
        renewable_mix: number;
    };
    active_tasks_count: number;
    cost_score?: number; // Added cost_score
}

interface MapProps {
    agents: Agent[];
}

const Map = ({ agents }: MapProps) => {
    const ukCenter: [number, number] = [54.5, -4.0];

    // Updated to use cost_score
    const getColor = (score: number) => {
        // Lower score is better
        if (score < 40) return '#22c55e'; // Green (Good)
        if (score < 70) return '#eab308'; // Yellow (Medium)
        return '#ef4444'; // Red (Bad)
    };

    const getRegionColor = (region: string) => {
        if (region.includes("South")) return '#06b6d4'; // Cyan
        if (region.includes("North")) return '#d946ef'; // Magenta
        return '#9ca3af'; // Gray
    };

    return (
        <div className="h-[400px] w-[647px] max-w-full rounded-xl overflow-hidden border border-gray-800 z-0 relative shadow-2xl shadow-black/50 group">
            <MapContainer
                center={ukCenter}
                zoom={5}
                style={{ height: '100%', width: '100%', background: '#0f1117' }}
                scrollWheelZoom={false}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />
                {agents.map((agent, idx) => (
                    <CircleMarker
                        key={idx}
                        center={[agent.location.lat, agent.location.lon]}
                        pathOptions={{
                            color: getRegionColor(agent.region),
                            fillColor: getColor(agent.cost_score ?? 100), // Default to 100 (Bad) if undefined
                            fillOpacity: 0.7,
                            weight: 3
                        }}
                        radius={8}
                    >
                        <Popup className="bg-gray-900 text-gray-100">
                            <div className="p-2 min-w-[200px]">
                                <h3 className="font-bold text-sm mb-2">{agent.name}</h3>
                                <div className="space-y-1 text-xs">
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Region:</span>
                                        <span style={{ color: getRegionColor(agent.region) }}>{agent.region}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Score:</span>
                                        <span style={{ color: getColor(agent.cost_score ?? 100) }} className="font-bold">
                                            {agent.cost_score?.toFixed(1) ?? 'N/A'}
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Carbon:</span>
                                        <span>
                                            {agent.energy_data.carbon_intensity} gCO2/kWh
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Price:</span>
                                        <span>${agent.energy_data.price?.toFixed(2)}/hr</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Active Jobs:</span>
                                        <span>{agent.active_tasks_count}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Status:</span>
                                        <span className={agent.available_capacity > 0 ? "text-green-400" : "text-red-400"}>
                                            {agent.available_capacity > 0 ? "Available" : "Busy"}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </Popup>
                    </CircleMarker>
                ))}
            </MapContainer>

            {/* Legend Overlay */}
            <div className="absolute bottom-4 right-4 bg-gray-900/90 backdrop-blur p-3 rounded-lg border border-gray-700 z-[1000] text-xs shadow-xl">
                <div className="font-bold mb-2 text-gray-300">Region Indicators</div>
                <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full border-2 border-cyan-500 bg-transparent"></div>
                        <span className="text-gray-400">South UK</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full border-2 border-fuchsia-500 bg-transparent"></div>
                        <span className="text-gray-400">North UK</span>
                    </div>
                </div>
                <div className="my-2 border-t border-gray-700"></div>
                <div className="font-bold mb-2 text-gray-300">Score</div>
                <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-green-500"></div>
                        <span className="text-gray-400">Good (&lt;40)</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                        <span className="text-gray-400">Medium (&lt;70)</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-red-500"></div>
                        <span className="text-gray-400">Poor (&ge;70)</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Map;
