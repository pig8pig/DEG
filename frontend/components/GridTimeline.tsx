"use client";

import React, { useEffect, useState } from 'react';
import { Clock, MapPin, Zap, Activity } from 'lucide-react';

interface LocationPeriod {
  start: string;
  end: string;
  utilization: number;
  carbonIntensity: number;
  renewableMix: number;
  activeJobs: string[];
}

interface LocationTimeline {
  location: string;
  region: string;
  lat: number;
  lon: number;
  periods: LocationPeriod[];
  currentUtilization: number;
}

interface GridTimelineProps {
  data: LocationTimeline[];
}

const GridTimeline: React.FC<GridTimelineProps> = ({ data }) => {
  const getUtilizationColor = (utilization: number) => {
    if (utilization === 0) return 'bg-green-500';
    if (utilization < 50) return 'bg-yellow-500';
    if (utilization < 80) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getUtilizationLabel = (utilization: number) => {
    if (utilization === 0) return 'Available';
    if (utilization < 50) return 'Light';
    if (utilization < 80) return 'Moderate';
    return 'Busy';
  };

  const getPriorityColor = (priority: number) => {
    switch (priority) {
      case 1: return 'bg-blue-500';      // Lowest priority
      case 2: return 'bg-green-500';     // Low priority
      case 3: return 'bg-yellow-500';    // Medium priority
      case 4: return 'bg-orange-500';    // High priority
      case 5: return 'bg-purple-600';    // Highest priority
      default: return 'bg-gray-500';     // Unknown priority
    }
  };

  const getPriorityLabel = (priority: number) => {
    switch (priority) {
      case 1: return 'Lowest';
      case 2: return 'Low';
      case 3: return 'Medium';
      case 4: return 'High';
      case 5: return 'Highest';
      default: return 'Unknown';
    }
  };

  return (
    <div className="space-y-4">
      {data.map((location, idx) => (
        <div key={idx} className="bg-[#161b22] rounded-xl border border-gray-800 p-6 hover:border-gray-700 transition-all">
          {/* Location Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-600/10 rounded-lg">
                <MapPin className="text-blue-400" size={20} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">{location.location}</h3>
                <p className="text-sm text-gray-400">{location.region}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-xs text-gray-500">Current Status</div>
                <div className={`text-sm font-bold ${
                  location.currentUtilization === 0 ? 'text-green-400' :
                  location.currentUtilization < 50 ? 'text-yellow-400' :
                  location.currentUtilization < 80 ? 'text-orange-400' :
                  'text-red-400'
                }`}>
                  {getUtilizationLabel(location.currentUtilization)}
                </div>
              </div>
              <div className={`w-3 h-3 rounded-full ${getUtilizationColor(location.currentUtilization)} animate-pulse`}></div>
            </div>
          </div>

          {/* Timeline Visualization */}
          <div className="space-y-2">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Clock size={14} />
                <span>Past 24 Hours → Future 24 Hours</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span>Priority:</span>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 bg-blue-500 rounded"></div>
                  <span>1</span>
                  <div className="w-3 h-3 bg-green-500 rounded ml-1"></div>
                  <span>2</span>
                  <div className="w-3 h-3 bg-yellow-500 rounded ml-1"></div>
                  <span>3</span>
                  <div className="w-3 h-3 bg-orange-500 rounded ml-1"></div>
                  <span>4</span>
                  <div className="w-3 h-3 bg-purple-600 rounded ml-1"></div>
                  <span>5</span>
                </div>
              </div>
            </div>
            
            <div className="relative h-12 bg-gray-900 rounded-lg overflow-hidden">
              {/* Time markers */}
              <div className="absolute inset-0 flex">
                {[-24, -18, -12, -6, 0, 6, 12, 18, 24].map((hour) => (
                  <div
                    key={hour}
                    className={`absolute top-0 bottom-0 ${hour === 0 ? 'border-l-2 border-blue-500' : 'border-l border-gray-700'}`}
                    style={{ left: `${((hour + 24) / 48) * 100}%` }}
                  >
                    <span className={`absolute -bottom-5 -translate-x-1/2 text-xs ${hour === 0 ? 'text-blue-400 font-bold' : 'text-gray-600'}`}>
                      {hour === 0 ? 'Now' : `${hour > 0 ? '+' : ''}${hour}h`}
                    </span>
                  </div>
                ))}
              </div>

              {/* Current time indicator */}
              <div 
                className="absolute top-0 bottom-0 w-0.5 bg-blue-500 z-10"
                style={{ left: '50%' }}
              >
                <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              </div>

              {/* Utilization periods */}
              {location.periods.map((period, periodIdx) => {
                const startTime = new Date(period.start).getTime();
                const endTime = new Date(period.end).getTime();
                const now = Date.now();
                const dayAgo = now - 24 * 60 * 60 * 1000;
                const dayAhead = now + 24 * 60 * 60 * 1000;
                
                // Calculate position relative to 48-hour window (24h past + 24h future)
                const left = Math.max(0, ((startTime - dayAgo) / (48 * 60 * 60 * 1000)) * 100);
                const width = ((endTime - startTime) / (48 * 60 * 60 * 1000)) * 100;
                
                // Determine if this is a future period
                const isFuture = startTime > now;
                
                if (left >= 0 && left <= 100) {
                  // Use priority color if available, otherwise fall back to utilization color
                  const priority = (period as any).priority;
                  const barColor = priority ? getPriorityColor(priority) : getUtilizationColor(period.utilization);
                  
                  return (
                    <div
                      key={periodIdx}
                      className={`absolute top-0 bottom-0 ${barColor} ${
                        isFuture ? 'opacity-50 border-l-2 border-dashed border-gray-600' : 'opacity-80'
                      } hover:opacity-100 transition-opacity group cursor-pointer`}
                      style={{
                        left: `${left}%`,
                        width: `${Math.min(width, 100 - left)}%`
                      }}
                    >
                      {/* Tooltip */}
                      <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-gray-900 border border-gray-700 rounded-lg p-3 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 whitespace-nowrap shadow-xl">
                        <div className="text-xs space-y-1">
                          <div className="font-bold text-white flex items-center gap-2">
                            {isFuture && <span className="text-blue-400 text-[10px] uppercase">Scheduled</span>}
                            {new Date(period.start).toLocaleTimeString()} - {new Date(period.end).toLocaleTimeString()}
                          </div>
                          {period.activeJobs && period.activeJobs.length > 0 && (
                            <>
                              <div className="text-gray-400">Job ID: {period.activeJobs[0].substring(0, 8)}...</div>
                              {(period as any).priority && (
                                <div className="font-semibold" style={{ color: barColor.replace('bg-', '#') }}>
                                  Priority: {(period as any).priority} ({getPriorityLabel((period as any).priority)})
                                </div>
                              )}
                              {(period as any).duration_hrs && (
                                <div className="text-gray-400">Duration: {(period as any).duration_hrs}h</div>
                              )}
                              {(period as any).status && (
                                <div className="text-gray-400">Status: {(period as any).status}</div>
                              )}
                            </>
                          )}
                          <div className="text-gray-400 flex items-center gap-1">
                            <Zap size={12} className="text-yellow-400" />
                            Carbon: {period.carbonIntensity} gCO₂/kWh
                          </div>
                          <div className="text-gray-400 flex items-center gap-1">
                            <Activity size={12} className="text-green-400" />
                            Renewable: {period.renewableMix}%
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                }
                return null;
              })}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-800">
            <div>
              <div className="text-xs text-gray-500">Avg Carbon</div>
              <div className="text-sm font-bold text-gray-300">
                {location.periods.length > 0
                  ? Math.round(location.periods.reduce((sum, p) => sum + p.carbonIntensity, 0) / location.periods.length)
                  : 0} gCO₂/kWh
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Avg Renewable</div>
              <div className="text-sm font-bold text-green-400">
                {location.periods.length > 0
                  ? Math.round(location.periods.reduce((sum, p) => sum + p.renewableMix, 0) / location.periods.length)
                  : 0}%
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Total Jobs</div>
              <div className="text-sm font-bold text-blue-400">
                {location.periods.reduce((sum, p) => sum + p.activeJobs.length, 0)}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default GridTimeline;
