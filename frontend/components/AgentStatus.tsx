"use client";

import React from 'react';
import { Server, Activity, Zap, Cloud, Cpu } from 'lucide-react';

interface AgentStatusProps {
  data: any;
}

const AgentStatus: React.FC<AgentStatusProps> = ({ data }) => {
  if (!data || !data.regions) return (
    <div className="flex items-center justify-center h-64 text-gray-400 animate-pulse">
      Waiting for agent network...
    </div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-6">
      {data.regions.map((region: any, idx: number) => {
        const capacityPercentage = (region.total_used / region.total_capacity) * 100;
        const isHighLoad = capacityPercentage > 80;
        
        return (
          <div key={idx} className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-2xl overflow-hidden hover:border-blue-500/50 transition-colors">
            {/* Region Header */}
            <div className="p-5 border-b border-gray-700/50 bg-gray-800/80 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                  <Cloud size={24} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-100">{region.region}</h3>
                  <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Regional Node</p>
                </div>
              </div>
              <div className={`px-3 py-1 rounded-full text-xs font-bold border ${
                isHighLoad 
                  ? 'bg-red-500/10 border-red-500/20 text-red-400' 
                  : 'bg-green-500/10 border-green-500/20 text-green-400'
              }`}>
                {isHighLoad ? 'HIGH LOAD' : 'OPTIMAL'}
              </div>
            </div>
            
            <div className="p-5 space-y-6">
              {/* Capacity Meter */}
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-400 flex items-center gap-2">
                    <Cpu size={16} /> Compute Load
                  </span>
                  <span className="font-mono font-medium text-gray-200">
                    {(region.total_used || 0).toLocaleString()} / {(region.total_capacity || 0).toLocaleString()} units
                  </span>
                </div>
                <div className="w-full bg-gray-700/50 rounded-full h-3 overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-1000 ease-out ${
                      isHighLoad ? 'bg-gradient-to-r from-red-500 to-orange-500' : 'bg-gradient-to-r from-blue-500 to-cyan-400'
                    }`}
                    style={{ width: `${capacityPercentage}%` }}
                  ></div>
                </div>
              </div>

              {/* Local Agents List */}
              <div>
                <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Top Local Providers</h4>
                <div className="space-y-2">
                  {(region.lowest_cost_options || []).slice(0, 3).map((opt: any, i: number) => (
                    <div key={i} className="flex justify-between items-center p-3 rounded-xl bg-gray-900/50 border border-gray-700/50 hover:bg-gray-700/30 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.5)]"></div>
                        <span className="text-sm font-medium text-gray-200">{opt.agent_name.replace(' Local', '')}</span>
                      </div>
                      <div className="flex gap-4 text-sm">
                        <div className="flex flex-col items-end">
                          <span className="text-xs text-gray-500">Price</span>
                          <span className="text-green-400 font-mono font-bold">${opt.cost}</span>
                        </div>
                        <div className="flex flex-col items-end w-16">
                          <span className="text-xs text-gray-500">Carbon</span>
                          <span className="text-yellow-400 font-mono font-bold">{opt.carbon}g</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default AgentStatus;
