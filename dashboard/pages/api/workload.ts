import { NextApiRequest, NextApiResponse } from 'next';

interface WorkloadData {
  id: string;
  cpu_cores: number;
  memory_gb: number;
  priority: string;
  cost_sensitivity: number;
  latency_sensitivity: number;
  estimated_duration_hours: number;
  reason: string;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const workloadData: WorkloadData = req.body;

    // Validate required fields
    const requiredFields = ['id', 'cpu_cores', 'memory_gb'];
    for (const field of requiredFields) {
      if (!workloadData[field as keyof WorkloadData]) {
        return res.status(400).json({ 
          error: `Missing required field: ${field}` 
        });
      }
    }

    // Send to AI engine
    const aiEngineUrl = process.env.AI_ENGINE_URL || 'http://localhost:8080';
    
    const response = await fetch(`${aiEngineUrl}/workload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(workloadData),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return res.status(response.status).json({ 
        error: `AI Engine error: ${errorText}` 
      });
    }

    const result = await response.json();
    
    res.status(200).json(result);
  } catch (error) {
    console.error('Error processing workload:', error);
    res.status(500).json({ 
      error: 'Internal server error' 
    });
  }
}
