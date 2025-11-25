"use client";

import React, { useEffect, useState } from 'react';
import axios from 'axios';
import GridTimeline from '../components/GridTimeline';
import { Globe, Activity, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

interface LocationTimeline {
  location: string;
  region: string;
  lat: number;
  lon: number;
  periods: Array<{
    start: string;
    end: string;
    utilization: number;
    carbonIntensity: number;
    renewableMix: number;
    activeJobs: string[];
  }>;
  currentUtilization: number;
}

export default function Home() {
  const [timelineData, setTimelineData] = useState<LocationTimeline[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRegion, setSelectedRegion] = useState<string>('all');

  const fetchTimelineData = async () => {
    try {
      const res = await axios.get('http://localhost:8000/discovery/status');
      const agents = res.data.agents || [];
      
      // Transform agent data into timeline format
      const timelines: LocationTimeline[] = agents.map((agent: any) => {
        const locationData = agent.location_data || {};
        const jobSchedule = agent.job_schedule || [];
        
        // Sort jobs by start time (chronological order)
        const sortedJobs = [...jobSchedule].sort((a, b) => {
          const timeA = new Date(a.start_time).getTime();
          const timeB = new Date(b.start_time).getTime();
          return timeA - timeB;
        });
        
        // Convert job schedule to timeline periods
        const jobPeriods = sortedJobs.map((job: any) => {
          // Validate and parse timing data
          const startTime = job.start_time ? new Date(job.start_time) : new Date();
          const endTime = job.end_time 
            ? new Date(job.end_time) 
            : new Date(startTime.getTime() + (job.duration_hrs || 1) * 3600000);
          
          return {
            start: startTime.toISOString(),
            end: endTime.toISOString(),
            utilization: 100, // Job is running = 100% utilization for that slot
            carbonIntensity: locationData.carbon_intensity || 0,
            renewableMix: locationData.renewable_mix || 0,
            activeJobs: [job.job_id],
            priority: job.priority,
            duration_hrs: job.duration_hrs,
            status: job.status,
            submitted_at: job.submitted_at,
            must_start_by: job.must_start_by
          };
        });
        
        // Calculate current utilization based on if any job is running now
        const now = Date.now();
        const currentlyRunning = jobPeriods.filter(period => {
          const start = new Date(period.start).getTime();
          const end = new Date(period.end).getTime();
          return start <= now && now <= end;
        });
        
        return {
          location: agent.assigned_location || agent.agent_name,
          region: agent.region,
          lat: 0,
          lon: 0,
          periods: jobPeriods, // Jobs are now sorted chronologically
          currentUtilization: currentlyRunning.length > 0 ? 100 : 0
        };
      });
      
      setTimelineData(timelines);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching timeline data:", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimelineData();
    const interval = setInterval(fetchTimelineData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const filteredData = selectedRegion === 'all' 
    ? timelineData 
    : timelineData.filter(t => t.region === selectedRegion);

  const regions = ['all', ...Array.from(new Set(timelineData.map(t => t.region)))];

  return (
    <div className="min-h-screen bg-[#0f1117] text-gray-100">
      {/* Header */}
      <header className="bg-[#161b22] border-b border-gray-800 sticky top-0 z-50 backdrop-blur-md bg-opacity-80">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-2 bg-blue-600 rounded-lg shadow-lg shadow-blue-600/20">
                <Globe className="text-white" size={24} />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  Grid Location Timelines
                </h1>
                <p className="text-sm text-gray-400 font-medium">Real-time capacity and utilization tracking</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <Link 
                href="/dashboard"
                className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg border border-gray-700 transition-colors text-sm font-medium"
              >
                Agent Dashboard
              </Link>
              <Link 
                href="/compute"
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors text-sm font-medium shadow-lg shadow-blue-600/25"
              >
                <ArrowLeft size={16} />
                Submit Jobs
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Region Filter */}
        <div className="mb-6 flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Activity size={16} />
            <span>Filter by region:</span>
          </div>
          <div className="flex gap-2">
            {regions.map((region) => (
              <button
                key={region}
                onClick={() => setSelectedRegion(region)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedRegion === region
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/25'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700 border border-gray-700'
                }`}
              >
                {region === 'all' ? 'All Regions' : region}
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Grid */}
        {loading ? (
          <div className="text-center py-20">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="mt-4 text-gray-400">Loading timeline data...</p>
          </div>
        ) : filteredData.length === 0 ? (
          <div className="text-center py-20 bg-[#161b22] rounded-xl border border-gray-800">
            <Activity className="mx-auto text-gray-600 mb-4" size={48} />
            <p className="text-gray-400">No location data available yet.</p>
            <p className="text-sm text-gray-600 mt-2">Data will appear as agents discover grid windows.</p>
          </div>
        ) : (
          <GridTimeline data={filteredData} />
        )}

        {/* Summary Stats */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-[#161b22] rounded-xl border border-gray-800 p-6">
            <div className="text-sm text-gray-500 mb-1">Total Locations</div>
            <div className="text-3xl font-bold text-white">{timelineData.length}</div>
          </div>
          <div className="bg-[#161b22] rounded-xl border border-gray-800 p-6">
            <div className="text-sm text-gray-500 mb-1">Available Now</div>
            <div className="text-3xl font-bold text-green-400">
              {timelineData.filter(t => t.currentUtilization === 0).length}
            </div>
          </div>
          <div className="bg-[#161b22] rounded-xl border border-gray-800 p-6">
            <div className="text-sm text-gray-500 mb-1">Busy Now</div>
            <div className="text-3xl font-bold text-red-400">
              {timelineData.filter(t => t.currentUtilization >= 80).length}
            </div>
          </div>
          <div className="bg-[#161b22] rounded-xl border border-gray-800 p-6">
            <div className="text-sm text-gray-500 mb-1">Avg Utilization</div>
            <div className="text-3xl font-bold text-blue-400">
              {timelineData.length > 0
                ? Math.round(timelineData.reduce((sum, t) => sum + t.currentUtilization, 0) / timelineData.length)
                : 0}%
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
