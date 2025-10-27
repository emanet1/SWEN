import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  DollarSign, 
  AlertTriangle,
  RefreshCw
} from 'lucide-react';

interface PendingWorkload {
  workload_id: string;
  timestamp: string;
  estimated_savings: number;
  aws_cost: number;
  alibaba_cost: number;
  recommended_provider: string;
  status: string;
  reason: string;
}

const ApprovalDashboard: React.FC = () => {
  const [pendingWorkloads, setPendingWorkloads] = useState<PendingWorkload[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    fetchPendingWorkloads();
    
    // Refresh every 10 seconds
    const interval = setInterval(fetchPendingWorkloads, 10000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchPendingWorkloads = async () => {
    try {
      const response = await fetch('http://localhost:8080/pending');
      if (response.ok) {
        const data = await response.json();
        // Handle both direct array and wrapped response
        let workloadsArray = [];
        if (Array.isArray(data)) {
          workloadsArray = data;
        } else if (data && Array.isArray(data.pending_workloads)) {
          workloadsArray = data.pending_workloads;
        }
        setPendingWorkloads(workloadsArray);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('Failed to fetch pending workloads:', error);
      // Set empty array on error to prevent crashes
      setPendingWorkloads([]);
    }
  };

  const approveWorkload = async (workloadId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8080/approve/${workloadId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ approved: true }),
      });

      if (response.ok) {
        // Refresh the list
        await fetchPendingWorkloads();
      }
    } catch (error) {
      console.error('Error approving workload:', error);
    } finally {
      setLoading(false);
    }
  };

  const rejectWorkload = async (workloadId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8080/approve/${workloadId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ approved: false }),
      });

      if (response.ok) {
        // Refresh the list
        await fetchPendingWorkloads();
      }
    } catch (error) {
      console.error('Error rejecting workload:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => `$${amount.toFixed(3)}`;
  const formatTime = (timestamp: string) => new Date(timestamp).toLocaleTimeString();

  const totalSavings = pendingWorkloads.reduce((sum, w) => sum + w.estimated_savings, 0);
  const highPriorityCount = pendingWorkloads.filter(w => w.estimated_savings > 0.01).length;

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>SWEN AI - Approval Dashboard</title>
        <meta name="description" content="AI Decision Approval Dashboard" />
      </Head>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">AI Decision Approval Dashboard</h1>
              <p className="mt-2 text-gray-600">Review and approve AI routing decisions</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                Last update: {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
              </div>
              <button
                onClick={fetchPendingWorkloads}
                disabled={loading}
                className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <Clock className="w-8 h-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Pending Decisions</p>
                <p className="text-2xl font-bold text-gray-900">{pendingWorkloads.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <DollarSign className="w-8 h-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Potential Savings</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalSavings)}/hr</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <AlertTriangle className="w-8 h-8 text-orange-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">High Priority</p>
                <p className="text-2xl font-bold text-gray-900">{highPriorityCount}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Workloads List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Pending Workload Decisions</h2>
          </div>
          
          <div className="p-6">
            {pendingWorkloads.length === 0 ? (
              <div className="text-center py-12">
                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Pending Decisions</h3>
                <p className="text-gray-600">All AI decisions have been processed!</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {pendingWorkloads.map((workload) => (
                  <div key={workload.workload_id} className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-medium text-gray-900">
                            Workload {workload.workload_id}
                          </h3>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            workload.status === 'pending_approval' 
                              ? 'bg-yellow-100 text-yellow-800' 
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {workload.status.replace('_', ' ')}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                          <div>
                            <p className="text-sm text-gray-600">Recommended Provider</p>
                            <p className="font-medium text-gray-900">
                              {workload.recommended_provider.toUpperCase()}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Estimated Savings</p>
                            <p className="font-medium text-green-600">
                              {formatCurrency(workload.estimated_savings)}/hour
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">AWS Cost</p>
                            <p className="font-medium text-gray-900">
                              {formatCurrency(workload.aws_cost)}/hour
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Alibaba Cost</p>
                            <p className="font-medium text-gray-900">
                              {formatCurrency(workload.alibaba_cost)}/hour
                            </p>
                          </div>
                        </div>
                        
                        <div className="mb-4">
                          <p className="text-sm text-gray-600">Reason</p>
                          <p className="text-gray-900">{workload.reason}</p>
                        </div>
                        
                        <div className="flex items-center text-sm text-gray-500">
                          <Clock className="w-4 h-4 mr-1" />
                          Requested at {formatTime(workload.timestamp)}
                        </div>
                      </div>
                      
                      <div className="ml-6 flex space-x-3">
                        <button
                          onClick={() => approveWorkload(workload.workload_id)}
                          disabled={loading}
                          className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                        >
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Approve
                        </button>
                        <button
                          onClick={() => rejectWorkload(workload.workload_id)}
                          disabled={loading}
                          className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                        >
                          <XCircle className="w-4 h-4 mr-2" />
                          Reject
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApprovalDashboard;