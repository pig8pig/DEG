"use client";

import React from 'react';
import { MessageSquare, Bot, MapPin, TrendingUp, ShieldCheck } from 'lucide-react';

interface AgentInteractionHubProps {
  data: any;
}

const AgentInteractionHub: React.FC<AgentInteractionHubProps> = ({ data }) => {
  if (!data || !data.regions) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
          <MessageSquare size={24} />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-100">Agent Communication Hub</h2>
          <p className="text-sm text-gray-400">Real-time LLM Synthesis & Negotiation</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {data.regions.map((region: any, idx: number) => (
          <div key={idx} className="bg-[#0d1117] border border-gray-800 rounded-2xl overflow-hidden flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-800 bg-gray-900/50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="text-green-400" size={18} />
                <span className="font-bold text-gray-200">{region.region} Channel</span>
              </div>
              <span className="text-xs font-mono text-gray-500">Live Feed</span>
            </div>

            {/* Content Area */}
            <div className="p-4 space-y-6 flex-1 overflow-y-auto max-h-[600px] scrollbar-thin scrollbar-thumb-gray-700">
              
              {/* Local Agent Reports (Incoming) */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider sticky top-0 bg-[#0d1117] py-2 z-10">
                  Incoming Local Reports
                </h4>
                
                {region.agent_summaries?.map((summary: any, sIdx: number) => (
                  <div key={sIdx} className="flex gap-3">
                    <div className="mt-1">
                      <div className="w-8 h-8 rounded-full bg-blue-600/20 flex items-center justify-center border border-blue-500/30">
                        <Bot size={14} className="text-blue-400" />
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-bold text-blue-400">{summary.agent_name}</span>
                        <span className="text-xs text-gray-500 flex items-center gap-1">
                          <MapPin size={10} /> {summary.location}
                        </span>
                      </div>
                      <div className="bg-blue-900/10 border border-blue-500/20 rounded-r-xl rounded-bl-xl p-3 text-sm text-gray-300 leading-relaxed">
                        {summary.summary}
                      </div>
                    </div>
                  </div>
                ))}
                
                {(!region.agent_summaries || region.agent_summaries.length === 0) && (
                  <div className="text-center py-4 text-gray-600 italic text-sm">
                    Waiting for local agent reports...
                  </div>
                )}
              </div>

              {/* Regional Synthesis (Outgoing/Analysis) */}
              <div className="pt-4 border-t border-gray-800">
                <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                  <TrendingUp size={14} /> Regional Coordinator Analysis
                </h4>
                
                {region.regional_ranking ? (
                  <div className="flex gap-3">
                    <div className="mt-1">
                      <div className="w-8 h-8 rounded-full bg-purple-600/20 flex items-center justify-center border border-purple-500/30">
                        <ShieldCheck size={14} className="text-purple-400" />
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-bold text-purple-400">{region.region} Coordinator</span>
                        <span className="text-xs text-gray-500">Synthesized Ranking</span>
                      </div>
                      <div className="bg-purple-900/10 border border-purple-500/20 rounded-r-xl rounded-bl-xl p-4 text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                        {region.regional_ranking}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-600 italic text-sm">
                    Analyzing reports...
                  </div>
                )}
              </div>

            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentInteractionHub;
