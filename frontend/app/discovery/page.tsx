'use client';

import { useEffect, useState } from 'react';

interface DiscoveryRecord {
  timestamp: string;
  city: string;
  query: string;
  result: any;
  agent_name: string;
  region: string;
  discovered_locations?: any[];  // Optional array of UK locations from Beckn API
  assigned_location?: string;  // Agent's assigned UK location
  location_data?: any;  // Location-specific data for assigned location
}

interface AgentDiscoveryData {
  agent_name: string;
  region: string;
  discovery_count: number;
  last_discovery_time: string | null;
  discovery_history: DiscoveryRecord[];
}

interface DiscoveryStatus {
  total_agents: number;
  agents: AgentDiscoveryData[];
}

export default function DiscoveryPage() {
  const [discoveryData, setDiscoveryData] = useState<DiscoveryStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDiscoveryData = async () => {
      try {
        const response = await fetch('http://localhost:8000/discovery/status');
        if (!response.ok) throw new Error('Failed to fetch discovery data');
        const data = await response.json();
        setDiscoveryData(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchDiscoveryData();

    // Auto-refresh every 3 seconds
    const interval = setInterval(fetchDiscoveryData, 3000);

    return () => clearInterval(interval);
  }, []);

  const extractCatalogInfo = (result: any) => {
    try {
      // Beckn API returns catalogs as an array
      const catalogs = result?.message?.catalogs || [];

      let totalItems = 0;
      let avgCarbon = 0;
      let avgRenewable = 0;
      let itemCount = 0;

      catalogs.forEach((catalog: any) => {
        // Items are directly in the catalog, not in providers
        const items = catalog['beckn:items'] || [];
        totalItems += items.length;

        items.forEach((item: any) => {
          const itemAttrs = item['beckn:itemAttributes'];
          const gridParams = itemAttrs?.['beckn:gridParameters'];
          if (gridParams) {
            avgCarbon += gridParams.carbonIntensity || 0;
            avgRenewable += gridParams.renewableMix || 0;
            itemCount++;
          }
        });
      });

      return {
        totalItems,
        avgCarbon: itemCount > 0 ? Math.round(avgCarbon / itemCount) : 0,
        avgRenewable: itemCount > 0 ? Math.round(avgRenewable / itemCount) : 0,
        providers: catalogs.length
      };
    } catch (e) {
      console.error('Error extracting catalog info:', e);
      return { totalItems: 0, avgCarbon: 0, avgRenewable: 0, providers: 0 };
    }
  };

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'Never';
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString();
    } catch {
      return 'Invalid time';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white text-2xl">Loading discovery data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-red-400 text-xl">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <h1 className="text-5xl font-bold text-white mb-4 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">
          Beckn Discovery Monitor
        </h1>
        <p className="text-gray-300 text-lg">
          Real-time monitoring of energy slot discovery across {discoveryData?.total_agents || 0} local agents
        </p>
        <div className="mt-4 flex items-center gap-2">
          <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-green-400 text-sm">Live • Auto-refreshing every 3s</span>
        </div>
      </div>

      {/* Agent Cards Grid */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {discoveryData?.agents.map((agent, idx) => {
          const latestDiscovery = agent.discovery_history[agent.discovery_history.length - 1];
          const catalogInfo = latestDiscovery ? extractCatalogInfo(latestDiscovery.result) : null;

          // Get location-specific data if available
          const locationData = latestDiscovery?.location_data;
          const assignedLocation = latestDiscovery?.assigned_location || agent.agent_name;

          return (
            <div
              key={idx}
              className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 hover:border-purple-400/50 transition-all duration-300 hover:shadow-2xl hover:shadow-purple-500/20"
            >
              {/* Agent Header */}
              <div className="mb-4">
                <h2 className="text-xl font-bold text-white mb-1">{agent.agent_name}</h2>
                <div className="flex items-center gap-2">
                  <span className="text-purple-300 text-sm">📍 {assignedLocation}</span>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-black/30 rounded-lg p-3">
                  <div className="text-gray-400 text-xs mb-1">Total Discoveries</div>
                  <div className="text-white text-2xl font-bold">{agent.discovery_count}</div>
                </div>
                <div className="bg-black/30 rounded-lg p-3">
                  <div className="text-gray-400 text-xs mb-1">Last Discovery</div>
                  <div className="text-white text-sm font-semibold">
                    {formatTimestamp(agent.last_discovery_time)}
                  </div>
                </div>
              </div>

              {/* Latest Discovery Info */}
              {latestDiscovery && (
                <div className="space-y-3">
                  <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-lg p-3 border border-purple-400/30">
                    <div className="text-purple-200 text-xs font-semibold mb-2">Latest Query</div>
                    <div className="text-white text-sm mb-2">🏙️ {latestDiscovery.city}</div>
                    <div className="text-gray-300 text-xs italic">"{latestDiscovery.query}"</div>
                  </div>

                  {/* Display location-specific data */}
                  {locationData && (
                    <div className="space-y-2">
                      <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 mb-2">
                        <div className="text-blue-200 text-xs font-semibold mb-1">
                          {locationData.locality}, {locationData.region}
                        </div>
                        <div className="text-gray-400 text-xs">
                          {locationData.grid_area} • {locationData.grid_zone}
                        </div>
                      </div>

                      <div className="flex items-center justify-between bg-black/30 rounded-lg p-2">
                        <span className="text-gray-400 text-xs">Carbon Intensity</span>
                        <span className="text-yellow-400 font-bold">{locationData.carbon_intensity} gCO₂/kWh</span>
                      </div>
                      <div className="flex items-center justify-between bg-black/30 rounded-lg p-2">
                        <span className="text-gray-400 text-xs">Renewable Mix</span>
                        <span className="text-green-400 font-bold">{locationData.renewable_mix}%</span>
                      </div>
                      <div className="flex items-center justify-between bg-black/30 rounded-lg p-2">
                        <span className="text-gray-400 text-xs">Available Capacity</span>
                        <span className="text-blue-400 font-bold">{locationData.available_capacity} MW</span>
                      </div>
                      {locationData.price && (
                        <div className="flex items-center justify-between bg-black/30 rounded-lg p-2">
                          <span className="text-gray-400 text-xs">
                            Cost
                            {locationData.price_source === 'estimated' && (
                              <span className="ml-1 text-xs text-cyan-400" title="Estimated">📊</span>
                            )}
                          </span>
                          <div className="flex items-center gap-1">
                            <span className="text-purple-400 font-bold">
                              {Number(locationData.price).toFixed(3)} GBP/kWh
                            </span>
                            {locationData.price_source === 'estimated' && (
                              <span className="text-xs text-cyan-400 font-semibold" title="Estimated by DataGenerator">EST</span>
                            )}
                          </div>
                        </div>
                      )}
                      <div className="flex items-center justify-between bg-black/30 rounded-lg p-2">
                        <span className="text-gray-400 text-xs">Items Found</span>
                        <span className="text-green-400 font-bold">{catalogInfo?.totalItems || 0}</span>
                      </div>
                    </div>
                  )}

                  {!locationData && catalogInfo && catalogInfo.totalItems > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between bg-black/30 rounded-lg p-2">
                        <span className="text-gray-400 text-xs">Items Found</span>
                        <span className="text-green-400 font-bold">{catalogInfo.totalItems}</span>
                      </div>
                      <div className="flex items-center justify-between bg-black/30 rounded-lg p-2">
                        <span className="text-gray-400 text-xs">Avg Carbon</span>
                        <span className="text-yellow-400 font-bold">{catalogInfo.avgCarbon} gCO₂/kWh</span>
                      </div>
                      <div className="flex items-center justify-between bg-black/30 rounded-lg p-2">
                        <span className="text-gray-400 text-xs">Avg Renewable</span>
                        <span className="text-green-400 font-bold">{catalogInfo.avgRenewable}%</span>
                      </div>
                    </div>
                  )}

                  {!locationData && (!catalogInfo || catalogInfo.totalItems === 0) && (
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                      <div className="text-yellow-400 text-xs">No location data available yet</div>
                    </div>
                  )}
                </div>
              )}

              {!latestDiscovery && (
                <div className="bg-gray-500/10 border border-gray-500/30 rounded-lg p-4 text-center">
                  <div className="text-gray-400 text-sm">No discoveries yet</div>
                </div>
              )}

              {/* Discovery History Count */}
              <div className="mt-4 pt-4 border-t border-white/10">
                <div className="text-gray-400 text-xs">
                  Recent history: {agent.discovery_history.length} records
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty State */}
      {(!discoveryData?.agents || discoveryData.agents.length === 0) && (
        <div className="max-w-7xl mx-auto text-center py-20">
          <div className="text-gray-400 text-xl">No agents discovered yet</div>
          <div className="text-gray-500 text-sm mt-2">Waiting for agents to start discovery...</div>
        </div>
      )}
    </div>
  );
}
