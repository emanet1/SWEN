import { NextApiRequest, NextApiResponse } from 'next';

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

// Simulate telemetry data generation
function generateTelemetryData(): TelemetryData {
  const now = Date.now();
  
  // Generate realistic provider data with some randomness
  const awsData: ProviderData = {
    region: 'us-west-2',
    cost_per_hour: 0.05 + Math.random() * 0.02,
    latency_ms: 50 + Math.random() * 20,
    cpu_utilization: 0.3 + Math.random() * 0.4,
    memory_utilization: 0.4 + Math.random() * 0.4,
    available_instances: Math.floor(5 + Math.random() * 15),
    spot_available: true,
    credits_available: 500 + Math.random() * 500,
    reliability_score: 0.85 + Math.random() * 0.1,
    additional_resources: {
      s3_bucket: Math.random() > 0.5,
      lambda_function: Math.random() > 0.7,
      api_gateway: Math.random() > 0.3,
      cloudfront: Math.random() > 0.6,
      cost_per_month: 0.5 + Math.random() * 2.0
    }
  };

  const alibabaData: ProviderData = {
    region: 'us-west-1',
    cost_per_hour: 0.03 + Math.random() * 0.01,
    latency_ms: 60 + Math.random() * 25,
    cpu_utilization: 0.2 + Math.random() * 0.5,
    memory_utilization: 0.3 + Math.random() * 0.5,
    available_instances: Math.floor(8 + Math.random() * 17),
    spot_available: true,
    credits_available: 800 + Math.random() * 700,
    reliability_score: 0.8 + Math.random() * 0.15,
    additional_resources: {
      s3_bucket: Math.random() > 0.6,
      lambda_function: Math.random() > 0.8,
      api_gateway: Math.random() > 0.4,
      cloudfront: Math.random() > 0.7,
      cost_per_month: 0.3 + Math.random() * 1.5
    }
  };

  return {
    timestamp: now,
    providers: {
      aws: awsData,
      alibaba: alibabaData
    },
    total_cost: awsData.cost_per_hour + alibabaData.cost_per_hour,
    total_latency: (awsData.latency_ms + alibabaData.latency_ms) / 2,
    ai_decisions: Math.floor(Math.random() * 10),
    cost_savings: Math.random() * 0.02 // Simulated savings
  };
}

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const telemetryData = generateTelemetryData();
    
    res.status(200).json(telemetryData);
  } catch (error) {
    console.error('Error generating telemetry data:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
}
