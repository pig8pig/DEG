"use client";

import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AgentStatus from './AgentStatus';
import AgentInteractionHub from './AgentInteractionHub';
import EnergyChart from './EnergyChart';
import { Play, Pause, Activity, Terminal, Zap, Globe } from 'lucide-react';
import Link from 'next/link';

import dynamic from 'next/dynamic';

const Map = dynamic(() => import('./Map'), {
  ssr: false,
  loading: () => <div className="h-[400px] w-full bg-[#161b22] rounded-xl animate-pulse border border-gray-800 flex items-center justify-center text-gray-500">Loading Map...</div>
});

const Dashboard = () => {
  const [status, setStatus] = useState<any>(null);
  const [isRunning, setIsRunning] = useState(false);

  const fetchData = async () => {
    try {
      const res = await axios.get('http://localhost:8000/status');
      setStatus(res.data);
    } catch (error) {
      console.error("Error fetching status:", error);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000); // Poll every 2 seconds
    return () => clearInterval(interval);
  }, []);

  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const toggleSimulation = async () => {
    try {
      if (isRunning) {
        await axios.post('http://localhost:8000/control/stop');
      } else {
        await axios.post('http://localhost:8000/control/start');
      }
      setIsRunning(!isRunning);
    } catch (error) {
      console.error("Error toggling simulation:", error);
    }
  };

  // Flatten all local agents from all regions
  const allAgents = status?.regions?.flatMap((r: any) => r.local_agents || []) || [];

  return (
    <div className="min-h-screen bg-[#0f1117] text-gray-100 font-sans selection:bg-blue-500/30">
      {/* Header */}
      <header className="bg-[#161b22] border-b border-gray-800 sticky top-0 z-50 backdrop-blur-md bg-opacity-80">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-blue-600 rounded-lg shadow-lg shadow-blue-600/20">
              <Globe className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">
                Digital Energy Grid
              </h1>
              <p className="text-sm text-gray-400 font-medium">Autonomous Multi-Agent Orchestration</p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 px-4 py-2 bg-gray-800 rounded-full border border-gray-700">
              <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
              <span className="text-sm font-medium text-gray-300">{isRunning ? 'System Active' : 'System Paused'}</span>
            </div>

            <div className="flex items-center gap-2 px-4 py-2 bg-gray-800 rounded-full border border-gray-700">
              <span className="text-sm font-mono text-blue-400 font-bold">
                {currentTime.toLocaleTimeString([], { hour12: false })}
              </span>
            </div>

            <Link
              href="/"
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg border border-gray-700 transition-colors text-sm font-medium"
            >
              Grid Timeline
            </Link>

            <button
              onClick={toggleSimulation}
              className={`flex items-center gap-2 px-6 py-2.5 rounded-lg font-bold transition-all transform active:scale-95 ${isRunning
                ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/50'
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/25'
                }`}
            >
              {isRunning ? <Pause size={18} /> : <Play size={18} />}
              {isRunning ? 'Stop Simulation' : 'Start Simulation'}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Left Column: Map & Agent Grid */}
          <div className="lg:col-span-2 space-y-6">
            {/* Map Section */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold flex items-center gap-2 text-gray-100">
                  <Globe size={20} className="text-green-400" />
                  Live Geospatial View
                </h2>
              </div>
              <Map agents={allAgents} />
            </div>

            <div className="flex items-center justify-between pt-4">
              <h2 className="text-xl font-bold flex items-center gap-2 text-gray-100">
                <Activity size={20} className="text-blue-400" />
                Regional Network Status
              </h2>
              <span className="text-sm text-gray-500">Updating real-time...</span>
            </div>
            <AgentStatus data={status} />
          </div>

          {/* Right Column: Metrics & Logs */}
          <div className="space-y-8">
            {/* Energy Chart Card */}
            <div>
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-gray-100">
                <Zap size={20} className="text-yellow-400" />
                Global Metrics
              </h2>
              <EnergyChart logs={status?.logs || []} />
            </div>

            {/* Logs Console */}
            <div className="bg-[#161b22] rounded-2xl border border-gray-800 overflow-hidden flex flex-col h-[400px]">
              <div className="px-4 py-3 border-b border-gray-800 bg-gray-900/50 flex items-center gap-2">
                <Terminal size={16} className="text-gray-400" />
                <h3 className="font-bold text-sm text-gray-300">System Event Log</h3>
              </div>
              <div className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                {status?.logs?.slice().reverse().map((log: any, i: number) => {
                  const timestamp = typeof log === 'string' ? new Date().toLocaleTimeString() : new Date(log.timestamp).toLocaleTimeString();
                  const message = typeof log === 'string' ? log : log.message;

                  // Extract priority from message if present (e.g., "Priority 3" or "(Priority 5)")
                  const priorityMatch = message.match(/\(Priority (\d)\)|Priority (\d)/);
                  const priority = priorityMatch ? parseInt(priorityMatch[1] || priorityMatch[2]) : null;

                  // Get priority color
                  const getPriorityColor = (p: number) => {
                    switch (p) {
                      case 1: return 'text-blue-400';
                      case 2: return 'text-green-400';
                      case 3: return 'text-yellow-400';
                      case 4: return 'text-orange-400';
                      case 5: return 'text-purple-400';
                      default: return 'text-gray-400';
                    }
                  };

                  // Determine if this is a success or failure message
                  const isSuccess = message.includes('✓');
                  const isFailure = message.includes('✗');

                  return (
                    <div key={i} className={`flex gap-3 ${priority ? getPriorityColor(priority) : 'text-gray-400'} hover:text-gray-200 transition-colors border-b border-gray-800/50 pb-1 last:border-0`}>
                      <span className="text-gray-600 select-none">[{timestamp}]</span>
                      <span className={isSuccess ? 'text-green-400' : isFailure ? 'text-red-400' : ''}>{message}</span>
                    </div>
                  );
                })}
                {!status?.logs?.length && (
                  <div className="text-gray-600 italic text-center mt-10">No events recorded yet...</div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Agent Interaction Section */}
        <div className="mt-8">
          <AgentInteractionHub data={status} />
        </div>
      </main>
    </div >
  );
};

export default Dashboard;
