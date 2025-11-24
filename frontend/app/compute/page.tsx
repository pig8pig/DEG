"use client";

import React, { useState, useEffect } from 'react';

interface ComputeJob {
  job_id: string;
  status: string;
  estimated_runtime_hrs: number;
  priority: number;
}

export default function ComputePage() {
  const [jobs, setJobs] = useState<ComputeJob[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Form state
  const [runtime, setRuntime] = useState(1.0);
  const [priority, setPriority] = useState(1);

  const fetchJobs = async () => {
    try {
      const res = await fetch('http://localhost:8000/jobs');
      const data = await res.json();
      if (data.jobs) {
        setJobs(data.jobs);
      }
    } catch (error) {
      console.error("Failed to fetch jobs:", error);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await fetch('http://localhost:8000/jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          estimated_runtime_hrs: runtime,
          priority: priority,
          status: "PENDING"
        }),
      });
      await fetchJobs();
    } catch (error) {
      console.error("Failed to submit job:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-blue-400">Compute Job Simulation</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Submission Form */}
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg h-fit">
            <h2 className="text-xl font-semibold mb-4">Submit New Job</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Estimated Runtime (Hours)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={runtime}
                  onChange={(e) => setRuntime(parseFloat(e.target.value))}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Priority (1-5)
                </label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(parseInt(e.target.value))}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                >
                  {[1, 2, 3, 4, 5].map(p => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </div>
              
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors disabled:opacity-50"
              >
                {loading ? 'Submitting...' : 'Submit Job'}
              </button>
            </form>
          </div>
          
          {/* Job List */}
          <div className="md:col-span-2 bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 className="text-xl font-semibold mb-4">Job Status</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="text-gray-400 border-b border-gray-700">
                  <tr>
                    <th className="pb-3 px-2">Job ID</th>
                    <th className="pb-3 px-2">Runtime</th>
                    <th className="pb-3 px-2">Priority</th>
                    <th className="pb-3 px-2">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {jobs.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-4 text-center text-gray-500">
                        No jobs submitted yet.
                      </td>
                    </tr>
                  ) : (
                    jobs.map((job) => (
                      <tr key={job.job_id} className="hover:bg-gray-750">
                        <td className="py-3 px-2 font-mono text-sm text-gray-300">
                          {job.job_id.substring(0, 8)}...
                        </td>
                        <td className="py-3 px-2">{job.estimated_runtime_hrs}h</td>
                        <td className="py-3 px-2">{job.priority}</td>
                        <td className="py-3 px-2">
                          <span className={`inline-block px-2 py-1 rounded text-xs font-semibold
                            ${job.status === 'COMPLETED' ? 'bg-green-900 text-green-200' : 
                              job.status === 'ASSIGNED' ? 'bg-blue-900 text-blue-200' : 
                              job.status === 'FAILED' ? 'bg-red-900 text-red-200' : 
                              'bg-yellow-900 text-yellow-200'}`}>
                            {job.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
