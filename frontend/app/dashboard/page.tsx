"use client";

import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import Dashboard from '../../components/Dashboard';

export default function DashboardPage() {
  return (
    <div className="relative">
      {/* Back to Timeline Link */}
      <div className="absolute top-4 right-4 z-50">
        <Link 
          href="/"
          className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg border border-gray-700 transition-colors text-sm font-medium"
        >
          <ArrowLeft size={16} />
          Back to Timeline
        </Link>
      </div>
      
      <Dashboard />
    </div>
  );
}
