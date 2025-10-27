import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { 
  Activity, 
  DollarSign, 
  Globe, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Server,
  Zap
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

interface TelemetryData {
  timestamp: number;
  providers: {
    aws: ProviderData;
    alibaba: ProviderData;
  };
  total_cost: number;
  total_latency: number;
  ai_decisions: number;
  cost_savings: number;
}

interface ProviderData {
  region: string;
  cost_per_hour: number;
  latency_ms: number;
  cpu_utilization: number;
  memory_utilization: number;
  available_instances: number;
  spot_available: boolean;
  credits_available: number;
  reliability_score: number;
  additional_resources?: {
    s3_bucket?: boolean;
    lambda_function?: boolean;
    api_gateway?: boolean;
    cloudfront?: boolean;
    cost_per_month?: number;
  };
}

interface AIDecision {
  timestamp: string;
  workload_id: string;
  selected_provider: string;
  confidence_score: number;
  reasoning: string;
  cost_impact: number;
}

const Dashboard: React.FC = () => {
  const [telemetryData, setTelemetryData] = useState<TelemetryData | null>(null);
  const [aiDecisions, setAiDecisions] = useState<AIDecision[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    // Check AI engine health
    const checkAIEngine = async () => {
      try {
        const response = await fetch('http://localhost:8080/health');
        if (response.ok) {
          console.log('✅ Connected to AI engine');
          setIsConnected(true);
          setLastUpdate(new Date());
        } else {
          console.log('❌ AI engine not responding');
          setIsConnected(false);
        }
      } catch (error) {
        console.log('Disconnected from AI engine');
        setIsConnected(false);
      }
    };

    // Check connection immediately
    checkAIEngine();

    // Fetch initial data
    fetchInitialData();

    // Set up polling for real-time updates
    const interval = setInterval(() => {
      fetchInitialData();
      checkAIEngine();
    }, 5000); // Update every 5 seconds

    return () => {
      clearInterval(interval);
    };
  }, []);

  const fetchInitialData = async () => {
    try {
      // Fetch real telemetry data from AI engine
      const response = await fetch('http://localhost:8080/telemetry');
      if (response.ok) {
        const data = await response.json();
        setTelemetryData(data);
        setLastUpdate(new Date());
        console.log('📊 Real AI telemetry data updated:', data);
      } else {
        console.log('AI engine telemetry not available, using mock data');
        // Fallback to mock data if AI engine telemetry not available
        const mockResponse = await fetch('/api/telemetry');
        const mockData = await mockResponse.json();
        setTelemetryData(mockData);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('Failed to fetch telemetry data:', error);
      // Fallback to mock data on error
      try {
        const mockResponse = await fetch('/api/telemetry');
        const mockData = await mockResponse.json();
        setTelemetryData(mockData);
        setLastUpdate(new Date());
      } catch (mockError) {
        console.error('Failed to fetch mock data:', mockError);
      }
    }
  };

  const formatCurrency = (amount: number | undefined) => `$${(amount || 0).toFixed(3)}`;
  const formatLatency = (latency: number | undefined) => `${(latency || 0).toFixed(1)}ms`;
  const formatPercentage = (value: number | undefined) => `${((value || 0) * 100).toFixed(1)}%`;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'critical': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getProviderColor = (provider: string) => {
    switch (provider) {
      case 'aws': return '#FF9900';
      case 'alibaba': return '#FF6A00';
      default: return '#6B7280';
    }
  };

  // Generate mock historical data for charts
  const generateHistoricalData = () => {
    const data = [];
    const now = new Date();
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      data.push({
        time: time.toISOString().substr(11, 5),
        aws_cost: 0.05 + Math.random() * 0.02,
        alibaba_cost: 0.03 + Math.random() * 0.01,
        total_latency: 50 + Math.random() * 20,
        ai_decisions: Math.floor(Math.random() * 5)
      });
    }
    return data;
  };

  const historicalData = generateHistoricalData();

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>SWEN Cloud Intelligence Dashboard</title>
        <meta name="description" content="Real-time telemetry and AI routing decisions for SWEN infrastructure" />
      </Head>

      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <Zap className="h-8 w-8 text-blue-600" />
                <h1 className="text-2xl font-bold text-gray-900">SWEN Cloud Intelligence</h1>
              </div>
              <div className="flex items-center space-x-2 ml-4">
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Live' : 'Disconnected'}
                </span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                Last update: {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
              </div>
              <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                AI-Powered
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <DollarSign className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Cost/Hour</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {telemetryData ? formatCurrency(telemetryData.total_cost_per_hour) : '$0.000'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Activity className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Avg Latency</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {telemetryData ? formatLatency(telemetryData.total_latency) : '0ms'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Server className="h-8 w-8 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">AI Decisions</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {telemetryData ? telemetryData.ai_decisions : 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-8 w-8 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Cost Savings</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {telemetryData ? formatCurrency(telemetryData.total_cost_per_hour * 0.3) : '$0.000'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Cost vs Latency Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Cost vs Latency (24h)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={historicalData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis yAxisId="cost" orientation="left" />
                <YAxis yAxisId="latency" orientation="right" />
                <Tooltip />
                <Line yAxisId="cost" type="monotone" dataKey="aws_cost" stroke="#FF9900" strokeWidth={2} name="AWS Cost" />
                <Line yAxisId="cost" type="monotone" dataKey="alibaba_cost" stroke="#FF6A00" strokeWidth={2} name="Alibaba Cost" />
                <Line yAxisId="latency" type="monotone" dataKey="total_latency" stroke="#3B82F6" strokeWidth={2} name="Latency (ms)" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Provider Utilization */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Provider Utilization</h3>
            {telemetryData && (
              <div className="space-y-4">
                {Object.entries(telemetryData.providers).map(([provider, data]) => (
                  <div key={provider} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <div 
                          className="w-4 h-4 rounded-full" 
                          style={{ backgroundColor: getProviderColor(provider) }}
                        />
                        <span className="font-medium capitalize">{provider}</span>
                        <span className="text-sm text-gray-500">({data.region})</span>
                      </div>
                      <span className="text-sm font-medium">
                        {formatCurrency(data.cost_per_hour)}/hr
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">CPU:</span>
                        <span className="ml-2 font-medium">{formatPercentage(data.cpu_utilization)}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Memory:</span>
                        <span className="ml-2 font-medium">{formatPercentage(data.memory_utilization)}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Instances:</span>
                        <span className="ml-2 font-medium">{data.available_instances}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Latency:</span>
                        <span className="ml-2 font-medium">{formatLatency(data.latency_ms)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* AI Decision History */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Recent AI Decisions</h3>
            <p className="text-sm text-gray-500 mt-1">Cost-optimized workload placement decisions</p>
          </div>
          <div className="divide-y">
            {aiDecisions.slice(0, 10).map((decision, index) => (
              <div key={index} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${getProviderColor(decision.selected_provider)}`} />
                    <div>
                      <span className="font-medium">Workload {decision.workload_id}</span>
                      <span className="text-sm text-gray-500 ml-2">
                        → {decision.selected_provider.toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-sm">
                      <span className="text-gray-500">Cost:</span>
                      <span className="ml-1 font-medium text-green-600">
                        ${decision.estimated_cost?.toFixed(3) || 'N/A'}/hr
                      </span>
                    </div>
                    <div className="text-sm">
                      <span className="text-gray-500">Savings:</span>
                      <span className="ml-1 font-medium text-green-600">
                        ${decision.cost_impact?.toFixed(2) || 'N/A'}/hr
                      </span>
                    </div>
                    <div className="text-sm text-gray-500">
                      {new Date(decision.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
                <div className="mt-2 text-sm text-gray-600">
                  {decision.reasoning}
                </div>
                {decision.cost_impact && decision.cost_impact > 0 && (
                  <div className="mt-2 text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
                    💰 Monthly savings: ${(decision.cost_impact * 24 * 30).toFixed(2)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
