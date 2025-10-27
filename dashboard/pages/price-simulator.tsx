import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { 
  DollarSign, 
  Cloud, 
  TrendingUp, 
  TrendingDown,
  Play,
  RotateCcw,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

interface PriceChange {
  provider: string;
  newCost: number;
  timestamp: string;
  status: 'success' | 'error' | 'pending';
}

const PriceSimulatorPage: React.FC = () => {
  const [awsCost, setAwsCost] = useState<number>(0.05);
  const [alibabaCost, setAlibabaCost] = useState<number>(0.03);
  const [priceChanges, setPriceChanges] = useState<PriceChange[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const applyPriceChange = async (provider: string, newCost: number) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8080/control/set-cost', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ provider, cost: newCost }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Add to price changes history
      const newChange: PriceChange = {
        provider,
        newCost,
        timestamp: new Date().toISOString(),
        status: 'success'
      };
      
      setPriceChanges(prev => [newChange, ...prev.slice(0, 9)]); // Keep last 10 changes
      
      // Update local state
      if (provider === 'aws') {
        setAwsCost(newCost);
      } else {
        setAlibabaCost(newCost);
      }

    } catch (e: any) {
      setError(`Failed to update ${provider} price: ${e.message}`);
      console.error("Error updating price:", e);
    } finally {
      setLoading(false);
    }
  };

  const resetPrices = () => {
    setAwsCost(0.05);
    setAlibabaCost(0.03);
    setPriceChanges([]);
    setError(null);
  };

  const simulatePriceDrop = (provider: string) => {
    const currentCost = provider === 'aws' ? awsCost : alibabaCost;
    const newCost = currentCost * 0.7; // 30% price drop
    applyPriceChange(provider, newCost);
  };

  const simulatePriceIncrease = (provider: string) => {
    const currentCost = provider === 'aws' ? awsCost : alibabaCost;
    const newCost = currentCost * 1.5; // 50% price increase
    applyPriceChange(provider, newCost);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <Head>
        <title>SWEN Price Simulator</title>
      </Head>
      
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-8 flex items-center">
          <DollarSign className="mr-3 text-green-600" size={32} /> 
          SWEN Price Simulator & Cost Control
        </h1>

        {/* Current Prices Display */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* AWS Price Card */}
          <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-orange-500">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-800 flex items-center">
                <Cloud className="mr-2 text-orange-500" size={24} /> AWS
              </h2>
              <span className="text-2xl font-bold text-orange-600">
                ${awsCost.toFixed(3)}/hour
              </span>
            </div>
            
            <div className="space-y-3">
              <div className="flex space-x-2">
                <input
                  type="number"
                  step="0.001"
                  value={awsCost}
                  onChange={(e) => setAwsCost(parseFloat(e.target.value))}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
                <button
                  onClick={() => applyPriceChange('aws', awsCost)}
                  disabled={loading}
                  className="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 disabled:opacity-50 flex items-center"
                >
                  <Play size={16} className="mr-1" />
                  Apply
                </button>
              </div>
              
              <div className="flex space-x-2">
                <button
                  onClick={() => simulatePriceDrop('aws')}
                  className="flex-1 px-3 py-2 bg-green-100 text-green-700 rounded-md hover:bg-green-200 flex items-center justify-center"
                >
                  <TrendingDown size={16} className="mr-1" />
                  -30% Drop
                </button>
                <button
                  onClick={() => simulatePriceIncrease('aws')}
                  className="flex-1 px-3 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 flex items-center justify-center"
                >
                  <TrendingUp size={16} className="mr-1" />
                  +50% Rise
                </button>
              </div>
            </div>
          </div>

          {/* Alibaba Price Card */}
          <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-blue-500">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-800 flex items-center">
                <Cloud className="mr-2 text-blue-500" size={24} /> Alibaba Cloud
              </h2>
              <span className="text-2xl font-bold text-blue-600">
                ${alibabaCost.toFixed(3)}/hour
              </span>
            </div>
            
            <div className="space-y-3">
              <div className="flex space-x-2">
                <input
                  type="number"
                  step="0.001"
                  value={alibabaCost}
                  onChange={(e) => setAlibabaCost(parseFloat(e.target.value))}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={() => applyPriceChange('alibaba', alibabaCost)}
                  disabled={loading}
                  className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 flex items-center"
                >
                  <Play size={16} className="mr-1" />
                  Apply
                </button>
              </div>
              
              <div className="flex space-x-2">
                <button
                  onClick={() => simulatePriceDrop('alibaba')}
                  className="flex-1 px-3 py-2 bg-green-100 text-green-700 rounded-md hover:bg-green-200 flex items-center justify-center"
                >
                  <TrendingDown size={16} className="mr-1" />
                  -30% Drop
                </button>
                <button
                  onClick={() => simulatePriceIncrease('alibaba')}
                  className="flex-1 px-3 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 flex items-center justify-center"
                >
                  <TrendingUp size={16} className="mr-1" />
                  +50% Rise
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Control Panel */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <RotateCcw className="mr-2" size={20} /> Control Panel
          </h3>
          
          <div className="flex space-x-4">
            <button
              onClick={resetPrices}
              className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 flex items-center"
            >
              <RotateCcw size={16} className="mr-1" />
              Reset to Default Prices
            </button>
            
            <a
              href="/approval"
              className="px-4 py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600 flex items-center"
            >
              <CheckCircle size={16} className="mr-1" />
              Go to Approval Dashboard
            </a>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 p-4 rounded-lg mb-6 flex items-center">
            <AlertCircle className="mr-2 text-red-500" size={20} />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Price Changes History */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <TrendingUp className="mr-2" size={20} /> Recent Price Changes
          </h3>
          
          {priceChanges.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No price changes yet. Use the controls above to simulate price changes.</p>
          ) : (
            <div className="space-y-2">
              {priceChanges.map((change, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                  <div className="flex items-center">
                    <Cloud className={`mr-2 ${change.provider === 'aws' ? 'text-orange-500' : 'text-blue-500'}`} size={16} />
                    <span className="font-medium">
                      {change.provider.toUpperCase()}
                    </span>
                    <span className="mx-2 text-gray-400">→</span>
                    <span className="font-bold text-green-600">
                      ${change.newCost.toFixed(3)}/hour
                    </span>
                  </div>
                  <div className="flex items-center text-sm text-gray-500">
                    <CheckCircle className="mr-1 text-green-500" size={14} />
                    {new Date(change.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-blue-50 border border-blue-200 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-800 mb-3">How to Use:</h3>
          <ol className="list-decimal list-inside space-y-2 text-blue-700">
            <li><strong>Set Custom Prices:</strong> Enter specific costs and click "Apply"</li>
            <li><strong>Simulate Drops:</strong> Use "-30% Drop" to simulate price reductions</li>
            <li><strong>Simulate Increases:</strong> Use "+50% Rise" to simulate price hikes</li>
            <li><strong>Monitor AI Response:</strong> Check the main dashboard for AI decisions</li>
            <li><strong>Approve/Reject:</strong> Go to Approval Dashboard to manage pending workloads</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default PriceSimulatorPage;
