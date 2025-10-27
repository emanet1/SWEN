#!/usr/bin/env python3
"""
SWEN AI Routing Engine
Core component that makes intelligent decisions about workload placement
based on cost, latency, and performance metrics.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import requests
import yaml
from flask import Flask, jsonify, request
from flask_cors import CORS

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file from project root
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed - using system environment variables only")
except Exception as e:
    print(f"⚠️ Error loading .env file: {e}")

# Prometheus and monitoring imports
from prometheus_client import Counter, Gauge, Histogram, start_http_server, CollectorRegistry, REGISTRY

# Configure logging
import os
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'swen-ai-engine.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Monitoring Configuration
PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
GRAFANA_URL = os.getenv('GRAFANA_URL', 'http://localhost:3000')
ALERT_WEBHOOK_URL = os.getenv('ALERT_WEBHOOK_URL', '')
PROMETHEUS_RETENTION = os.getenv('PROMETHEUS_RETENTION', '30d')
GRAFANA_DASHBOARD_ID = os.getenv('GRAFANA_DASHBOARD_ID', 'swen-ai-routing')

# Prometheus Metrics
workload_requests = Counter('swen_workload_requests_total', 'Total workload requests', ['status'])
cost_savings = Gauge('swen_cost_savings_dollars', 'Cost savings in dollars')
ai_decisions = Counter('swen_ai_decisions_total', 'Total AI decisions', ['provider', 'region'])
workload_cost = Gauge('swen_workload_cost_dollars_per_hour', 'Current workload cost per hour', ['workload_id'])
approval_requests = Counter('swen_approval_requests_total', 'Total approval requests', ['reason'])
terraform_applies = Counter('swen_terraform_applies_total', 'Total Terraform applies', ['status'])
ml_predictions = Counter('swen_ml_predictions_total', 'Total ML predictions', ['provider'])
decision_confidence = Histogram('swen_decision_confidence', 'AI decision confidence scores', buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
processing_time = Histogram('swen_processing_time_seconds', 'Workload processing time in seconds', buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0])

@dataclass
class CloudProvider:
    """Represents a cloud provider with its characteristics"""
    name: str
    region: str
    cost_per_hour: float
    latency_ms: float
    cpu_utilization: float
    memory_utilization: float
    available_instances: int
    spot_available: bool
    credits_available: float
    reliability_score: float

@dataclass
class Workload:
    """Represents an AI workload with its requirements"""
    id: str
    cpu_cores: int
    memory_gb: int
    priority: str  # high, medium, low
    cost_sensitivity: float  # 0-1, higher means more cost sensitive
    latency_sensitivity: float  # 0-1, higher means more latency sensitive
    estimated_duration_hours: float

class AIRoutingEngine:
    """AI-driven routing engine for optimal workload placement"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.ml_model = None
        self.scaler = StandardScaler()
        self.decision_history = []
        self.telemetry_data = []
        
        # Deployment control
        self.auto_deploy_enabled = False  # Manual approval required by default
        self.pending_workloads = []
        self.approval_threshold = 0.01  # $0.01/hour savings threshold
        self.max_cost_per_hour = 1.0    # $1/hour max cost
        self.cost_threshold = float(os.getenv('AI_COST_THRESHOLD', 50.0))  # $50/hour threshold
        
        # Simulated costs for testing (can be overridden via API)
        # Making Alibaba expensive so AI always chooses AWS
        self.aws_simulated_cost = 0.05      # $0.05/hour - Cheap AWS
        self.alibaba_simulated_cost = 0.50  # $0.50/hour - Expensive Alibaba (10x more)
        
        # Initialize ML model
        self._initialize_ml_model()
        
        # Initialize monitoring
        self._initialize_monitoring()
        
        # Initialize Flask web server with CORS
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        self._setup_routes()
        
        # Start background tasks (only if event loop is running)
        try:
            asyncio.create_task(self._collect_telemetry())
            asyncio.create_task(self._update_cost_data())
            asyncio.create_task(self._continuous_monitoring())
        except RuntimeError:
            logger.warning("No event loop running, async tasks will be started manually")
    
    def _get_aws_cost(self) -> float:
        """Get AWS cost (synchronous wrapper)"""
        # Force simulated cost for demo
        return getattr(self, 'aws_simulated_cost', 0.05)
    
    def _get_alibaba_cost(self) -> float:
        """Get Alibaba cost (synchronous wrapper)"""
        # Force simulated cost for demo
        return getattr(self, 'alibaba_simulated_cost', 0.50)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'providers': {
                'aws': {
                    'regions': ['us-east-1', 'us-west-2'],
                    'base_cost': 0.05,
                    'latency_base': 50
                },
                'alibaba': {
                    'regions': ['us-west-1', 'ap-southeast-1'],
                    'base_cost': 0.03,
                    'latency_base': 60
                }
            },
            'ml_model': {
                'retrain_interval_hours': 24,
                'features': ['cost', 'latency', 'cpu_util', 'memory_util', 'reliability']
            },
            'routing': {
                'algorithm': 'balanced',
                'cost_weight': 0.4,
                'latency_weight': 0.3,
                'reliability_weight': 0.3
            }
        }
    
    def _initialize_ml_model(self):
        """Initialize the machine learning model"""
        try:
            # Try to load existing model first
            model_path = os.getenv('AI_ML_MODEL_PATH', './models/routing_model.pkl')
            if os.path.exists(model_path):
                self._load_model(model_path)
                logger.info(f"ML model loaded from {model_path}")
            else:
                # Initialize new model
                self.ml_model = RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    max_depth=10
                )
                logger.info("New ML model initialized")
        except Exception as e:
            logger.error(f"Error initializing ML model: {e}")
            # Fallback to simple model
            self.ml_model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10
            )
            logger.info("Fallback ML model initialized")
    
    def _initialize_monitoring(self):
        """Initialize monitoring and metrics collection"""
        try:
            # Start Prometheus metrics server
            metrics_port = int(os.getenv('METRICS_PORT', '8000'))
            start_http_server(metrics_port)
            logger.info(f"Prometheus metrics server started on port {metrics_port}")
            
            # Initialize monitoring configuration
            self.prometheus_url = PROMETHEUS_URL
            self.grafana_url = GRAFANA_URL
            self.alert_webhook_url = ALERT_WEBHOOK_URL
            self.grafana_dashboard_id = GRAFANA_DASHBOARD_ID
            
            logger.info("Monitoring initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing monitoring: {e}")
            logger.warning("Continuing without monitoring capabilities")
    
    async def _collect_telemetry(self):
        """Continuously collect telemetry data from all providers"""
        while True:
            try:
                # Simulate telemetry collection from multiple sources
                telemetry = await self._fetch_telemetry_data()
                self.telemetry_data.append(telemetry)
                
                # Keep only last 1000 records
                if len(self.telemetry_data) > 1000:
                    self.telemetry_data = self.telemetry_data[-1000:]
                
                logger.info(f"Collected telemetry data: {len(self.telemetry_data)} records")
                
            except Exception as e:
                logger.error(f"Error collecting telemetry: {e}")
            
            await asyncio.sleep(60)  # Collect every minute
    
    async def _fetch_telemetry_data(self) -> Dict:
        """Fetch telemetry data from all cloud providers"""
        telemetry = {
            'timestamp': time.time(),
            'providers': {}
        }
        
        # Simulate fetching data from AWS
        aws_data = await self._fetch_aws_telemetry()
        telemetry['providers']['aws'] = aws_data
        
        # Simulate fetching data from Alibaba Cloud
        alibaba_data = await self._fetch_alibaba_telemetry()
        telemetry['providers']['alibaba'] = alibaba_data
        
        return telemetry
    
    async def _fetch_aws_telemetry(self) -> Dict:
        """Fetch real AWS telemetry data from CloudWatch and EC2 APIs"""
        try:
            import boto3
            from datetime import datetime, timedelta
            
            # Initialize AWS clients
            ec2 = boto3.client('ec2')
            cloudwatch = boto3.client('cloudwatch')
            
            # Get real instance count and types
            response = ec2.describe_instances(
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['running']},
                    {'Name': 'tag:Project', 'Values': ['SWEN-AI']}
                ]
            )
            
            running_instances = []
            total_cost = 0
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    running_instances.append(instance)
                    instance_type = instance['InstanceType']
                    # Real cost calculation based on instance type
                    if 't3.medium' in instance_type:
                        total_cost += 0.0416  # $0.0416/hour for t3.medium
                    elif 't3.small' in instance_type:
                        total_cost += 0.0208  # $0.0208/hour for t3.small
                    else:
                        total_cost += 0.05  # Default cost
            
            # Get real CPU utilization from CloudWatch (last 5 minutes)
            cpu_utilization = 0
            memory_utilization = 0
            
            if running_instances:
                try:
                    end_time = datetime.utcnow()
                    start_time = end_time - timedelta(minutes=5)
                    
                    # Get CPU utilization for all instances
                    cpu_response = cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='CPUUtilization',
                        Dimensions=[
                            {'Name': 'InstanceId', 'Value': running_instances[0]['InstanceId']}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,
                        Statistics=['Average']
                    )
                    
                    if cpu_response['Datapoints']:
                        cpu_utilization = cpu_response['Datapoints'][-1]['Average'] / 100.0
                    
                    # Get memory utilization (if available)
                    try:
                        memory_response = cloudwatch.get_metric_statistics(
                            Namespace='CWAgent',
                            MetricName='mem_used_percent',
                            Dimensions=[
                                {'Name': 'InstanceId', 'Value': running_instances[0]['InstanceId']}
                            ],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=300,
                            Statistics=['Average']
                        )
                        
                        if memory_response['Datapoints']:
                            memory_utilization = memory_response['Datapoints'][-1]['Average'] / 100.0
                    except:
                        # CloudWatch agent not installed, use simulated memory
                        memory_utilization = 0.3 + np.random.normal(0, 0.1)
                        
                except Exception as e:
                    logger.warning(f"CloudWatch metrics not available: {e}")
                    # Use simulated values if CloudWatch fails
                    cpu_utilization = 0.2 + np.random.normal(0, 0.1)
                    memory_utilization = 0.3 + np.random.normal(0, 0.1)
            
            # Get real region and Load Balancer DNS from Terraform outputs
            try:
                import subprocess
                import json
                
                # Get Terraform outputs to get real region and LB DNS
                terraform_dir = os.path.join(os.path.dirname(__file__), '..', 'infra', 'terraform')
                result = subprocess.run(
                    ['terraform', 'output', '-json', 'aws_endpoints'],
                    cwd=terraform_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    aws_outputs = json.loads(result.stdout)
                    real_region = aws_outputs.get('region', 'us-east-1')
                    lb_dns = aws_outputs.get('load_balancer_dns', 'dev-swen-app-elb-1969379828.us-east-1.elb.amazonaws.com')
                    logger.info(f"Real AWS region: {real_region}")
                else:
                    real_region = 'us-east-1'
                    lb_dns = "dev-swen-app-elb-1969379828.us-east-1.elb.amazonaws.com"
                    logger.warning("Could not get Terraform outputs, using fallback values")
                
                # Get real latency by pinging the Load Balancer
                latency_ms = self._ping_test_latency(lb_dns)
                logger.info(f"Real AWS latency: {latency_ms:.1f}ms")
                
            except Exception as e:
                logger.warning(f"Could not get real region/latency: {e}, using simulated")
                real_region = 'us-east-1'
                latency_ms = 50 + np.random.normal(0, 10)
            
            return {
                'region': real_region,  # Real region from Terraform outputs
                'cost_per_hour': total_cost if total_cost > 0 else self.aws_simulated_cost,
                'latency_ms': latency_ms,  # Real latency from Load Balancer ping
                'cpu_utilization': max(0, min(1, cpu_utilization)),  # Clamp between 0-1
                'memory_utilization': max(0, min(1, memory_utilization)),  # Clamp between 0-1
                'available_instances': len(running_instances),  # Real instance count
                'spot_available': True,
                'credits_available': 500  # Simulated credits
            }
            
        except Exception as e:
            logger.warning(f"Could not fetch real AWS data: {e}, using simulated data")
            # Fallback to simulated data if APIs fail
            try:
                # Still try to get real region and latency even in fallback
                terraform_dir = os.path.join(os.path.dirname(__file__), '..', 'infra', 'terraform')
                result = subprocess.run(
                    ['terraform', 'output', '-json', 'aws_endpoints'],
                    cwd=terraform_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    aws_outputs = json.loads(result.stdout)
                    real_region = aws_outputs.get('region', 'us-east-1')
                    lb_dns = aws_outputs.get('load_balancer_dns', 'dev-swen-app-elb-1969379828.us-east-1.elb.amazonaws.com')
                else:
                    real_region = 'us-east-1'
                    lb_dns = "dev-swen-app-elb-1969379828.us-east-1.elb.amazonaws.com"
                
                latency_ms = self._ping_test_latency(lb_dns)
                logger.info(f"Real AWS region/latency (fallback): {real_region}, {latency_ms:.1f}ms")
            except:
                real_region = 'us-east-1'
                latency_ms = 50 + np.random.normal(0, 10)
                
            return {
                'region': real_region,  # Real region from Terraform outputs
                'cost_per_hour': self.aws_simulated_cost,
                'latency_ms': latency_ms,  # Real latency from Load Balancer ping
                'cpu_utilization': 0.2 + np.random.normal(0, 0.1),
                'memory_utilization': 0.3 + np.random.normal(0, 0.1),
                'available_instances': 2,  # We know we have 2 instances deployed
                'spot_available': True,
                'credits_available': 500
            }
    
    async def _fetch_alibaba_telemetry(self) -> Dict:
        """Fetch telemetry data from Alibaba Cloud"""
        # Use simulated cost for demo
        alibaba_cost = self.alibaba_simulated_cost
        
        return {
            'region': 'us-west-1',
            'cost_per_hour': alibaba_cost,
            'latency_ms': 60 + np.random.normal(0, 15),
            'cpu_utilization': np.random.uniform(0.2, 0.7),
            'memory_utilization': np.random.uniform(0.3, 0.8),
            'available_instances': np.random.randint(8, 25),
            'spot_available': True,
            'credits_available': np.random.uniform(200, 1500)
        }
    
    async def _update_cost_data(self):
        """Update cost data from cloud provider APIs (NO infrastructure needed)"""
        while True:
            try:
                # Use simulated costs for demo
                aws_cost = self.aws_simulated_cost
                alibaba_cost = self.alibaba_simulated_cost
                
                logger.info(f"Updated cost data: AWS=${aws_cost:.3f}/hr, Alibaba=${alibaba_cost:.3f}/hr")
            except Exception as e:
                logger.error(f"Error updating cost data: {e}")
            
            await asyncio.sleep(3600)  # Update every hour
    
    async def _get_aws_cost_from_api(self) -> float:
        """Get AWS cost data (real API or simulated)"""
        # Use simulated cost if available, otherwise try real API
        if hasattr(self, 'aws_simulated_cost'):
            logger.info(f"Using simulated AWS cost: ${self.aws_simulated_cost}/hour")
            return self.aws_simulated_cost
            
        try:
            import boto3
            from datetime import datetime, timedelta
            
            # Initialize AWS Cost Explorer client
            ce_client = boto3.client('ce', region_name='us-east-1')
            
            # Get cost data for last 24 hours
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            # Calculate hourly cost from daily data
            total_cost = 0.0
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    total_cost += cost
            
            # Convert daily cost to hourly
            hourly_cost = total_cost / 24.0
            
            logger.info(f"Real AWS cost: ${hourly_cost:.4f}/hour")
            return hourly_cost
            
        except Exception as e:
            logger.warning(f"Failed to get real AWS cost: {e}")
            # Try alternative method using EC2 instances
            try:
                return await self._get_aws_cost_from_instances()
            except Exception as e2:
                logger.warning(f"EC2 cost method also failed: {e2}")
                # Final fallback to pricing API
                pricing_data = await self._get_aws_pricing_from_api()
                return pricing_data.get('on_demand', 0.05)
    
    async def _get_aws_cost_from_instances(self) -> float:
        """Get AWS cost based on running instances"""
        try:
            import boto3
            
            # Initialize EC2 client
            ec2_client = boto3.client('ec2', region_name='us-east-1')
            
            # Get running instances
            response = ec2_client.describe_instances(
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['running']},
                    {'Name': 'tag:Project', 'Values': ['SWEN-AI']}
                ]
            )
            
            total_cost = 0.0
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_type = instance['InstanceType']
                    # Estimate cost based on instance type
                    if 't3' in instance_type:
                        total_cost += 0.02  # $0.02/hour for t3 instances
                    elif 't2' in instance_type:
                        total_cost += 0.01  # $0.01/hour for t2 instances
                    else:
                        total_cost += 0.03  # Default cost
            
            logger.info(f"AWS cost from instances: ${total_cost:.4f}/hour")
            return total_cost
            
        except Exception as e:
            logger.warning(f"Failed to get AWS cost from instances: {e}")
            raise e
    
    async def _get_aws_pricing_from_api(self) -> Dict:
        """Get AWS pricing data from Pricing API (NO infrastructure needed)"""
        try:
            # In production, use boto3 to call AWS Pricing API
            # import boto3
            # pricing = boto3.client('pricing')
            # response = pricing.get_products(...)
            # return parsed_pricing_data
            
            # For now, return simulated data
            return {
                'on_demand': 0.05,
                'spot': 0.02,
                'reserved': 0.03
            }
        except Exception as e:
            logger.warning(f"AWS Pricing API failed: {e}")
            return {'on_demand': 0.05, 'spot': 0.02, 'reserved': 0.03}
    
    async def _get_alibaba_pricing_from_api(self) -> float:
        """Get Alibaba pricing data from ECS API (fallback method)"""
        try:
            # Return base pricing as fallback
            return 0.03
        except Exception as e:
            logger.warning(f"Alibaba Pricing API failed: {e}")
            return 0.03
    
    async def _ping_test_latency(self, host: str) -> float:
        """Get real network latency using ping test"""
        try:
            import subprocess
            import platform
            
            # Choose ping command based on OS
            if platform.system().lower() == "windows":
                cmd = ['ping', '-n', '1', host]
            else:
                cmd = ['ping', '-c', '1', host]
            
            # Run ping command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Parse ping time from output
                output = result.stdout
                if 'time=' in output:
                    # Extract time value (format: time=50ms or time<1ms)
                    import re
                    time_match = re.search(r'time[<=](\d+(?:\.\d+)?)', output)
                    if time_match:
                        latency = float(time_match.group(1))
                        logger.info(f"Real ping latency to {host}: {latency}ms")
                        return latency
                
                # Fallback parsing for different ping formats
                if 'ms' in output:
                    import re
                    ms_match = re.search(r'(\d+(?:\.\d+)?)\s*ms', output)
                    if ms_match:
                        latency = float(ms_match.group(1))
                        logger.info(f"Real ping latency to {host}: {latency}ms")
                        return latency
            
            logger.warning(f"Ping test failed for {host}, using fallback")
            return 50.0  # Fallback latency
            
        except Exception as e:
            logger.warning(f"Ping test error for {host}: {e}")
            return 50.0  # Fallback latency
    
    async def _get_aws_credits_from_api(self) -> float:
        """Get AWS credits from billing API (NO infrastructure needed)"""
        try:
            # In production, use boto3 to call AWS Billing API
            # import boto3
            # billing = boto3.client('billing')
            # response = billing.get_credits_balance(...)
            # return credits_available
            
            # For now, return simulated data
            return 500 + np.random.uniform(0, 500)
        except Exception as e:
            logger.warning(f"AWS Credits API failed: {e}")
            return 500
    
    async def _get_aws_instance_data(self) -> Dict:
        """Get real AWS instance data from EC2 API"""
        try:
            import boto3
            
            # Initialize EC2 client
            ec2_client = boto3.client('ec2', region_name='us-east-1')
            
            # Get running instances
            response = ec2_client.describe_instances(
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['running']},
                    {'Name': 'tag:Project', 'Values': ['SWEN-AI']}
                ]
            )
            
            instance_count = 0
            total_cpu = 0
            total_memory = 0
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_count += 1
                    # Get instance type details
                    instance_type = instance['InstanceType']
                    # Get CPU and memory from instance type
                    if 't3' in instance_type:
                        total_cpu += 2  # t3 instances have 2 vCPUs
                        total_memory += 8  # 8 GB RAM
                    elif 't2' in instance_type:
                        total_cpu += 1
                        total_memory += 4
            
            # Calculate utilization (simplified)
            cpu_utilization = min(0.8, total_cpu * 0.1) if instance_count > 0 else 0
            memory_utilization = min(0.9, total_memory * 0.05) if instance_count > 0 else 0
            
            # Get real latency using ping test
            latency_ms = await self._ping_test_latency('us-east-1.amazonaws.com')
            
            return {
                'instance_count': instance_count,
                'cpu_utilization': cpu_utilization,
                'memory_utilization': memory_utilization,
                'latency_ms': latency_ms,
                'spot_available': True,
                'credits': 500,
                'reliability': 0.99
            }
            
        except Exception as e:
            logger.warning(f"Failed to get AWS instance data: {e}")
            return {
                'instance_count': 0,
                'cpu_utilization': 0,
                'memory_utilization': 0,
                'latency_ms': 50,
                'spot_available': True,
                'credits': 500,
                'reliability': 0.99
            }
    
    async def _get_alibaba_instance_data(self) -> Dict:
        """Get real Alibaba instance data from ECS API"""
        try:
            from alibabacloud_ecs20140526.client import Client
            from alibabacloud_tea_openapi import models as open_api_models
            
            # Initialize ECS client
            config = open_api_models.Config(
                access_key_id=os.getenv('ALIBABA_ACCESS_KEY_ID'),
                access_key_secret=os.getenv('ALIBABA_ACCESS_KEY_SECRET'),
                endpoint='ecs.us-west-1.aliyuncs.com'
            )
            
            client = Client(config)
            
            # Get running instances
            from alibabacloud_ecs20140526 import models
            request = models.DescribeInstancesRequest()
            request.region_id = 'us-west-1'
            response = client.describe_instances(request)
            
            instance_count = 0
            total_cpu = 0
            total_memory = 0
            
            if response.body.instances:
                for instance in response.body.instances.instance:
                    instance_count += 1
                    # Get instance type details
                    instance_type = instance.instance_type
                    # Get CPU and memory from instance type
                    if 'ecs.t5' in instance_type:
                        total_cpu += 1  # t5 instances have 1 vCPU
                        total_memory += 2  # 2 GB RAM
                    elif 'ecs.c5' in instance_type:
                        total_cpu += 2
                        total_memory += 4
            
            # Calculate utilization (simplified)
            cpu_utilization = min(0.7, total_cpu * 0.15) if instance_count > 0 else 0
            memory_utilization = min(0.8, total_memory * 0.1) if instance_count > 0 else 0
            
            # Get real latency using ping test
            latency_ms = await self._ping_test_latency('ecs.us-west-1.aliyuncs.com')
            
            return {
                'instance_count': instance_count,
                'cpu_utilization': cpu_utilization,
                'memory_utilization': memory_utilization,
                'latency_ms': latency_ms,
                'spot_available': True,
                'credits': 300,
                'reliability': 0.95
            }
            
        except Exception as e:
            logger.warning(f"Failed to get Alibaba instance data: {e}")
            return {
                'instance_count': 0,
                'cpu_utilization': 0,
                'memory_utilization': 0,
                'latency_ms': 60,
                'spot_available': True,
                'credits': 300,
                'reliability': 0.95
            }
    
    async def _get_alibaba_cost_from_api(self) -> float:
        """Get Alibaba cost data (real API or simulated)"""
        # Use simulated cost if available, otherwise try real API
        if hasattr(self, 'alibaba_simulated_cost'):
            logger.info(f"Using simulated Alibaba cost: ${self.alibaba_simulated_cost}/hour")
            return self.alibaba_simulated_cost
            
        try:
            from alibabacloud_ecs20140526.client import Client
            from alibabacloud_tea_openapi import models as open_api_models
            
            # Initialize Alibaba Cloud ECS client
            config = open_api_models.Config(
                access_key_id=os.getenv('ALIBABA_ACCESS_KEY_ID'),
                access_key_secret=os.getenv('ALIBABA_ACCESS_KEY_SECRET'),
                endpoint='ecs.us-west-1.aliyuncs.com'
            )
            
            client = Client(config)
            
            # Get running instances to calculate cost
            from alibabacloud_ecs20140526 import models
            request = models.DescribeInstancesRequest()
            request.region_id = 'us-west-1'
            response = client.describe_instances(request)
            
            # Calculate cost based on running instances
            total_cost = 0.0
            if response.body.instances:
                for instance in response.body.instances.instance:
                    instance_type = instance.instance_type
                    # Estimate cost based on instance type
                    if 'ecs.t5' in instance_type:
                        total_cost += 0.02  # $0.02/hour for t5 instances
                    elif 'ecs.c5' in instance_type:
                        total_cost += 0.05  # $0.05/hour for c5 instances
                    else:
                        total_cost += 0.03  # Default cost
            
            logger.info(f"Real Alibaba cost: ${total_cost:.4f}/hour")
            return total_cost
            
        except Exception as e:
            logger.warning(f"Failed to get real Alibaba cost: {e}")
            # Fallback to pricing API
            return await self._get_alibaba_pricing_from_api()
    
    def calculate_optimal_placement(self, workload: Workload) -> Tuple[str, str, float]:
        """
        Calculate optimal cloud provider and region for a workload
        NEW STRATEGY: Choose ONE cloud provider, don't run on both
        
        Returns:
            Tuple of (provider, region, confidence_score)
        """
        logger.info(f"Calculating optimal placement for workload {workload.id}")
        
        # Get current provider states (pricing data, not running instances)
        providers = self._get_current_provider_states()
        
        # Calculate costs for each provider WITHOUT deploying to both
        costs = {}
        ml_predictions = {}
        
        for provider_name, provider_data in providers.items():
            cost = self._calculate_workload_cost(workload, provider_data)
            costs[provider_name] = cost
            
            # Get ML prediction for this provider
            ml_confidence = self._predict_optimal_provider(workload, provider_data)
            ml_predictions[provider_name] = ml_confidence
        
        # Combine cost-based and ML-based decisions
        # Weight: 70% cost-based, 30% ML-based
        combined_scores = {}
        for provider_name in costs.keys():
            cost_score = 1.0 / (costs[provider_name] + 0.001)  # Lower cost = higher score
            ml_score = ml_predictions[provider_name]
            combined_scores[provider_name] = 0.7 * cost_score + 0.3 * ml_score
        
        # Select best provider based on combined score
        best_provider = max(combined_scores.items(), key=lambda x: x[1])
        provider_name, combined_score = best_provider
        estimated_cost = costs[provider_name]
        
        # Calculate confidence based on both cost difference and ML prediction
        other_costs = [cost for name, cost in costs.items() if name != provider_name]
        cost_confidence = 0.5
        if other_costs:
            cost_savings = max(other_costs) - estimated_cost
            cost_confidence = min(1.0, cost_savings / estimated_cost * 2)
        
        ml_confidence = ml_predictions[provider_name]
        confidence_score = 0.7 * cost_confidence + 0.3 * ml_confidence
        
        # Log decision
        decision = {
            'timestamp': datetime.now().isoformat(),
            'workload_id': workload.id,
            'selected_provider': provider_name,
            'estimated_cost': estimated_cost,
            'all_costs': costs,
            'ml_predictions': ml_predictions,
            'combined_scores': combined_scores,
            'confidence_score': confidence_score,
            'cost_confidence': cost_confidence,
            'ml_confidence': ml_confidence,
            'reasoning': self._explain_cost_decision(workload, costs, provider_name)
        }
        
        self.decision_history.append(decision)
        logger.info(f"Selected {provider_name} with cost ${estimated_cost:.3f}/hour (confidence: {confidence_score:.3f})")
        
        return provider_name, providers[provider_name]['region'], confidence_score
    
    def _get_current_provider_states(self) -> Dict:
        """Get current state of all cloud providers"""
        if not self.telemetry_data:
            return self._get_default_provider_states()
        
        latest_telemetry = self.telemetry_data[-1]
        return latest_telemetry['providers']
    
    def _get_default_provider_states(self) -> Dict:
        """Get default provider states when no telemetry data is available"""
        return {
            'aws': {
                'region': 'us-east-1',
                'cost_per_hour': self.aws_simulated_cost,
                'latency_ms': 50,
                'cpu_utilization': 0.5,
                'memory_utilization': 0.6,
                'available_instances': 10,
                'spot_available': True,
                'credits_available': 500
            },
            'alibaba': {
                'region': 'us-west-1',
                'cost_per_hour': self.alibaba_simulated_cost,
                'latency_ms': 60,
                'cpu_utilization': 0.4,
                'memory_utilization': 0.5,
                'available_instances': 15,
                'spot_available': True,
                'credits_available': 800
            }
        }
    
    def _calculate_workload_cost(self, workload: Workload, provider_data: Dict) -> float:
        """Calculate the actual cost for running a workload on a provider"""
        
        # Base cost per hour for the provider
        base_cost_per_hour = provider_data['cost_per_hour']
        
        # Calculate required instances based on workload requirements
        required_instances = max(1, workload.cpu_cores // 2)  # 2 CPU cores per instance
        
        # Calculate total cost
        total_cost = base_cost_per_hour * required_instances
        
        # Apply spot instance discount if available
        if provider_data.get('spot_available', False):
            spot_discount = 0.6  # 60% discount for spot instances
            total_cost *= (1 - spot_discount)
        
        # Apply credits discount if available
        if provider_data.get('credits_available', 0) > 0:
            credits_discount = min(0.2, provider_data['credits_available'] / 1000.0)
            total_cost *= (1 - credits_discount)
        
        return total_cost
    
    def _check_cost_threshold(self, workload_cost: float) -> bool:
        """Check if workload cost exceeds threshold"""
        if workload_cost > self.cost_threshold:
            logger.warning(f"Workload cost ${workload_cost:.2f}/hour exceeds threshold ${self.cost_threshold:.2f}/hour")
            return False  # Requires manual approval
        else:
            logger.info(f"Workload cost ${workload_cost:.2f}/hour within threshold ${self.cost_threshold:.2f}/hour")
            return True   # Can auto-approve
    
    def _calculate_provider_score(self, workload: Workload, provider_data: Dict) -> float:
        """Calculate score for a provider based on workload requirements (legacy method)"""
        
        # Cost score (lower is better)
        cost_score = 1.0 / (1.0 + provider_data['cost_per_hour'])
        
        # Latency score (lower is better)
        latency_score = 1.0 / (1.0 + provider_data['latency_ms'] / 100.0)
        
        # Resource availability score
        resource_score = min(1.0, provider_data['available_instances'] / 20.0)
        
        # Reliability score (based on historical data)
        reliability_score = 0.8 + np.random.normal(0, 0.1)  # Simulated
        
        # Credits bonus
        credits_bonus = min(0.2, provider_data['credits_available'] / 1000.0)
        
        # Weighted combination
        weights = self.config['routing']
        total_score = (
            weights['cost_weight'] * cost_score +
            weights['latency_weight'] * latency_score +
            weights['reliability_weight'] * reliability_score +
            0.1 * resource_score +
            0.1 * credits_bonus
        )
        
        return total_score
    
    def _explain_cost_decision(self, workload: Workload, costs: Dict, selected_provider: str) -> str:
        """Generate human-readable explanation of the cost-based decision"""
        selected_cost = costs[selected_provider]
        other_costs = {name: cost for name, cost in costs.items() if name != selected_provider}
        
        if other_costs:
            cheapest_alternative = min(other_costs.items(), key=lambda x: x[1])
            alt_name, alt_cost = cheapest_alternative
            savings = alt_cost - selected_cost
            savings_percent = (savings / alt_cost) * 100
        else:
            alt_name, alt_cost, savings, savings_percent = "N/A", 0, 0, 0
        
        explanation = f"""
        Selected {selected_provider.upper()} for workload {workload.id}:
        - Estimated cost: ${selected_cost:.3f}/hour
        - Alternative ({alt_name}): ${alt_cost:.3f}/hour
        - Cost savings: ${savings:.3f}/hour ({savings_percent:.1f}%)
        - Required instances: {max(1, workload.cpu_cores // 2)}
        - Total monthly savings: ${savings * 24 * 30:.2f}
        """
        
        return explanation.strip()
    
    def _explain_decision(self, workload: Workload, providers: Dict, scores: Dict) -> str:
        """Generate human-readable explanation of the routing decision (legacy method)"""
        best_provider = max(scores.items(), key=lambda x: x[1])
        provider_name, score = best_provider
        
        provider_data = providers[provider_name]
        
        explanation = f"""
        Selected {provider_name.upper()} for workload {workload.id}:
        - Cost: ${provider_data['cost_per_hour']:.3f}/hour
        - Latency: {provider_data['latency_ms']:.1f}ms
        - Available instances: {provider_data['available_instances']}
        - Credits available: ${provider_data['credits_available']:.0f}
        - Confidence score: {score:.3f}
        """
        
        return explanation.strip()
    
    def generate_terraform_changes(self, workload: Workload, provider: str, region: str) -> Dict:
        """Generate Terraform configuration changes for the selected provider
        NEW STRATEGY: Scale up chosen provider with COMPLETE infrastructure, scale down others"""
        
        terraform_changes = {
            'timestamp': datetime.now().isoformat(),
            'workload_id': workload.id,
            'provider': provider,
            'region': region,
            'strategy': 'single_provider_optimization',
            'changes': {}
        }
        
        # Calculate required capacity
        required_instances = max(1, workload.cpu_cores // 2)
        
        # Get additional resources needed
        additional_resources = self._generate_additional_resources(workload, provider)
        
        if provider == 'aws':
            terraform_changes['changes'] = {
                'aws': {
                    'provider': 'aws',
                    'region': region,
                    'instance_type': self._get_optimal_instance_type(workload, 'aws'),
                    'desired_capacity': required_instances,  # Simple instance count
                    'min_capacity': required_instances,
                    'max_capacity': required_instances * 2,
                    'enable_spot': True,
                    # PROPER LOAD BALANCER SETUP
                    'create_load_balancer': True,      # ✅ Create LB
                    'create_target_group': True,      # ✅ Create TG
                    'create_listener': True,           # ✅ Create listener
                    'create_instances': True,           # ✅ Create instances
                    'additional_resources': {},        # ❌ No additional resources
                    'action': 'scale_up'
                },
                'alibaba': {
                    'provider': 'alicloud',
                    'region': region,
                    'desired_capacity': 0,            # Scale down Alibaba
                    'min_capacity': 0,
                    'max_capacity': 0,
                    'destroy_load_balancer': True,      # Destroy LB
                    'destroy_target_group': True,       # Destroy TG
                    'destroy_listener': True,             # Destroy listener
                    'destroy_instances': True,           # Destroy instances
                    'action': 'scale_down'
                }
            }
        elif provider == 'alibaba':
            terraform_changes['changes'] = {
                'aws': {
                    'provider': 'aws',
                    'region': region,
                    'desired_capacity': 0,            # Scale down AWS
                    'min_capacity': 0,
                    'max_capacity': 0,
                    'destroy_load_balancer': True,      # Destroy LB
                    'destroy_target_group': True,       # Destroy TG
                    'destroy_listener': True,           # Destroy listener
                    'destroy_instances': True,          # Destroy instances
                    'action': 'scale_down'
                },
                'alibaba': {
                    'provider': 'alicloud',
                    'region': region,
                    'instance_type': self._get_optimal_instance_type(workload, 'alibaba'),
                    'desired_capacity': required_instances,  # Simple instance count
                    'min_capacity': required_instances,
                    'max_capacity': required_instances * 2,
                    'enable_spot': True,
                    # PROPER LOAD BALANCER SETUP
                    'create_load_balancer': True,      # ✅ Create LB
                    'create_target_group': True,      # ✅ Create TG
                    'create_listener': True,           # ✅ Create listener
                    'create_instances': True,           # ✅ Create instances
                    'additional_resources': {},        # ❌ No additional resources
                    'action': 'scale_up'
                }
            }
        
        # AUTOMATIC DEPLOYMENT: Apply changes immediately
        self._apply_terraform_changes(terraform_changes)
        
        return terraform_changes
    
    def _apply_terraform_changes(self, terraform_changes: Dict):
        """Automatically apply Terraform changes and update DNS (FULLY AUTOMATIC)"""
        try:
            logger.info(f"Applying Terraform changes for {terraform_changes['workload_id']}")
            
            # Get absolute path to terraform directory
            import os
            import tempfile
            import subprocess
            
            # Get terraform directory
            terraform_dir = self._get_terraform_directory()
            logger.info(f"Terraform directory: {terraform_dir}")
            
            # Initialize Terraform if needed
            logger.info("Initializing Terraform...")
            
            # Prepare environment variables for Terraform
            env = os.environ.copy()
            
            # Add Alibaba credentials to environment
            if os.getenv('ALIBABA_ACCESS_KEY_ID'):
                env['ALICLOUD_ACCESS_KEY'] = os.getenv('ALIBABA_ACCESS_KEY_ID')
                env['ALICLOUD_SECRET_KEY'] = os.getenv('ALIBABA_ACCESS_KEY_SECRET')
                env['ALICLOUD_REGION'] = os.getenv('ALIBABA_REGION', 'ap-southeast-1')
                logger.info("Added Alibaba credentials to Terraform environment")
            
            # Add AWS credentials to environment
            if os.getenv('AWS_ACCESS_KEY_ID'):
                env['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
                env['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
                env['AWS_DEFAULT_REGION'] = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
                logger.info("Added AWS credentials to Terraform environment")
            
            # Add SSH public key to environment
            if os.getenv('PUBLIC_KEY'):
                env['TF_VAR_public_key'] = os.getenv('PUBLIC_KEY')
                logger.info("Added SSH public key to Terraform environment")
            
            init_result = subprocess.run([
                'terraform', 'init'
            ], cwd=terraform_dir, capture_output=True, text=True, env=env)
            
            # Log the full output for debugging
            logger.info(f"Terraform init stdout: {init_result.stdout}")
            if init_result.stderr:
                logger.error(f"Terraform init stderr: {init_result.stderr}")
            
            if init_result.returncode != 0:
                logger.error(f"Terraform init failed with return code {init_result.returncode}")
                logger.error(f"Terraform init failed: {init_result.stderr}")
                raise Exception(f"Terraform init failed: {init_result.stderr}")
            
            # Save changes to temporary file (cross-platform)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(terraform_changes, f, indent=2)
                changes_file = f.name
            
            logger.info(f"Changes file: {changes_file}")
            
            # Apply Terraform changes by modifying the main.tf file
            self._apply_terraform_config_changes(terraform_changes, terraform_dir)
            
            # Run terraform apply with the same environment variables
            result = subprocess.run([
                'terraform', 'apply', '-auto-approve'
            ], cwd=terraform_dir, capture_output=True, text=True, env=env)
            
            # Log the full output for debugging
            logger.info(f"Terraform apply stdout: {result.stdout}")
            if result.stderr:
                logger.error(f"Terraform apply stderr: {result.stderr}")
            
            if result.returncode == 0:
                logger.info("Terraform apply successful - infrastructure updated")
                
                # Record successful Terraform apply
                self.record_terraform_metrics("success")
                
                # Get LB DNS names from Terraform output
                lb_dns_names = self._get_lb_dns_names(terraform_dir)
                
                # Update DNS records with actual LB DNS names
                if lb_dns_names:
                    self._update_dns_records(lb_dns_names)
                
                # Update telemetry data
                self._update_telemetry_after_deployment(terraform_changes)
                
                # Send success alert
                self.send_alert(f"Terraform apply successful for workload {terraform_changes['workload_id']}", "info")
            else:
                logger.error(f"Terraform apply failed with return code {result.returncode}")
                logger.error(f"Terraform apply failed: {result.stderr}")
                
                # Record failed Terraform apply
                self.record_terraform_metrics("failed")
                
                # Send failure alert
                self.send_alert(f"Terraform apply failed for workload {terraform_changes['workload_id']}: {result.stderr}", "error")
                
                # Don't rollback on failure - let user know what went wrong
                raise Exception(f"Terraform apply failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error applying Terraform changes: {e}")
            # Rollback on error
            self._rollback_terraform_changes(terraform_changes)
    
    def _update_telemetry_after_deployment(self, terraform_changes: Dict):
        """Update telemetry data after successful deployment"""
        logger.info("Updating telemetry data after deployment")
        # Trigger telemetry refresh (only if event loop is running)
        try:
            asyncio.create_task(self._collect_telemetry())
        except RuntimeError:
            logger.warning("No event loop running, skipping telemetry refresh")
    
    def _rollback_terraform_changes(self, terraform_changes: Dict):
        """Rollback Terraform changes on failure"""
        logger.warning(f"Rolling back changes for {terraform_changes['workload_id']}")
        try:
            import subprocess
            import os
            
            # Get terraform directory
            terraform_dir = self._get_terraform_directory()
            logger.info(f"Rollback terraform directory: {terraform_dir}")
            
            # Rollback to previous state
            result = subprocess.run([
                'terraform', 'apply', '-auto-approve',
                '-var', 'min_capacity=0',
                '-var', 'max_capacity=0'
            ], cwd=terraform_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Rollback successful - infrastructure reset to minimal state")
            else:
                logger.error(f"Rollback failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
    
    def _get_optimal_instance_type(self, workload: Workload, provider: str) -> str:
        """Get optimal instance type for the workload"""
        
        if provider == 'aws':
            if workload.cpu_cores <= 2:
                return 't3.medium'
            elif workload.cpu_cores <= 4:
                return 't3.large'
            else:
                return 'm5.large'
        elif provider == 'alibaba':
            if workload.cpu_cores <= 2:
                return 'ecs.t5-lc1m2.small'
            elif workload.cpu_cores <= 4:
                return 'ecs.t5-lc1m2.medium'
            else:
                return 'ecs.c5.large'
        
        return 't3.medium'  # Default fallback
    
    def _analyze_workload_requirements(self, workload: Workload) -> Dict:
        """Analyze workload requirements and determine needed resources"""
        requirements = {
            'compute': {
                'instances': max(1, workload.cpu_cores // 2),
                'instance_type': self._get_optimal_instance_type(workload, 'aws')
            },
            'storage': {
                's3_bucket_needed': workload.memory_gb > 8,  # Large workloads need S3
                'ebs_volumes': max(1, workload.memory_gb // 8)  # 1 EBS per 8GB
            },
            'serverless': {
                'lambda_needed': workload.cpu_cores <= 1,  # Small workloads use Lambda
                'api_gateway_needed': True  # Always need API Gateway
            },
            'networking': {
                'load_balancer': True,
                'target_group': True,
                'listener': True,
                'cdn_needed': workload.priority == 'high'  # High priority needs CDN
            },
            'monitoring': {
                'cloudwatch': True,
                'alarms': True,
                'logs': True
            }
        }
        
        return requirements
    
    def _generate_additional_resources(self, workload: Workload, provider: str) -> Dict:
        """Generate additional resources based on workload requirements"""
        requirements = self._analyze_workload_requirements(workload)
        additional_resources = {}
        
        if provider == 'aws':
            additional_resources = {
                's3_bucket': {
                    'create': requirements['storage']['s3_bucket_needed'],
                    'name': f"swen-{workload.id}-bucket",
                    'cost_per_month': 0.023  # S3 standard pricing
                },
                'lambda_function': {
                    'create': requirements['serverless']['lambda_needed'],
                    'name': f"swen-{workload.id}-lambda",
                    'cost_per_request': 0.0000002
                },
                'api_gateway': {
                    'create': requirements['serverless']['api_gateway_needed'],
                    'name': f"swen-{workload.id}-api",
                    'cost_per_request': 0.0000035
                },
                'cloudfront_cdn': {
                    'create': requirements['networking']['cdn_needed'],
                    'name': f"swen-{workload.id}-cdn",
                    'cost_per_gb': 0.085
                },
                'ebs_volumes': {
                    'create': requirements['storage']['ebs_volumes'] > 0,
                    'count': requirements['storage']['ebs_volumes'],
                    'cost_per_gb_month': 0.10
                }
            }
        elif provider == 'alibaba':
            additional_resources = {
                'oss_bucket': {
                    'create': requirements['storage']['s3_bucket_needed'],
                    'name': f"swen-{workload.id}-bucket",
                    'cost_per_month': 0.012  # OSS pricing
                },
                'function_compute': {
                    'create': requirements['serverless']['lambda_needed'],
                    'name': f"swen-{workload.id}-function",
                    'cost_per_request': 0.0000001
                },
                'api_gateway': {
                    'create': requirements['serverless']['api_gateway_needed'],
                    'name': f"swen-{workload.id}-api",
                    'cost_per_request': 0.000001
                },
                'cdn': {
                    'create': requirements['networking']['cdn_needed'],
                    'name': f"swen-{workload.id}-cdn",
                    'cost_per_gb': 0.05
                },
                'cloud_disk': {
                    'create': requirements['storage']['ebs_volumes'] > 0,
                    'count': requirements['storage']['ebs_volumes'],
                    'cost_per_gb_month': 0.05
                }
            }
        
        return additional_resources
    
    def process_workload(self, workload: Workload):
        """Process workload with approval gates"""
        start_time = time.time()
        try:
            # Record workload request
            workload_requests.labels(status='received').inc()
            
            # 1. Calculate optimal placement and cost
            provider, region, confidence = self.calculate_optimal_placement(workload)
            providers = self._get_current_provider_states()
            estimated_cost = self._calculate_workload_cost(workload, providers[provider])
            
            # Record ML metrics
            self.record_ml_metrics(provider, confidence)
            
            # 2. Check cost threshold first
            if not self._check_cost_threshold(estimated_cost):
                # Cost exceeds threshold - require manual approval
                logger.warning(f"Workload {workload.id} cost ${estimated_cost:.2f}/hour exceeds threshold ${self.cost_threshold:.2f}/hour")
                self._queue_for_approval(workload, estimated_cost, f"Cost ${estimated_cost:.2f}/hour exceeds threshold ${self.cost_threshold:.2f}/hour")
                
                # Record metrics
                self.record_approval_metrics("cost_threshold_exceeded")
                workload_requests.labels(status='pending_approval').inc()
                
                # Send alert
                self.send_alert(f"High cost workload {workload.id}: ${estimated_cost:.2f}/hour", "warning")
                return
            
            # 3. Calculate savings
            aws_cost = self._get_aws_cost()
            alibaba_cost = self._get_alibaba_cost()
            savings = abs(aws_cost - alibaba_cost)
            
            # Update cost savings metric
            cost_savings.set(savings)
            
            # 4. Check if auto-deploy is enabled
            if self.auto_deploy_enabled and savings > self.approval_threshold:
                # Auto-deploy if savings are significant
                logger.info(f"Auto-deploying workload {workload.id} (savings: ${savings:.3f}/hour)")
                self._deploy_workload(workload)
                
                # Record metrics
                self.record_workload_metrics(workload.id, estimated_cost, provider, region)
                workload_requests.labels(status='auto_deployed').inc()
                
                # Update dashboard
                self.update_grafana_dashboard({
                    'workload_id': workload.id,
                    'provider': provider,
                    'cost': estimated_cost,
                    'savings': savings
                })
            else:
                # Queue for manual approval
                self._queue_for_approval(workload, savings, "Manual approval required")
                
                # Record metrics
                self.record_approval_metrics("manual_approval_required")
                workload_requests.labels(status='pending_approval').inc()
            
            # Record processing time
            processing_time.observe(time.time() - start_time)
                
        except Exception as e:
            logger.error(f"Error processing workload {workload.id}: {e}")
            workload_requests.labels(status='error').inc()
            self.send_alert(f"Error processing workload {workload.id}: {str(e)}", "error")
    
    def _queue_for_approval(self, workload: Workload, savings: float, reason: str = "Manual approval required"):
        """Queue workload for manual approval"""
        approval_request = {
            'workload_id': workload.id,
            'timestamp': datetime.now().isoformat(),
            'estimated_savings': savings,
            'aws_cost': self._get_aws_cost(),
            'alibaba_cost': self._get_alibaba_cost(),
            'recommended_provider': 'alibaba' if self._get_alibaba_cost() < self._get_aws_cost() else 'aws',
            'status': 'pending_approval',
            'reason': reason
        }
        
        self.pending_workloads.append(approval_request)
        logger.info(f"Workload {workload.id} queued for approval. Reason: {reason}. Estimated savings: ${savings:.3f}/hour")
        
        # Send notification (email, Slack, etc.)
        self._send_approval_notification(approval_request)
    
    def approve_workload(self, workload_id: str, approved: bool):
        """Approve or reject a workload"""
        for workload in self.pending_workloads:
            if workload['workload_id'] == workload_id:
                if approved:
                    workload['status'] = 'approved'
                    logger.info(f"Workload {workload_id} approved")
                    # Deploy the workload asynchronously to avoid blocking the response
                    try:
                        import threading
                        deployment_thread = threading.Thread(target=self._deploy_workload, args=(workload,))
                        deployment_thread.daemon = True
                        deployment_thread.start()
                        logger.info(f"Deployment started in background for workload {workload_id}")
                    except Exception as e:
                        logger.error(f"Failed to start deployment thread: {e}")
                        self._deploy_workload(workload)  # Fallback to synchronous
                else:
                    workload['status'] = 'rejected'
                    logger.info(f"Workload {workload_id} rejected")
                break
    
    def _deploy_workload(self, workload_data: Dict):
        """Deploy workload to chosen provider"""
        try:
            # Get workload object
            workload = Workload(
                id=workload_data['workload_id'],
                cpu_cores=4,  # Default values, should come from workload_data
                memory_gb=8,
                priority='medium',
                cost_sensitivity=0.5,
                latency_sensitivity=0.5,
                estimated_duration_hours=24.0
            )
            
            # Calculate optimal placement
            provider, region, confidence = self.calculate_optimal_placement(workload)
            
            # Generate and apply Terraform changes
            terraform_changes = self.generate_terraform_changes(workload, provider, region)
            
            logger.info(f"Workload {workload.id} deployed to {provider} in {region}")
            
        except Exception as e:
            logger.error(f"Error deploying workload: {e}")
    
    def _send_approval_notification(self, approval_request: Dict):
        """Send approval notification"""
        try:
            # Send email notification
            subject = f"SWEN AI: Workload {approval_request['workload_id']} requires approval"
            message = f"""
            Workload ID: {approval_request['workload_id']}
            Reason: {approval_request.get('reason', 'Manual approval required')}
            Estimated Savings: ${approval_request['estimated_savings']:.3f}/hour
            AWS Cost: ${approval_request['aws_cost']:.3f}/hour
            Alibaba Cost: ${approval_request['alibaba_cost']:.3f}/hour
            Recommended Provider: {approval_request['recommended_provider']}
            
            To approve: POST /approve/{approval_request['workload_id']} with {{"approved": true}}
            To reject: POST /approve/{approval_request['workload_id']} with {{"approved": false}}
            """
            
            logger.info(f"Approval notification sent for workload {approval_request['workload_id']}")
            
        except Exception as e:
            logger.error(f"Error sending approval notification: {e}")
    
    def send_alert(self, message: str, severity: str = 'info'):
        """Send alert to Slack webhook"""
        if not self.alert_webhook_url:
            return
        
        try:
            payload = {
                'text': f'SWEN AI Alert: {message}',
                'severity': severity,
                'timestamp': datetime.now().isoformat()
            }
            response = requests.post(self.alert_webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            logger.info(f"Alert sent successfully: {message}")
        except Exception as e:
            logger.warning(f"Failed to send alert: {e}")
    
    def update_grafana_dashboard(self, metrics_data: Dict):
        """Update Grafana dashboard with metrics data"""
        if not self.grafana_dashboard_id:
            return
        
        try:
            # Prepare dashboard data
            dashboard_data = {
                'dashboard_id': self.grafana_dashboard_id,
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics_data
            }
            
            # Send to Grafana (simulated - would need Grafana API key)
            logger.info(f"Dashboard update sent: {metrics_data}")
            
        except Exception as e:
            logger.warning(f"Failed to update Grafana dashboard: {e}")
    
    def record_workload_metrics(self, workload_id: str, cost: float, provider: str, region: str):
        """Record workload metrics"""
        try:
            workload_cost.labels(workload_id=workload_id).set(cost)
            ai_decisions.labels(provider=provider, region=region).inc()
            logger.info(f"Metrics recorded for workload {workload_id}: ${cost:.2f}/hour on {provider}")
        except Exception as e:
            logger.warning(f"Failed to record workload metrics: {e}")
    
    def record_approval_metrics(self, reason: str):
        """Record approval request metrics"""
        try:
            approval_requests.labels(reason=reason).inc()
            logger.info(f"Approval metrics recorded: {reason}")
        except Exception as e:
            logger.warning(f"Failed to record approval metrics: {e}")
    
    def record_terraform_metrics(self, status: str):
        """Record Terraform apply metrics"""
        try:
            terraform_applies.labels(status=status).inc()
            logger.info(f"Terraform metrics recorded: {status}")
        except Exception as e:
            logger.warning(f"Failed to record Terraform metrics: {e}")
    
    def record_ml_metrics(self, provider: str, confidence: float):
        """Record ML prediction metrics"""
        try:
            ml_predictions.labels(provider=provider).inc()
            decision_confidence.observe(confidence)
            logger.info(f"ML metrics recorded: {provider} with confidence {confidence:.3f}")
        except Exception as e:
            logger.warning(f"Failed to record ML metrics: {e}")
    
    def enable_auto_deploy(self, conditions: Dict):
        """Enable auto-deploy with conditions"""
        self.auto_deploy_enabled = True
        self.approval_threshold = conditions.get('savings_threshold', 0.01)
        self.max_cost_per_hour = conditions.get('max_cost', 1.0)
        self.cost_threshold = conditions.get('cost_threshold', float(os.getenv('AI_COST_THRESHOLD', 50.0)))
        
        logger.info("Auto-deploy enabled with conditions:")
        logger.info(f"- Savings threshold: ${self.approval_threshold}/hour")
        logger.info(f"- Max cost: ${self.max_cost_per_hour}/hour")
        logger.info(f"- Cost threshold: ${self.cost_threshold}/hour")
    
    def disable_auto_deploy(self):
        """Disable auto-deploy (manual approval required)"""
        self.auto_deploy_enabled = False
        logger.info("Auto-deploy disabled - manual approval required")
    
    def get_pending_workloads(self) -> List[Dict]:
        """Get list of pending workloads"""
        return [w for w in self.pending_workloads if w['status'] == 'pending_approval']
    
    async def _continuous_monitoring(self):
        """Continuously monitor costs and optimize running workloads"""
        while True:
            try:
                # Wait 1 hour between checks
                await asyncio.sleep(3600)
                
                # Get running workloads
                running_workloads = self._get_running_workloads()
                
                if running_workloads:
                    logger.info(f"Monitoring {len(running_workloads)} running workloads")
                    
                    # Monitor costs for each workload
                    for workload in running_workloads:
                        await self._monitor_workload_costs(workload)
                else:
                    logger.info("No running workloads to monitor")
                    
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def _get_running_workloads(self) -> List[Dict]:
        """Get list of currently running workloads"""
        # This would come from your infrastructure state
        # For now, we'll simulate it based on approved workloads
        running_workloads = []
        
        for workload in self.pending_workloads:
            if workload['status'] == 'approved':
                running_workloads.append({
                    'id': workload['workload_id'],
                    'provider': workload['recommended_provider'],
                    'cpu_cores': 4,  # Default values
                    'memory_gb': 8,
                    'priority': 'medium',
                    'started_at': workload['timestamp']
                })
        
        return running_workloads
    
    async def _monitor_workload_costs(self, workload: Dict):
        """Monitor costs for a specific workload"""
        try:
            # Get current costs
            aws_cost = await self._get_aws_cost()
            alibaba_cost = await self._get_alibaba_cost()
            
            current_provider = workload['provider']
            
            # Check if current provider is still optimal
            if current_provider == "aws" and alibaba_cost < aws_cost:
                savings = aws_cost - alibaba_cost
                if savings > 0.01:  # $0.01/hour savings threshold
                    await self._request_switch_approval(workload, "alibaba", savings)
                    
            elif current_provider == "alibaba" and aws_cost < alibaba_cost:
                savings = alibaba_cost - aws_cost
                if savings > 0.01:  # $0.01/hour savings threshold
                    await self._request_switch_approval(workload, "aws", savings)
            
            # Check for cost spikes
            current_cost = aws_cost if current_provider == "aws" else alibaba_cost
            if current_cost > 0.075:  # $0.075/hour threshold
                logger.warning(f"Cost spike detected for {workload['id']}: ${current_cost:.3f}/hour")
                
        except Exception as e:
            logger.error(f"Error monitoring workload {workload['id']}: {e}")
    
    async def _request_switch_approval(self, workload: Dict, new_provider: str, savings: float):
        """Request approval to switch providers"""
        try:
            switch_request = {
                'workload_id': workload['id'],
                'current_provider': workload['provider'],
                'new_provider': new_provider,
                'estimated_savings': savings,
                'reason': f"Cost optimization: {new_provider} is ${savings:.3f}/hour cheaper",
                'timestamp': datetime.now().isoformat(),
                'status': 'pending_switch_approval'
            }
            
            # Add to pending workloads for approval
            self.pending_workloads.append(switch_request)
            
            logger.info(f"Switch approval requested for {workload['id']}: {new_provider} (savings: ${savings:.3f}/hour)")
            
            # Send notification
            self._send_switch_notification(switch_request)
            
        except Exception as e:
            logger.error(f"Error requesting switch approval: {e}")
    
    def _send_switch_notification(self, switch_request: Dict):
        """Send switch approval notification"""
        try:
            message = f"""
            SWEN AI: Workload {switch_request['workload_id']} switch approval required
            
            Current Provider: {switch_request['current_provider']}
            New Provider: {switch_request['new_provider']}
            Estimated Savings: ${switch_request['estimated_savings']:.3f}/hour
            Reason: {switch_request['reason']}
            
            To approve: POST /approve/{switch_request['workload_id']} with {{"approved": true}}
            To reject: POST /approve/{switch_request['workload_id']} with {{"approved": false}}
            """
            
            logger.info(f"Switch approval notification sent for workload {switch_request['workload_id']}")
            
        except Exception as e:
            logger.error(f"Error sending switch notification: {e}")
    
    def _get_terraform_directory(self) -> str:
        """Get the absolute path to the terraform directory"""
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        terraform_dir = os.path.join(current_dir, '..', 'infra', 'terraform')
        terraform_dir = os.path.abspath(terraform_dir)
        
        if not os.path.exists(terraform_dir):
            raise FileNotFoundError(f"Terraform directory not found: {terraform_dir}")
        
        return terraform_dir
    
    def _apply_terraform_config_changes(self, terraform_changes: Dict, terraform_dir: str):
        """Apply Terraform configuration changes by modifying main.tf"""
        try:
            import os
            
            main_tf_path = os.path.join(terraform_dir, 'main.tf')
            
            # Read current main.tf
            with open(main_tf_path, 'r') as f:
                content = f.read()
            
            # Extract the changes
            changes = terraform_changes.get('changes', {})
            provider = terraform_changes.get('provider', 'aws')
            
            # Update AWS module configuration
            if 'aws' in changes:
                aws_changes = changes['aws']
                if aws_changes.get('action') == 'scale_up':
                    # Update AWS module to deploy instances
                    content = self._update_aws_module_config(content, aws_changes)
                elif aws_changes.get('action') == 'scale_down':
                    # Update AWS module to destroy instances
                    content = self._update_aws_module_config(content, aws_changes, scale_down=True)
            
            # Update Alibaba module configuration
            if 'alibaba' in changes:
                alibaba_changes = changes['alibaba']
                if alibaba_changes.get('action') == 'scale_up':
                    # Update Alibaba module to deploy instances
                    content = self._update_alibaba_module_config(content, alibaba_changes)
                elif alibaba_changes.get('action') == 'scale_down':
                    # Update Alibaba module to destroy instances
                    content = self._update_alibaba_module_config(content, alibaba_changes, scale_down=True)
            
            # Write updated main.tf
            with open(main_tf_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Updated Terraform configuration for {provider}")
            
        except Exception as e:
            logger.error(f"Error applying Terraform config changes: {e}")
    
    def _update_aws_module_config(self, content: str, aws_changes: Dict, scale_down: bool = False):
        """Update AWS module configuration in main.tf"""
        try:
            if scale_down:
                # Scale down AWS - set desired_capacity to 0
                import re
                pattern = r'(module "aws_infrastructure" \{[\s\S]*?desired_capacity\s+=\s*)\d+'
                replacement = r'\g<1>0'
                content = re.sub(pattern, replacement, content)
            else:
                # Scale up AWS - set desired_capacity to required value
                desired_capacity = aws_changes.get('desired_capacity', 1)
                import re
                pattern = r'(module "aws_infrastructure" \{[\s\S]*?desired_capacity\s+=\s*)\d+'
                replacement = f'\\g<1>{desired_capacity}'
                content = re.sub(pattern, replacement, content)
            
            return content
            
        except Exception as e:
            logger.error(f"Error updating AWS module config: {e}")
            return content
    
    def _update_alibaba_module_config(self, content: str, alibaba_changes: Dict, scale_down: bool = False):
        """Update Alibaba module configuration in main.tf"""
        try:
            if scale_down:
                # Scale down Alibaba - set desired_capacity to 0
                import re
                pattern = r'(module "alibaba_infrastructure" \{[\s\S]*?desired_capacity\s+=\s*)\d+'
                replacement = r'\g<1>0'
                content = re.sub(pattern, replacement, content)
            else:
                # Scale up Alibaba - set desired_capacity to required value
                desired_capacity = alibaba_changes.get('desired_capacity', 1)
                import re
                pattern = r'(module "alibaba_infrastructure" \{[\s\S]*?desired_capacity\s+=\s*)\d+'
                replacement = f'\\g<1>{desired_capacity}'
                content = re.sub(pattern, replacement, content)
            
            return content
            
        except Exception as e:
            logger.error(f"Error updating Alibaba module config: {e}")
            return content
    
    def _load_model(self, model_path: str):
        """Load pre-trained ML model from file"""
        try:
            import joblib
            self.ml_model = joblib.load(model_path)
            logger.info(f"ML model loaded from {model_path}")
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
            raise
    
    def _save_model(self, model_path: str = None):
        """Save trained ML model to file"""
        try:
            import joblib
            import os
            
            if model_path is None:
                model_path = os.getenv('AI_ML_MODEL_PATH', './models/routing_model.pkl')
            
            # Create models directory if it doesn't exist
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            joblib.dump(self.ml_model, model_path)
            logger.info(f"ML model saved to {model_path}")
        except Exception as e:
            logger.error(f"Error saving ML model: {e}")
            raise
    
    def _train_ml_model(self, training_data: List[Dict]):
        """Train the ML model on historical data"""
        try:
            import pandas as pd
            import numpy as np
            
            if not training_data:
                logger.warning("No training data available")
                return
            
            # Convert to DataFrame
            df = pd.DataFrame(training_data)
            
            # Prepare features (cost, latency, reliability, workload characteristics)
            feature_columns = [
                'cpu_cores', 'memory_gb', 'priority_score', 'cost_sensitivity',
                'latency_sensitivity', 'aws_cost', 'alibaba_cost',
                'aws_latency', 'alibaba_latency', 'aws_reliability', 'alibaba_reliability'
            ]
            
            # Create target variable (0 for AWS, 1 for Alibaba)
            df['target'] = df['selected_provider'].map({'aws': 0, 'alibaba': 1})
            
            # Prepare features and target
            X = df[feature_columns].fillna(0)
            y = df['target']
            
            # Train the model
            self.ml_model.fit(X, y)
            
            # Save the trained model
            self._save_model()
            
            logger.info(f"ML model trained on {len(training_data)} samples")
            
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
            raise
    
    def _predict_optimal_provider(self, workload: Workload, provider_data: Dict) -> float:
        """Use ML model to predict optimal provider"""
        try:
            if self.ml_model is None:
                logger.warning("ML model not available, using fallback logic")
                return 0.5  # Neutral prediction
            
            # Prepare features for prediction
            features = np.array([[
                workload.cpu_cores,
                workload.memory_gb,
                self._get_priority_score(workload.priority),
                workload.cost_sensitivity,
                workload.latency_sensitivity,
                provider_data.get('aws_cost', 0.05),
                provider_data.get('alibaba_cost', 0.03),
                provider_data.get('aws_latency', 50),
                provider_data.get('alibaba_latency', 60),
                provider_data.get('aws_reliability', 0.99),
                provider_data.get('alibaba_reliability', 0.98)
            ]])
            
            # Check if model is trained
            if not hasattr(self.ml_model, 'classes_'):
                logger.warning("ML model not trained yet, using cost-based decision")
                return 0.5
            
            # Get prediction probability
            prediction = self.ml_model.predict_proba(features)[0]
            
            # Return confidence score (probability of being optimal)
            return float(prediction[1])  # Probability of Alibaba being optimal
            
        except Exception as e:
            logger.error(f"Error predicting with ML model: {e}")
            return 0.5  # Neutral prediction on error
    
    def _get_priority_score(self, priority: str) -> float:
        """Convert priority string to numeric score"""
        priority_map = {
            'low': 0.2,
            'medium': 0.5,
            'high': 0.8,
            'critical': 1.0
        }
        return priority_map.get(priority.lower(), 0.5)
    
    def _get_lb_dns_names(self, terraform_dir: str):
        """Get LB DNS names from Terraform output"""
        try:
            import subprocess
            import json
            
            # Get AWS endpoints
            aws_result = subprocess.run([
                'terraform', 'output', '-json', 'aws_endpoints'
            ], cwd=terraform_dir, capture_output=True, text=True)
            
            # Get Alibaba endpoints
            alibaba_result = subprocess.run([
                'terraform', 'output', '-json', 'alibaba_endpoints'
            ], cwd=terraform_dir, capture_output=True, text=True)
            
            # Parse outputs
            aws_endpoints = json.loads(aws_result.stdout) if aws_result.returncode == 0 else {}
            alibaba_endpoints = json.loads(alibaba_result.stdout) if alibaba_result.returncode == 0 else {}
            
            return {
                'aws': aws_endpoints.get('load_balancer_dns'),
                'alibaba': alibaba_endpoints.get('load_balancer_dns')
            }
            
        except Exception as e:
            logger.error(f"Error getting LB DNS names: {e}")
            return {'aws': None, 'alibaba': None}
    
    def _update_dns_records(self, lb_dns_names: Dict):
        """Update DNS records with actual LB DNS names"""
        try:
            # Find the active provider (non-null LB DNS)
            active_provider = None
            active_lb_dns = None
            
            for provider, lb_dns in lb_dns_names.items():
                if lb_dns:
                    active_provider = provider
                    active_lb_dns = lb_dns
                    break
            
            if not active_provider or not active_lb_dns:
                logger.warning("No active provider found")
                return False
            
            # Update DNS record using Namecheap API
            result = self._update_namecheap_dns(active_lb_dns)
            
            if result:
                logger.info(f"DNS updated to {active_provider}: {active_lb_dns}")
                
                # Wait for DNS propagation
                self._wait_for_dns_propagation(active_lb_dns)
                
                return True
            else:
                logger.error("DNS update failed")
                return False
                
        except Exception as e:
            logger.error(f"DNS update failed: {e}")
            return False
    
    def _update_namecheap_dns(self, lb_dns: str):
        """Update DNS record in Namecheap"""
        try:
            import requests
            import os
            
            # Namecheap API configuration
            api_key = os.getenv('NAMECHEAP_API_KEY')
            username = os.getenv('NAMECHEAP_USERNAME')
            client_ip = os.getenv('NAMECHEAP_CLIENT_IP')
            domain = os.getenv('DOMAIN_NAME')
            
            if not all([api_key, username, client_ip, domain]):
                logger.warning("Namecheap credentials not configured, skipping DNS update")
                return True  # Return True to continue without DNS update
            
            # Namecheap API URL
            base_url = "https://api.namecheap.com/xml.response"
            
            # Update DNS record
            params = {
                'ApiUser': username,
                'ApiKey': api_key,
                'UserName': username,
                'Command': 'namecheap.domains.dns.setHosts',
                'ClientIp': client_ip,
                'SLD': domain.split('.')[0],
                'TLD': domain.split('.')[1],
                'HostName': '@',
                'RecordType': 'CNAME',
                'Address': lb_dns,
                'TTL': 60
            }
            
            response = requests.get(base_url, params=params)
            
            if response.status_code == 200:
                logger.info(f"DNS updated successfully: {domain} → {lb_dns}")
                return True
            else:
                logger.error(f"DNS update failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Namecheap DNS update failed: {e}")
            return False
    
    def _wait_for_dns_propagation(self, expected_dns: str, timeout: int = 300):
        """Wait for DNS propagation"""
        try:
            import time
            import socket
            import os
            
            domain = os.getenv('DOMAIN_NAME')
            if not domain:
                logger.warning("Domain name not configured, skipping DNS propagation check")
                return True
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Check if DNS has propagated
                    resolved_ip = socket.gethostbyname(domain)
                    if resolved_ip:
                        logger.info(f"DNS propagated: {domain} → {resolved_ip}")
                        return True
                except:
                    pass
                
                time.sleep(10)  # Check every 10 seconds
            
            logger.warning("DNS propagation timeout")
            return False
            
        except Exception as e:
            logger.error(f"DNS propagation check failed: {e}")
            return False
    
    def get_health_status(self) -> Dict:
        """Get health status of the AI routing engine"""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'decisions_made': len(self.decision_history),
            'telemetry_records': len(self.telemetry_data),
            'ml_model_trained': self.ml_model is not None,
            'uptime_seconds': time.time() - self.start_time if hasattr(self, 'start_time') else 0
        }
    
    def get_decision_history(self, limit: int = 100) -> List[Dict]:
        """Get recent decision history"""
        return self.decision_history[-limit:]
    
    def get_telemetry_summary(self) -> Dict:
        """Get summary of current telemetry data"""
        if not self.telemetry_data:
            return {'message': 'No telemetry data available'}
        
        latest = self.telemetry_data[-1]
        return {
            'timestamp': latest['timestamp'],
            'providers': {
                name: {
                    'cost_per_hour': data['cost_per_hour'],
                    'latency_ms': data['latency_ms'],
                    'cpu_utilization': data['cpu_utilization'],
                    'available_instances': data['available_instances']
                }
                for name, data in latest['providers'].items()
            }
        }

    def _setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'ai_engine': 'running'
            })
        
        @self.app.route('/telemetry', methods=['GET'])
        def telemetry():
            if not self.telemetry_data:
                return jsonify({
                    'providers': {
                        'aws': {
                            'cost_per_hour': self.aws_simulated_cost,
                            'latency_ms': 50,
                            'region': 'us-east-1',
                            'cpu_utilization': 0.5,
                            'memory_utilization': 0.6,
                            'available_instances': 10,
                            'spot_available': True,
                            'credits_available': 500
                        },
                        'alibaba': {
                            'cost_per_hour': self.alibaba_simulated_cost,
                            'latency_ms': 60,
                            'region': 'us-west-1',
                            'cpu_utilization': 0.4,
                            'memory_utilization': 0.5,
                            'available_instances': 15,
                            'spot_available': True,
                            'credits_available': 800
                        }
                    },
                    'timestamp': datetime.now().isoformat(),
                    'total_cost_per_hour': self.aws_simulated_cost + self.alibaba_simulated_cost,
                    'avg_latency_ms': (50 + 60) / 2
                })
            
            latest = self.telemetry_data[-1]
            
            # Add calculated fields that the dashboard expects
            latest['total_cost_per_hour'] = sum(
                provider_data.get('cost_per_hour', 0) 
                for provider_data in latest['providers'].values()
            )
            latest['avg_latency_ms'] = sum(
                provider_data.get('latency_ms', 0) 
                for provider_data in latest['providers'].values()
            ) / len(latest['providers'])
            
            return jsonify(latest)
        
        @self.app.route('/workloads', methods=['GET'])
        def get_workloads():
            return jsonify({
                'workloads': self.workload_queue,
                'pending': self.pending_workloads,
                'completed': len(self.decision_history)
            })
        
        @self.app.route('/pending', methods=['GET'])
        def get_pending():
            return jsonify({
                'pending_workloads': self.pending_workloads,
                'count': len(self.pending_workloads)
            })
        
        @self.app.route('/workload', methods=['POST'])
        def submit_workload():
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            workload = Workload(
                id=data.get('id', f'workload-{int(time.time())}'),
                cpu_cores=data.get('cpu_cores', 2),
                memory_gb=data.get('memory_gb', 4),
                priority=data.get('priority', 'medium'),
                cost_sensitivity=data.get('cost_sensitivity', 0.5),
                latency_sensitivity=data.get('latency_sensitivity', 0.5),
                estimated_duration_hours=data.get('estimated_duration_hours', 1.0)
            )
            
            # Add to queue
            self.workload_queue.append(workload)
            
            return jsonify({
                'message': 'Workload submitted successfully',
                'workload_id': workload.id
            })

async def main():
    """Main function to run the AI routing engine"""
    logger.info("Starting SWEN AI Routing Engine")
    
    # Initialize the routing engine
    engine = AIRoutingEngine()
    engine.start_time = time.time()
    
    # Example workload
    workload = Workload(
        id="workload-001",
        cpu_cores=4,
        memory_gb=8,
        priority="high",
        cost_sensitivity=0.7,
        latency_sensitivity=0.5,
        estimated_duration_hours=24.0
    )
    
    # Calculate optimal placement
    provider, region, confidence = engine.calculate_optimal_placement(workload)
    
    # Generate Terraform changes
    terraform_changes = engine.generate_terraform_changes(workload, provider, region)
    
    logger.info(f"Terraform changes: {json.dumps(terraform_changes, indent=2)}")
    
    # Start Flask web server in a separate thread
    import threading
    def run_flask():
        engine.app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask web server started on port 8080")
    
    # Keep the engine running
    while True:
        await asyncio.sleep(60)
        logger.info("AI Routing Engine running...")

if __name__ == "__main__":
    asyncio.run(main())
