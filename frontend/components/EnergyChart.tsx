"use client";

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

interface EnergyChartProps {
  logs: any[];
}

const EnergyChart: React.FC<EnergyChartProps> = ({ logs }) => {
  // In a real app, we'd parse logs or have a dedicated history endpoint.
  // For now, we'll mock some data or just show a placeholder if no history.
  
  const data = [
    { name: '00:00', price: 40, carbon: 240 },
    { name: '04:00', price: 30, carbon: 139 },
    { name: '08:00', price: 20, carbon: 980 },
    { name: '12:00', price: 27, carbon: 390 },
    { name: '16:00', price: 18, carbon: 480 },
    { name: '20:00', price: 23, carbon: 380 },
    { name: '23:59', price: 34, carbon: 430 },
  ];

  return (
    <div className="bg-[#161b22] p-5 rounded-2xl border border-gray-800 shadow-xl">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Market Signals</h3>
        <div className="flex gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
            <span className="text-gray-400">Price ($)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-amber-400"></div>
            <span className="text-gray-400">Carbon (g)</span>
          </div>
        </div>
      </div>
      
      <div className="h-[250px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#34D399" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#34D399" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorCarbon" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#FBBF24" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#FBBF24" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" vertical={false} />
            <XAxis 
              dataKey="name" 
              stroke="#6B7280" 
              tick={{fill: '#6B7280', fontSize: 10}} 
              axisLine={false}
              tickLine={false}
            />
            <YAxis 
              stroke="#6B7280" 
              tick={{fill: '#6B7280', fontSize: 10}} 
              axisLine={false}
              tickLine={false}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1F2937', 
                borderColor: '#374151', 
                color: '#F3F4F6',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              itemStyle={{ fontSize: '12px' }}
            />
            <Area 
              type="monotone" 
              dataKey="price" 
              stroke="#34D399" 
              strokeWidth={2} 
              fillOpacity={1} 
              fill="url(#colorPrice)" 
            />
            <Area 
              type="monotone" 
              dataKey="carbon" 
              stroke="#FBBF24" 
              strokeWidth={2} 
              fillOpacity={1} 
              fill="url(#colorCarbon)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default EnergyChart;
