import { NextApiRequest, NextApiResponse } from 'next';

interface HealthStatus {
  status: string;
  timestamp: string;
  services: {
    ai_engine: ServiceStatus;
    telemetry: ServiceStatus;
    gitops: ServiceStatus;
    monitoring: ServiceStatus;
  };
  metrics: {
    uptime_seconds: number;
    total_requests: number;
    error_rate: number;
    avg_response_time_ms: number;
  };
}

interface ServiceStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  last_check: string;
  response_time_ms: number;
  details?: string;
}

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const healthStatus: HealthStatus = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        ai_engine: {
          status: 'healthy',
          last_check: new Date().toISOString(),
          response_time_ms: Math.floor(Math.random() * 50) + 10
        },
        telemetry: {
          status: 'healthy',
          last_check: new Date().toISOString(),
          response_time_ms: Math.floor(Math.random() * 30) + 5
        },
        gitops: {
          status: 'healthy',
          last_check: new Date().toISOString(),
          response_time_ms: Math.floor(Math.random() * 100) + 20
        },
        monitoring: {
          status: 'healthy',
          last_check: new Date().toISOString(),
          response_time_ms: Math.floor(Math.random() * 40) + 15
        }
      },
      metrics: {
        uptime_seconds: Math.floor(Math.random() * 86400) + 3600, // 1-25 hours
        total_requests: Math.floor(Math.random() * 10000) + 1000,
        error_rate: Math.random() * 0.05, // 0-5%
        avg_response_time_ms: Math.floor(Math.random() * 200) + 50
      }
    };

    // Simulate occasional degraded service
    if (Math.random() < 0.1) {
      const degradedService = Object.keys(healthStatus.services)[
        Math.floor(Math.random() * Object.keys(healthStatus.services).length)
      ];
      healthStatus.services[degradedService as keyof typeof healthStatus.services].status = 'degraded';
      healthStatus.services[degradedService as keyof typeof healthStatus.services].details = 'High latency detected';
    }

    // Determine overall status
    const serviceStatuses = Object.values(healthStatus.services).map(s => s.status);
    if (serviceStatuses.includes('unhealthy')) {
      healthStatus.status = 'unhealthy';
    } else if (serviceStatuses.includes('degraded')) {
      healthStatus.status = 'degraded';
    }

    const statusCode = healthStatus.status === 'healthy' ? 200 : 
                      healthStatus.status === 'degraded' ? 200 : 503;

    res.status(statusCode).json(healthStatus);
  } catch (error) {
    console.error('Error generating health status:', error);
    res.status(500).json({ 
      status: 'unhealthy',
      message: 'Internal server error',
      timestamp: new Date().toISOString()
    });
  }
}
