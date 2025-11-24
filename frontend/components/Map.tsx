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
}

interface MapProps {
    agents: Agent[];
}

const Map = ({ agents }: MapProps) => {
    const ukCenter: [number, number] = [54.5, -4.0];

    const getColor = (carbon: number) => {
        if (carbon < 50) return '#22c55e'; // Green
        if (carbon < 150) return '#eab308'; // Yellow
        return '#ef4444'; // Red
    };

    return (
        <div className="h-[400px] w-[647px] max-w-full rounded-xl overflow-hidden border border-gray-800 z-0 relative shadow-2xl shadow-black/50">
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
                            color: getColor(agent.energy_data.carbon_intensity),
                            fillColor: getColor(agent.energy_data.carbon_intensity),
                            fillOpacity: 0.7,
                            weight: 2
                        }}
                        radius={8}
                    >
                        <Popup className="bg-gray-900 text-gray-100">
                            <div className="p-2 min-w-[200px]">
                                <h3 className="font-bold text-sm mb-2">{agent.name}</h3>
                                <div className="space-y-1 text-xs">
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Region:</span>
                                        <span>{agent.region}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Carbon:</span>
                                        <span style={{ color: getColor(agent.energy_data.carbon_intensity) }}>
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
        </div>
    );
};

export default Map;
