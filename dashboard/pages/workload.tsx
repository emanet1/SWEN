import React, { useState } from 'react';
import Head from 'next/head';
import { 
  Plus, 
  Send, 
  Clock, 
  DollarSign, 
  Zap,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';

interface WorkloadForm {
  id: string;
  cpu_cores: number;
  memory_gb: number;
  priority: string;
  cost_sensitivity: number;
  latency_sensitivity: number;
  estimated_duration_hours: number;
  reason: string;
}

const WorkloadPage: React.FC = () => {
  const [form, setForm] = useState<WorkloadForm>({
    id: '',
    cpu_cores: 2,
    memory_gb: 4,
    priority: 'medium',
    cost_sensitivity: 0.5,
    latency_sensitivity: 0.5,
    estimated_duration_hours: 24,
    reason: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setResult(null);

    try {
      const response = await fetch('/api/workload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(form),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: 'Failed to submit workload' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof WorkloadForm, value: any) => {
    setForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const workloadTemplates = [
    {
      name: 'Web Application',
      description: 'Standard web app with moderate resources',
      values: {
        cpu_cores: 2,
        memory_gb: 4,
        priority: 'medium',
        cost_sensitivity: 0.5,
        latency_sensitivity: 0.8,
        estimated_duration_hours: 24,
        reason: 'Web application deployment'
      }
    },
    {
      name: 'Machine Learning Training',
      description: 'ML model training with high compute requirements',
      values: {
        cpu_cores: 8,
        memory_gb: 32,
        priority: 'high',
        cost_sensitivity: 0.8,
        latency_sensitivity: 0.2,
        estimated_duration_hours: 48,
        reason: 'ML model training job'
      }
    },
    {
      name: 'Batch Processing',
      description: 'Data processing job with cost optimization',
      values: {
        cpu_cores: 4,
        memory_gb: 16,
        priority: 'low',
        cost_sensitivity: 0.9,
        latency_sensitivity: 0.1,
        estimated_duration_hours: 12,
        reason: 'Batch data processing'
      }
    },
    {
      name: 'High Performance Computing',
      description: 'HPC workload with maximum performance',
      values: {
        cpu_cores: 16,
        memory_gb: 64,
        priority: 'high',
        cost_sensitivity: 0.3,
        latency_sensitivity: 0.9,
        estimated_duration_hours: 6,
        reason: 'High performance computing task'
      }
    }
  ];

  const applyTemplate = (template: any) => {
    setForm(prev => ({
      ...prev,
      ...template.values,
      id: `workload-${Date.now()}`
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>SWEN AI - Workload Management</title>
      </Head>

      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center mb-6">
            <Plus className="h-8 w-8 text-blue-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900">Create New Workload</h1>
          </div>

          {/* Workload Templates */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Templates</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {workloadTemplates.map((template, index) => (
                <div
                  key={index}
                  className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 cursor-pointer transition-colors"
                  onClick={() => applyTemplate(template)}
                >
                  <h3 className="font-semibold text-gray-900">{template.name}</h3>
                  <p className="text-sm text-gray-600 mb-2">{template.description}</p>
                  <div className="text-xs text-gray-500">
                    {template.values.cpu_cores} CPU cores, {template.values.memory_gb}GB RAM
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Workload Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Workload ID
                  </label>
                  <input
                    type="text"
                    value={form.id}
                    onChange={(e) => handleInputChange('id', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="workload-001"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    CPU Cores
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="32"
                    value={form.cpu_cores}
                    onChange={(e) => handleInputChange('cpu_cores', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Memory (GB)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="128"
                    value={form.memory_gb}
                    onChange={(e) => handleInputChange('memory_gb', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priority
                  </label>
                  <select
                    value={form.priority}
                    onChange={(e) => handleInputChange('priority', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
              </div>

              {/* Advanced Settings */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">Advanced Settings</h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Cost Sensitivity: {form.cost_sensitivity}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={form.cost_sensitivity}
                    onChange={(e) => handleInputChange('cost_sensitivity', parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Performance</span>
                    <span>Cost</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Latency Sensitivity: {form.latency_sensitivity}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={form.latency_sensitivity}
                    onChange={(e) => handleInputChange('latency_sensitivity', parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Flexible</span>
                    <span>Critical</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Duration (hours)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="168"
                    value={form.estimated_duration_hours}
                    onChange={(e) => handleInputChange('estimated_duration_hours', parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reason
                  </label>
                  <textarea
                    value={form.reason}
                    onChange={(e) => handleInputChange('reason', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="Why do you need these resources?"
                  />
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <Clock className="h-5 w-5 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send className="h-5 w-5 mr-2" />
                    Submit Workload
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Result */}
          {result && (
            <div className="mt-6 p-4 rounded-md bg-gray-50">
              {result.error ? (
                <div className="flex items-center text-red-600">
                  <AlertTriangle className="h-5 w-5 mr-2" />
                  <span>{result.error}</span>
                </div>
              ) : (
                <div className="flex items-center text-green-600">
                  <CheckCircle className="h-5 w-5 mr-2" />
                  <span>Workload submitted successfully!</span>
                </div>
              )}
              {result.workload_id && (
                <div className="mt-2 text-sm text-gray-600">
                  Workload ID: {result.workload_id}
                </div>
              )}
              {result.approval_required && (
                <div className="mt-2 text-sm text-yellow-600">
                  ⚠️ This workload requires manual approval
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkloadPage;
