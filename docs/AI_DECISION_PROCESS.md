# SWEN AI Decision Process & Approval Workflow

## Overview

This document explains how the SWEN AI Engine makes decisions about workload placement, the approval process, and the complete workflow from workload arrival to infrastructure deployment.

## 🎯 AI Decision Process

### Step 1: Workload Arrival

When a workload arrives (via webhook, UI, or simulated app), the AI engine receives a `Workload` object:

```python
workload = Workload(
    id="workload-123",
    cpu_cores=4,
    memory_gb=8,
    priority="high",                    # high, medium, low, critical
    cost_sensitivity=0.8,              # 0-1, higher = more cost sensitive
    latency_sensitivity=0.3,            # 0-1, higher = more latency sensitive
    estimated_duration_hours=24.0
)
```

#### **💰 Cost Sensitivity (0-1 scale)**

**What it means:** How much the workload cares about cost vs other factors.

##### **Examples:**

**Cost Sensitivity = 0.8 (High Cost Sensitivity)**
```python
workload = Workload(
    cpu_cores=4,
    memory_gb=8,
    cost_sensitivity=0.8,  # Very cost-sensitive
    latency_sensitivity=0.3
)

# What this means:
# "This workload REALLY cares about cost"
# "Save money is more important than performance"
# "Choose the cheapest option, even if it's slower"
```

**Cost Sensitivity = 0.2 (Low Cost Sensitivity)**
```python
workload = Workload(
    cpu_cores=4,
    memory_gb=8,
    cost_sensitivity=0.2,  # Not very cost-sensitive
    latency_sensitivity=0.8
)

# What this means:
# "This workload doesn't care much about cost"
# "Performance is more important than saving money"
# "Choose the best option, even if it's expensive"
```

#### **⚡ Latency Sensitivity (0-1 scale)**

**What it means:** How much the workload cares about speed/response time.

##### **Examples:**

**Latency Sensitivity = 0.9 (High Latency Sensitivity)**
```python
workload = Workload(
    cpu_cores=4,
    memory_gb=8,
    cost_sensitivity=0.3,
    latency_sensitivity=0.9  # Very latency-sensitive
)

# What this means:
# "This workload REALLY needs to be fast"
# "Speed is more important than cost"
# "Choose the fastest option, even if it's expensive"
```

**Latency Sensitivity = 0.1 (Low Latency Sensitivity)**
```python
workload = Workload(
    cpu_cores=4,
    memory_gb=8,
    cost_sensitivity=0.8,
    latency_sensitivity=0.1  # Not very latency-sensitive
)

# What this means:
# "This workload doesn't care much about speed"
# "Cost is more important than speed"
# "Choose the cheapest option, even if it's slower"
```

#### **🎯 Real-World Examples**

##### **Example 1: Cost-Sensitive Workload**
```python
# Batch processing job (runs overnight)
workload = Workload(
    cpu_cores=8,
    memory_gb=16,
    cost_sensitivity=0.9,    # Very cost-sensitive
    latency_sensitivity=0.1   # Not latency-sensitive
)

# AI Decision Logic:
# "This job runs overnight, so speed doesn't matter"
# "But cost matters a lot - we want to save money"
# "Choose Alibaba even if it's slower, because it's cheaper"
```

##### **Example 2: Latency-Sensitive Workload**
```python
# Real-time trading system
workload = Workload(
    cpu_cores=4,
    memory_gb=8,
    cost_sensitivity=0.2,    # Not very cost-sensitive
    latency_sensitivity=0.9  # Very latency-sensitive
)

# AI Decision Logic:
# "This needs to be FAST - every millisecond counts"
# "Cost doesn't matter as much as speed"
# "Choose AWS even if it's more expensive, because it's faster"
```

##### **Example 3: Balanced Workload**
```python
# Standard web application
workload = Workload(
    cpu_cores=2,
    memory_gb=4,
    cost_sensitivity=0.5,    # Moderately cost-sensitive
    latency_sensitivity=0.5  # Moderately latency-sensitive
)

# AI Decision Logic:
# "This needs to be reasonably fast and reasonably cheap"
# "Balance both factors"
# "Choose based on overall best value"
```

#### **📊 Sensitivity Scale Examples**

| Sensitivity | Meaning | Example Workload |
|-------------|---------|------------------|
| **0.0-0.2** | Not sensitive | Batch processing, data backup |
| **0.3-0.5** | Moderately sensitive | Standard web apps, APIs |
| **0.6-0.8** | Very sensitive | Real-time systems, gaming |
| **0.9-1.0** | Extremely sensitive | Trading systems, critical operations |

#### **🧠 How the AI Uses These Values**

##### **Decision Weighting:**
```python
# AI combines cost and latency sensitivity
if workload.cost_sensitivity > 0.7:
    # Cost is very important
    cost_weight = 0.8
    latency_weight = 0.2
elif workload.latency_sensitivity > 0.7:
    # Latency is very important
    cost_weight = 0.2
    latency_weight = 0.8
else:
    # Balanced approach
    cost_weight = 0.5
    latency_weight = 0.5
```

##### **Provider Selection Logic:**
```python
# Example: Cost-sensitive workload
if workload.cost_sensitivity > 0.8:
    # Prioritize cost over everything else
    if aws_cost < alibaba_cost:
        return "aws"
    else:
        return "alibaba"
        
# Example: Latency-sensitive workload  
elif workload.latency_sensitivity > 0.8:
    # Prioritize speed over everything else
    if aws_latency < alibaba_latency:
        return "aws"
    else:
        return "alibaba"
```

#### **🎯 How It Affects AI Decisions**

##### **Cost-Sensitive Workload (cost_sensitivity=0.8):**
```
AWS: $0.10/hour, 50ms latency
Alibaba: $0.06/hour, 80ms latency

AI Decision: "Cost is 80% important, latency is 20% important"
Result: Choose Alibaba (40% cheaper, but 60% slower)
Reasoning: "Saving $0.04/hour is more important than 30ms faster response"
```

##### **Latency-Sensitive Workload (latency_sensitivity=0.8):**
```
AWS: $0.10/hour, 50ms latency  
Alibaba: $0.06/hour, 80ms latency

AI Decision: "Latency is 80% important, cost is 20% important"
Result: Choose AWS (60% faster, but 67% more expensive)
Reasoning: "30ms faster response is more important than $0.04/hour cost"
```

### Step 2: Real Data Collection (Infrastructure Required)

The AI collects **real-time data** from deployed infrastructure and cloud APIs:

```python
# Real AWS data from deployed infrastructure
aws_data = {
    'region': 'us-east-1',                    # Real region from Terraform outputs
    'cost_per_hour': 0.083,                   # Real cost: 2x t3.medium instances
    'latency_ms': 176.0,                      # Real latency from Load Balancer ping
    'cpu_utilization': 0.25,                  # Real CPU from CloudWatch metrics
    'memory_utilization': 0.35,               # Real memory from CloudWatch metrics
    'available_instances': 2,                 # Real instance count from EC2 API
    'spot_available': True,
    'credits_available': 500
}

# Simulated Alibaba data (disabled due to risk control)
alibaba_data = {
    'region': 'us-west-1',                    # Simulated region
    'cost_per_hour': 0.50,                    # Simulated cost (made expensive for demo)
    'latency_ms': 60.0,                       # Simulated latency
    'cpu_utilization': 0.30,                  # Simulated CPU
    'memory_utilization': 0.55,               # Simulated memory
    'available_instances': 16,                # Simulated instances
    'spot_available': True,
    'credits_available': 800
}
```

#### **🔍 Real Data Sources**

**AWS Data Collection:**
```python
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
        
        # Get real latency by pinging the Load Balancer
        try:
            # Get Load Balancer DNS from Terraform outputs
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
        return {
            'region': 'us-east-1',
            'cost_per_hour': self.aws_simulated_cost,
            'latency_ms': 50 + np.random.normal(0, 10),
            'cpu_utilization': 0.2 + np.random.normal(0, 0.1),
            'memory_utilization': 0.3 + np.random.normal(0, 0.1),
            'available_instances': 2,  # We know we have 2 instances deployed
            'spot_available': True,
            'credits_available': 500
        }
```

**Real Latency Measurement:**
```python
def _ping_test_latency(self, host: str) -> float:
    """Get real network latency using ping test"""
    try:
        import subprocess
        import platform
        
        # Determine ping command based on OS
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "4", host]
        else:
            cmd = ["ping", "-c", "4", host]
        
        # Execute ping command
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Parse ping output for average latency
            output = result.stdout
            if "Average" in output:
                # Windows format: "Average = 176ms"
                avg_line = [line for line in output.split('\n') if 'Average' in line][0]
                latency_str = avg_line.split('=')[1].strip().replace('ms', '')
                return float(latency_str)
            elif "avg" in output:
                # Linux format: "rtt min/avg/max/mdev = 175.123/176.456/178.789/1.234 ms"
                avg_line = [line for line in output.split('\n') if 'rtt' in line][0]
                latency_str = avg_line.split('/')[1]
                return float(latency_str)
        
        # Fallback to simulated latency
        return 50 + np.random.normal(0, 10)
        
    except Exception as e:
        logger.warning(f"Ping test failed: {e}")
        return 50 + np.random.normal(0, 10)
```

### Step 3: Cost Calculation

The AI calculates the actual cost for running the workload on each provider:

```python
def _calculate_workload_cost(workload, provider_data):
    # Base cost per hour
    base_cost = provider_data['cost_per_hour']
    
    # Calculate required instances
    required_instances = max(1, workload.cpu_cores // 2)
    
    # Calculate total cost
    total_cost = base_cost * required_instances
    
    # Apply spot instance discount (60% off)
    if provider_data['spot_available']:
        total_cost *= 0.4
    
    # Apply credits discount
    if provider_data['credits_available'] > 0:
        credits_discount = min(0.2, provider_data['credits_available'] / 1000.0)
        total_cost *= (1 - credits_discount)
    
    return total_cost

# Example results:
# AWS: 0.05 * 2 instances * 0.4 (spot) * 0.8 (credits) = 0.032/hour
# Alibaba: 0.03 * 2 instances * 0.4 (spot) * 0.8 (credits) = 0.019/hour
```

### Step 4: ML Model Prediction

The AI uses a machine learning model to predict the optimal provider:

```python
def _predict_optimal_provider(workload, provider_data):
    # Features: workload characteristics + provider data
    features = [
        workload.cpu_cores,                    # 4
        workload.memory_gb,                    # 8
        workload.priority_score,               # 0.8 (high priority)
        provider_data['cost_per_hour'],       # 0.05
        provider_data['latency_ms'],          # 50
        provider_data['reliability_score']    # 0.95
    ]
    
    # ML model predicts confidence (0-1)
    ml_confidence = self.ml_model.predict_proba([features])[0][1]
    
    return ml_confidence

# Example results:
# AWS ML confidence: 0.3 (30% likely to be optimal)
# Alibaba ML confidence: 0.8 (80% likely to be optimal)
```

### Step 5: ML Model Training & Prediction

#### **🧠 How ML Model Learns from Historical Data**

The ML model uses a **RandomForestClassifier** that learns from historical decision patterns:

```python
def _train_ml_model(self):
    """Train ML model on historical decision data"""
    if len(self.decision_history) < 10:
        return  # Need at least 10 decisions to train
    
    # Prepare training features
    features = []
    targets = []
    
    for decision in self.decision_history:
        # Feature vector: [workload_cpu, workload_memory, workload_priority, 
        #                  aws_cost, alibaba_cost, aws_latency, alibaba_latency,
        #                  aws_reliability, alibaba_reliability, time_of_day]
        features.append([
            decision['workload_cpu_cores'],
            decision['workload_memory_gb'],
            decision['workload_priority_score'],
            decision['aws_cost'],
            decision['alibaba_cost'],
            decision['aws_latency'],
            decision['alibaba_latency'],
            decision['aws_reliability'],
            decision['alibaba_reliability'],
            decision['hour_of_day']
        ])
        # Target: 0 for AWS, 1 for Alibaba
        targets.append(1 if decision['selected_provider'] == 'alibaba' else 0)
    
    # Train RandomForest model
    self.ml_model.fit(features, targets)
    self._save_model()
```

#### **🎯 ML Prediction Mechanism**

The ML model predicts the **probability** that Alibaba is optimal:

```python
def _predict_optimal_provider(self, workload, provider_data):
    """Get ML prediction for provider optimality"""
    
    # Prepare feature vector for prediction
    features = [
        workload.cpu_cores,                    # 4
        workload.memory_gb,                    # 8
        self._get_priority_score(workload.priority),  # 0.8 (high priority)
        provider_data['cost_per_hour'],       # 0.05
        provider_data['latency_ms'],          # 50
        provider_data['reliability_score'],   # 0.95
        datetime.now().hour                   # 14 (2 PM)
    ]
    
    # Get prediction probability
    # predict_proba returns [prob_aws, prob_alibaba]
    probabilities = self.ml_model.predict_proba([features])[0]
    alibaba_probability = probabilities[1]  # 0.8 = 80% chance Alibaba is optimal
    
    return alibaba_probability
```

#### **📊 ML Model Features & Learning**

The ML model learns from these **10 key features**:

| Feature | Description | Impact on Decision |
|---------|-------------|-------------------|
| **CPU Cores** | Workload CPU requirements | High CPU → AWS (better performance) |
| **Memory GB** | Workload memory requirements | High memory → Alibaba (cheaper) |
| **Priority** | Workload priority level | Critical → AWS (higher reliability) |
| **AWS Cost** | Current AWS pricing | Lower cost → Higher AWS probability |
| **Alibaba Cost** | Current Alibaba pricing | Lower cost → Higher Alibaba probability |
| **AWS Latency** | AWS network latency | Lower latency → Higher AWS probability |
| **Alibaba Latency** | Alibaba network latency | Lower latency → Higher Alibaba probability |
| **AWS Reliability** | Historical AWS uptime | Higher reliability → Higher AWS probability |
| **Alibaba Reliability** | Historical Alibaba uptime | Higher reliability → Higher Alibaba probability |
| **Time of Day** | Hour of the day | Peak hours → Different patterns |

#### **🎯 ML Confidence Scoring**

The ML model provides **confidence scores** (0-1) for each provider:

```python
# Example ML predictions:
aws_ml_confidence = 0.3    # 30% chance AWS is optimal
alibaba_ml_confidence = 0.8  # 80% chance Alibaba is optimal

# ML confidence is based on:
# 1. Historical success patterns
# 2. Workload similarity to past successful deployments
# 3. Time-based patterns (peak hours, maintenance windows)
# 4. Provider performance history
# 5. Workload characteristics matching
```

### Step 6: Combined Decision (70% Cost + 30% ML)

The AI combines cost-based and ML-based decisions with weighted scoring:

```python
def calculate_optimal_placement(workload):
    # Cost scores (lower cost = higher score)
    aws_cost_score = 1.0 / (aws_final_cost + 0.001)      # 1.0 / 0.032 = 31.25
    alibaba_cost_score = 1.0 / (alibaba_final_cost + 0.001)  # 1.0 / 0.019 = 52.63
    
    # ML confidence scores (0-1)
    aws_ml_confidence = 0.3    # 30% chance AWS is optimal
    alibaba_ml_confidence = 0.8  # 80% chance Alibaba is optimal
    
    # Combined scores (70% cost + 30% ML)
    aws_combined = 0.7 * aws_cost_score + 0.3 * aws_ml_confidence
    alibaba_combined = 0.7 * alibaba_cost_score + 0.3 * alibaba_ml_confidence
    
    # Calculate final scores:
    # AWS: 0.7 * 31.25 + 0.3 * 0.3 = 21.875 + 0.09 = 21.965
    # Alibaba: 0.7 * 52.63 + 0.3 * 0.8 = 36.841 + 0.24 = 37.081
    
    # Alibaba wins! (higher score)
    return "alibaba", "us-west-1", 0.85  # 85% confidence
```

### Step 7: Decision Override Scenarios

#### **🚨 When ML Can Override Cost Decisions**

The ML model can override cost-based decisions in these scenarios:

##### **1. Reliability Override**
```python
# Scenario: AWS is 20% cheaper but has 95% reliability vs Alibaba 99%
if aws_reliability < 0.95 and workload.priority == "critical":
    # ML overrides cost decision for critical workloads
    ml_confidence_boost = 0.4  # +40% ML confidence for Alibaba
    alibaba_ml_confidence = min(1.0, alibaba_ml_confidence + ml_confidence_boost)
```

##### **2. Performance Override**
```python
# Scenario: High-performance workload needs AWS's better infrastructure
if workload.cpu_cores > 8 and workload.memory_gb > 16:
    # ML recognizes high-performance pattern
    if historical_aws_performance > historical_alibaba_performance:
        aws_ml_confidence += 0.3  # Boost AWS confidence
```

##### **3. Time-Based Override**
```python
# Scenario: Peak hours favor different providers
current_hour = datetime.now().hour
if 9 <= current_hour <= 17:  # Business hours
    # Historical data shows AWS performs better during business hours
    aws_ml_confidence += 0.2
elif 18 <= current_hour <= 23:  # Evening hours
    # Alibaba performs better during evening hours
    alibaba_ml_confidence += 0.2
```

##### **4. Latency Override**
```python
# Scenario: Latency-sensitive workload
if workload.latency_sensitivity > 0.8:
    if aws_latency < alibaba_latency:
        # AWS has better latency
        aws_ml_confidence += 0.4
    else:
        # Alibaba has better latency
        alibaba_ml_confidence += 0.4
```

##### **5. Historical Success Override**
```python
# Scenario: Similar workloads have succeeded on specific provider
similar_workloads = self._find_similar_workloads(workload)
if similar_workloads:
    aws_success_rate = sum(1 for w in similar_workloads if w['provider'] == 'aws' and w['success']) / len(similar_workloads)
    alibaba_success_rate = sum(1 for w in similar_workloads if w['provider'] == 'alibaba' and w['success']) / len(similar_workloads)
    
    if aws_success_rate > alibaba_success_rate + 0.2:
        aws_ml_confidence += 0.3
    elif alibaba_success_rate > aws_success_rate + 0.2:
        alibaba_ml_confidence += 0.3
```

#### **🎯 ML Override Examples**

##### **Example 1: Critical Workload Override**
```python
# Workload: Critical AI training job
workload = Workload(
    cpu_cores=16,
    memory_gb=64,
    priority="critical",
    latency_sensitivity=0.9
)

# Cost analysis: Alibaba is 30% cheaper
aws_cost = 0.50/hour
alibaba_cost = 0.35/hour  # 30% cheaper

# ML analysis: Historical data shows AWS has 99.9% uptime vs Alibaba 99.5%
# For critical workloads, reliability > cost
aws_ml_confidence = 0.9  # High confidence due to reliability
alibaba_ml_confidence = 0.4  # Lower confidence due to reliability

# Combined decision:
aws_combined = 0.7 * (1.0/0.50) + 0.3 * 0.9 = 1.4 + 0.27 = 1.67
alibaba_combined = 0.7 * (1.0/0.35) + 0.3 * 0.4 = 2.0 + 0.12 = 2.12

# Result: Alibaba still wins due to significant cost advantage
# But ML confidence is lower, indicating higher risk
```

##### **Example 2: Performance Override**
```python
# Workload: High-performance computing
workload = Workload(
    cpu_cores=32,
    memory_gb=128,
    priority="high",
    latency_sensitivity=0.8
)

# Cost analysis: AWS is 20% more expensive
aws_cost = 0.60/hour
alibaba_cost = 0.50/hour  # 20% cheaper

# ML analysis: Historical data shows AWS performs 40% better for HPC workloads
aws_ml_confidence = 0.9  # High confidence due to performance history
alibaba_ml_confidence = 0.3  # Lower confidence for HPC workloads

# Combined decision:
aws_combined = 0.7 * (1.0/0.60) + 0.3 * 0.9 = 1.17 + 0.27 = 1.44
alibaba_combined = 0.7 * (1.0/0.50) + 0.3 * 0.3 = 1.4 + 0.09 = 1.49

# Result: Alibaba still wins, but ML is warning about performance
# Decision includes ML warning: "High performance workload, consider AWS for better performance"
```

##### **Example 3: ML Override Success**
```python
# Workload: Standard web application
workload = Workload(
    cpu_cores=2,
    memory_gb=4,
    priority="medium",
    latency_sensitivity=0.5
)

# Cost analysis: AWS is 10% cheaper
aws_cost = 0.10/hour
alibaba_cost = 0.11/hour  # 10% more expensive

# ML analysis: Historical data shows Alibaba has 99.9% uptime vs AWS 99.7%
# For standard workloads, reliability matters more than small cost differences
aws_ml_confidence = 0.4  # Lower confidence due to reliability
alibaba_ml_confidence = 0.9  # High confidence due to reliability

# Combined decision:
aws_combined = 0.7 * (1.0/0.10) + 0.3 * 0.4 = 7.0 + 0.12 = 7.12
alibaba_combined = 0.7 * (1.0/0.11) + 0.3 * 0.9 = 6.36 + 0.27 = 6.63

# Result: AWS wins due to cost advantage
# But ML is suggesting Alibaba for reliability
# Decision includes ML warning: "Consider Alibaba for better reliability"
```

#### **🎯 ML Model Training Scenarios**

The ML model learns from these **decision patterns**:

##### **Pattern 1: Cost vs Reliability Trade-off**
```python
# Training data: Critical workloads
# Pattern: When cost difference < 20% and reliability difference > 2%
# → Choose higher reliability provider
if abs(aws_cost - alibaba_cost) / min(aws_cost, alibaba_cost) < 0.2:
    if aws_reliability > alibaba_reliability + 0.02:
        aws_ml_confidence += 0.3
    elif alibaba_reliability > aws_reliability + 0.02:
        alibaba_ml_confidence += 0.3
```

##### **Pattern 2: Performance vs Cost Trade-off**
```python
# Training data: High-performance workloads
# Pattern: When CPU > 8 cores and memory > 16GB
# → AWS typically performs better
if workload.cpu_cores > 8 and workload.memory_gb > 16:
    aws_ml_confidence += 0.2  # AWS performance advantage
```

##### **Pattern 3: Time-Based Patterns**
```python
# Training data: Time-based performance
# Pattern: AWS performs better during business hours
# Pattern: Alibaba performs better during off-peak hours
current_hour = datetime.now().hour
if 9 <= current_hour <= 17:  # Business hours
    aws_ml_confidence += 0.1
elif 0 <= current_hour <= 8 or 18 <= current_hour <= 23:  # Off-peak
    alibaba_ml_confidence += 0.1
```

#### **🎯 ML Model Persistence & Continuous Learning**

```python
def _save_model(self):
    """Save trained ML model for persistence"""
    import joblib
    os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
    joblib.dump(self.ml_model, self.model_path)
    logger.info(f"ML model saved to {self.model_path}")

def _load_model(self):
    """Load existing ML model"""
    try:
        self.ml_model = joblib.load(self.model_path)
        logger.info(f"ML model loaded from {self.model_path}")
    except FileNotFoundError:
        logger.info("No existing ML model found, will train new one")
        self._initialize_ml_model()
```

The ML model **automatically retrains** every 50 new decisions, ensuring it stays current with changing patterns and performance data.

#### **🧠 Learning from Every Decision - Detailed Explanation**

The ML model is like a **smart student** that watches every decision the AI makes and learns patterns from them. It's not just making random guesses - it's building knowledge from experience.

##### **📊 How It Works in Practice**

**Example 1: First 10 Decisions (Learning Phase)**

Let's say the AI makes these first 10 decisions:

```
Decision 1: Workload(4 CPU, 8GB, priority="medium") → AWS ($0.05/hour) → SUCCESS
Decision 2: Workload(2 CPU, 4GB, priority="low") → Alibaba ($0.03/hour) → SUCCESS  
Decision 3: Workload(8 CPU, 16GB, priority="high") → AWS ($0.20/hour) → SUCCESS
Decision 4: Workload(4 CPU, 8GB, priority="medium") → Alibaba ($0.04/hour) → SUCCESS
Decision 5: Workload(16 CPU, 32GB, priority="critical") → AWS ($0.80/hour) → SUCCESS
Decision 6: Workload(2 CPU, 4GB, priority="low") → Alibaba ($0.03/hour) → SUCCESS
Decision 7: Workload(8 CPU, 16GB, priority="high") → AWS ($0.20/hour) → SUCCESS
Decision 8: Workload(4 CPU, 8GB, priority="medium") → Alibaba ($0.04/hour) → SUCCESS
Decision 9: Workload(32 CPU, 64GB, priority="critical") → AWS ($1.60/hour) → SUCCESS
Decision 10: Workload(2 CPU, 4GB, priority="low") → Alibaba ($0.03/hour) → SUCCESS
```

**What the ML model learns:**
- **Pattern 1**: Small workloads (2-4 CPU) → Alibaba works well
- **Pattern 2**: Large workloads (8+ CPU) → AWS works well  
- **Pattern 3**: Critical workloads → AWS is more reliable
- **Pattern 4**: Medium workloads → Either works, but Alibaba is cheaper

**Example 2: ML Model Training Process**

After 10 decisions, the ML model trains itself:

```python
# Training data the ML model sees:
features = [
    [4, 8, 0.5, 0.05, 0.04, 50, 60, 0.99, 0.95, 14],  # Decision 1 → AWS
    [2, 4, 0.2, 0.05, 0.03, 50, 60, 0.99, 0.95, 15],  # Decision 2 → Alibaba
    [8, 16, 0.8, 0.20, 0.15, 50, 60, 0.99, 0.95, 16], # Decision 3 → AWS
    # ... more training data
]

targets = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]  # 0=AWS, 1=Alibaba

# ML model learns: "When I see these patterns, this provider usually works better"
```

**Example 3: ML Model Makes Predictions**

Now when a new workload comes in:

```python
# New workload: Workload(6 CPU, 12GB, priority="medium")
new_workload_features = [6, 12, 0.5, 0.08, 0.06, 50, 60, 0.99, 0.95, 14]

# ML model thinks:
# "This looks like a medium workload (6 CPU, 12GB)"
# "From my training, medium workloads usually work well on Alibaba"
# "But it's not too small (like 2-4 CPU) and not too large (like 16+ CPU)"
# "Based on my experience, I'm 70% confident Alibaba is better"

ml_confidence = 0.7  # 70% chance Alibaba is optimal
```

##### **🔄 Continuous Learning Process**

**Example 4: Learning from Mistakes**

Let's say the ML model makes a wrong prediction:

```
Decision 15: Workload(6 CPU, 12GB, priority="medium") → Alibaba (ML suggested) → FAILED
# The workload failed on Alibaba due to performance issues
```

**What happens:**
1. **ML model gets feedback**: "My prediction was wrong"
2. **Model adjusts**: "Maybe 6 CPU workloads need AWS after all"
3. **Future predictions**: "Next time I see 6 CPU, I'll be more cautious about Alibaba"

**Example 5: Learning from Success**

```
Decision 20: Workload(6 CPU, 12GB, priority="medium") → AWS → SUCCESS
# The workload succeeded on AWS
```

**What happens:**
1. **ML model gets feedback**: "My prediction was right"
2. **Model strengthens**: "6 CPU workloads do work better on AWS"
3. **Future predictions**: "Next time I see 6 CPU, I'll be more confident about AWS"

##### **🎯 Real-World Learning Scenarios**

**Scenario 1: Time-Based Learning**

```
# ML model learns from these patterns:
Morning (9 AM): Workload → AWS → SUCCESS
Afternoon (2 PM): Workload → Alibaba → SUCCESS  
Evening (8 PM): Workload → Alibaba → SUCCESS
Night (2 AM): Workload → AWS → SUCCESS

# ML model learns: "Time of day affects which provider works better"
# Future prediction: "It's 2 PM, so Alibaba is probably better"
```

**Scenario 2: Performance-Based Learning**

```
# ML model learns from these patterns:
High CPU (16+ cores): AWS → SUCCESS, Alibaba → FAILED
Medium CPU (4-8 cores): Either works, but Alibaba cheaper
Low CPU (2-4 cores): Alibaba → SUCCESS, AWS → Overkill

# ML model learns: "CPU requirements affect provider choice"
# Future prediction: "This has 20 CPU cores, so AWS is probably better"
```

**Scenario 3: Cost vs Performance Learning**

```
# ML model learns from these patterns:
Critical workload + AWS (expensive) → SUCCESS
Critical workload + Alibaba (cheap) → FAILED
Standard workload + Alibaba (cheap) → SUCCESS
Standard workload + AWS (expensive) → SUCCESS but wasteful

# ML model learns: "Critical workloads need AWS regardless of cost"
# Future prediction: "This is critical, so AWS is better even if expensive"
```

##### **🧠 How ML Confidence Builds Over Time**

**Early Days (0-50 decisions):**
```
ML confidence: 0.5 (50% - basically guessing)
Reasoning: "I don't have enough data yet"
```

**Learning Phase (50-200 decisions):**
```
ML confidence: 0.7 (70% - getting better)
Reasoning: "I've seen similar workloads before, and they usually work on this provider"
```

**Expert Phase (200+ decisions):**
```
ML confidence: 0.9 (90% - very confident)
Reasoning: "I've seen this exact pattern 20 times, and it always works on this provider"
```

##### **🎯 The Bottom Line**

**ML learning from every decision means:**

1. **📚 Building Knowledge**: Each decision teaches the model something new
2. **🔍 Pattern Recognition**: The model spots patterns humans might miss
3. **🎯 Better Predictions**: Over time, predictions get more accurate
4. **🔄 Self-Improvement**: The model gets smarter with each decision
5. **⚡ Faster Decisions**: The model learns to make decisions faster

**It's like having a smart assistant that gets better at its job every day!** 🤖📈

The ML model doesn't just make random guesses - it builds a **database of experience** from every decision, learning what works and what doesn't, so it can make better predictions in the future.

### Step 8: Workload Migration Process

#### **🔄 Complete Migration Workflow**

When the AI detects cost changes for running workloads, it initiates a **complete migration process**:

##### **Phase 1: Migration Detection & Approval**
```python
# AI continuously monitors running workloads
def monitor_running_workloads():
    for workload in running_workloads:
        current_cost = get_current_provider_cost(workload)
        alternative_cost = get_alternative_provider_cost(workload)
        
        if alternative_cost < current_cost * 0.8:  # 20% cheaper
            # Send migration approval request
            request_migration_approval(workload, current_cost, alternative_cost)
```

##### **Phase 2: Infrastructure Provisioning**
```python
# AI provisions new infrastructure
def provision_new_infrastructure(workload_id, new_provider):
    # 1. Generate Terraform for new provider
    terraform_config = generate_migration_terraform(workload_id, new_provider)
    
    # 2. Apply Terraform
    terraform_apply(terraform_config)
    
    # 3. Health check new infrastructure
    if health_check_infrastructure(new_provider):
        return "SUCCESS"
    else:
        rollback_infrastructure(new_provider)
        return "FAILED"
```

##### **Phase 3: Application Migration**
```python
# AI handles application migration
def migrate_application(workload_id, old_provider, new_provider):
    # 1. Stop application gracefully
    stop_application(old_provider)
    
    # 2. Export application state
    app_state = export_application_state(old_provider)
    
    # 3. Deploy application to new provider
    deploy_application(new_provider, app_state)
    
    # 4. Health check application
    if health_check_application(new_provider):
        return "SUCCESS"
    else:
        rollback_application(old_provider, app_state)
        return "FAILED"
```

##### **Phase 4: DNS Update & Traffic Routing**
```python
# AI updates DNS routing
def update_dns_routing(workload_id, new_provider):
    # 1. Get new load balancer DNS
    new_lb_dns = get_load_balancer_dns(new_provider)
    
    # 2. Update DNS records
    update_dns_record(workload_id.domain, new_lb_dns)
    
    # 3. Wait for DNS propagation
    wait_for_dns_propagation(workload_id.domain)
    
    # 4. Verify traffic routing
    verify_traffic_routing(workload_id.domain, new_provider)
```

##### **Phase 5: Verification & Cleanup**
```python
# AI verifies migration and cleans up
def complete_migration(workload_id, old_provider, new_provider):
    # 1. Verify new deployment works
    if verify_migration(workload_id, new_provider):
        # 2. Cleanup old infrastructure
        cleanup_old_infrastructure(workload_id, old_provider)
        return "SUCCESS"
    else:
        # 3. Rollback if verification fails
        rollback_migration(workload_id, old_provider, new_provider)
        return "FAILED"
```

#### **🎯 Migration Timeline**

```
⏰ T+0:00 - AI detects cost change
⏰ T+0:05 - Migration approval requested
⏰ T+0:10 - New infrastructure provisioned
⏰ T+0:15 - Application deployed to new provider
⏰ T+0:20 - DNS updated to point to new provider
⏰ T+0:25 - Traffic routing verified
⏰ T+0:30 - Old infrastructure cleaned up
⏰ T+0:35 - Migration completed!
```

#### **🔄 Rollback Process**

If migration fails at any phase:

```python
def rollback_migration(workload_id, old_provider, new_provider):
    # 1. Stop new application
    stop_application(new_provider)
    
    # 2. Restore old infrastructure
    restore_old_infrastructure(old_provider)
    
    # 3. Update DNS back to old provider
    restore_dns_routing(old_provider)
    
    # 4. Restart application on old provider
    restart_application(old_provider)
```

#### **📊 Migration Examples**

##### **Example 1: HTML Page Migration**
```python
# Before Migration:
swen-ai.com → AWS Load Balancer → AWS Server
Cost: $0.10/hour, Latency: 50ms

# After Migration:
swen-ai.com → Alibaba Load Balancer → Alibaba Server
Cost: $0.06/hour (40% cheaper!), Latency: 80ms
```

##### **Example 2: Database Strategy**
```python
# Recommended approach for databases:
database_strategy = {
    "aws_database": "Always running on AWS",
    "alibaba_database": "Always running on Alibaba", 
    "sync_strategy": "Real-time replication between clouds",
    "migration": "No database migration needed - just switch app connections"
}
```

### Step 9: Cost Exception Scenarios

#### **🚨 When Cost is NOT the Deciding Factor**

The AI can override cost-based decisions in these **exceptional scenarios**:

##### **1. Critical Workload Exception**
```python
# Exception: Critical workloads prioritize reliability over cost
if workload.priority == "critical":
    # Cost threshold is ignored for critical workloads
    # Reliability becomes the primary factor
    if aws_reliability > alibaba_reliability + 0.05:  # 5% reliability difference
        return "aws", region, 0.95  # Override cost decision
    elif alibaba_reliability > aws_reliability + 0.05:
        return "alibaba", region, 0.95  # Override cost decision
```

##### **2. Performance Exception**
```python
# Exception: High-performance workloads prioritize performance over cost
if workload.cpu_cores > 16 or workload.memory_gb > 64:
    # Performance becomes primary factor
    if aws_performance_score > alibaba_performance_score + 0.3:  # 30% performance difference
        return "aws", region, 0.90  # Override cost decision
    elif alibaba_performance_score > aws_performance_score + 0.3:
        return "alibaba", region, 0.90  # Override cost decision
```

##### **3. Latency Exception**
```python
# Exception: Latency-sensitive workloads prioritize latency over cost
if workload.latency_sensitivity > 0.8:
    # Latency becomes primary factor
    if aws_latency < alibaba_latency - 20:  # 20ms latency difference
        return "aws", region, 0.85  # Override cost decision
    elif alibaba_latency < aws_latency - 20:
        return "alibaba", region, 0.85  # Override cost decision
```

##### **4. Compliance Exception**
```python
# Exception: Compliance requirements override cost
if workload.requires_compliance:
    # Check compliance requirements
    if aws_compliance_score > alibaba_compliance_score:
        return "aws", region, 0.95  # Override cost decision
    elif alibaba_compliance_score > aws_compliance_score:
        return "alibaba", region, 0.95  # Override cost decision
```

##### **5. Security Exception**
```python
# Exception: Security requirements override cost
if workload.security_level == "high":
    # Security becomes primary factor
    if aws_security_score > alibaba_security_score + 0.1:  # 10% security difference
        return "aws", region, 0.90  # Override cost decision
    elif alibaba_security_score > aws_security_score + 0.1:
        return "alibaba", region, 0.90  # Override cost decision
```

#### **🎯 Cost Exception Examples**

##### **Example 1: Critical AI Training Override**
```python
# Workload: Critical AI training job
workload = Workload(
    cpu_cores=32,
    memory_gb=128,
    priority="critical",
    latency_sensitivity=0.9,
    security_level="high"
)

# Cost analysis: Alibaba is 40% cheaper
aws_cost = 1.00/hour
alibaba_cost = 0.60/hour  # 40% cheaper

# Exception check: Critical workload
if workload.priority == "critical":
    # Reliability becomes primary factor
    aws_reliability = 0.999  # 99.9% uptime
    alibaba_reliability = 0.995  # 99.5% uptime
    
    if aws_reliability > alibaba_reliability + 0.05:
        # AWS chosen despite 40% higher cost
        return "aws", "us-west-2", 0.95
        # Decision: "Critical workload requires maximum reliability, cost secondary"
```

##### **Example 2: High-Performance Override**
```python
# Workload: High-performance computing
workload = Workload(
    cpu_cores=64,
    memory_gb=256,
    priority="high",
    latency_sensitivity=0.8
)

# Cost analysis: AWS is 50% more expensive
aws_cost = 2.00/hour
alibaba_cost = 1.00/hour  # 50% cheaper

# Exception check: High-performance workload
if workload.cpu_cores > 16:
    # Performance becomes primary factor
    aws_performance = 0.95  # 95% performance score
    alibaba_performance = 0.70  # 70% performance score
    
    if aws_performance > alibaba_performance + 0.3:
        # AWS chosen despite 50% higher cost
        return "aws", "us-west-2", 0.90
        # Decision: "High-performance workload requires AWS infrastructure, cost secondary"
```

##### **Example 3: Latency-Sensitive Override**
```python
# Workload: Real-time trading system
workload = Workload(
    cpu_cores=8,
    memory_gb=16,
    priority="high",
    latency_sensitivity=0.95  # Very latency sensitive
)

# Cost analysis: AWS is 30% more expensive
aws_cost = 0.50/hour
alibaba_cost = 0.35/hour  # 30% cheaper

# Exception check: Latency-sensitive workload
if workload.latency_sensitivity > 0.8:
    # Latency becomes primary factor
    aws_latency = 10  # 10ms latency
    alibaba_latency = 50  # 50ms latency
    
    if aws_latency < alibaba_latency - 20:  # 20ms difference
        # AWS chosen despite 30% higher cost
        return "aws", "us-west-2", 0.85
        # Decision: "Latency-sensitive workload requires AWS low latency, cost secondary"
```

#### **🎯 Cost Exception Decision Matrix**

| Scenario | Primary Factor | Cost Override Threshold | Example |
|----------|----------------|-------------------------|---------|
| **Critical Workload** | Reliability | > 5% reliability difference | 99.9% vs 99.5% uptime |
| **High Performance** | Performance | > 30% performance difference | 95% vs 70% performance |
| **Latency Sensitive** | Latency | > 20ms latency difference | 10ms vs 50ms latency |
| **Security Required** | Security | > 10% security difference | 95% vs 85% security score |
| **Compliance Required** | Compliance | Any compliance difference | SOC2 vs ISO27001 |

#### **🎯 Cost Exception Logging**

Every cost exception is logged with full context:

```python
cost_exception = {
    'timestamp': '2024-01-15T10:30:00Z',
    'workload_id': 'workload-123',
    'exception_type': 'critical_workload',
    'primary_factor': 'reliability',
    'cost_override': {
        'aws_cost': 1.00,
        'alibaba_cost': 0.60,
        'cost_difference': 0.40,
        'cost_percentage': 0.40
    },
    'decision_factors': {
        'aws_reliability': 0.999,
        'alibaba_reliability': 0.995,
        'reliability_difference': 0.004
    },
    'final_decision': 'aws',
    'confidence': 0.95,
    'reasoning': 'Critical workload requires maximum reliability, cost secondary'
}
```

## 🚨 Approval Process

### Approval Triggers

The AI requires manual approval in these scenarios:

1. **Cost Threshold Exceeded**: `estimated_cost > $50/hour` (configurable)
2. **High Risk Workload**: `priority == "critical"` and `cost > $100/hour`
3. **Low ML Confidence**: ML model confidence < 0.3
4. **Budget Limit**: Monthly budget exceeded
5. **Unusual Pattern**: Workload doesn't match historical patterns

### Approval Workflow

#### Step 1: Cost Threshold Check

```python
def process_workload(workload):
    # Calculate optimal placement
    provider, region, confidence = self.calculate_optimal_placement(workload)
    estimated_cost = self._calculate_workload_cost(workload, providers[provider])
    
    # Check cost threshold
    if not self._check_cost_threshold(estimated_cost):
        # Cost too high - require manual approval
        self._queue_for_approval(workload, estimated_cost, "Cost exceeds threshold")
        return  # Stop processing, wait for approval
```

#### Step 2: Queue for Approval

```python
def _queue_for_approval(workload, estimated_cost, reason):
    approval_request = {
        'workload_id': workload.id,
        'estimated_cost': estimated_cost,
        'reason': reason,
        'timestamp': datetime.now(),
        'status': 'pending',
        'aws_cost': self._get_aws_cost(),
        'alibaba_cost': self._get_alibaba_cost(),
        'recommended_provider': provider
    }
    
    # Add to pending workloads
    self.pending_workloads.append(approval_request)
    
    # Send notifications
    self._send_approval_notification(approval_request)
    self.send_alert(f"Workload {workload.id} requires approval: {reason}")
```

#### Step 3: Notification System

**Email Notification:**
```
Subject: SWEN AI: Workload workload-123 requires approval

Workload ID: workload-123
Reason: Cost $75.00/hour exceeds threshold $50.00/hour
Estimated Savings: $25.00/hour
AWS Cost: $100.00/hour
Alibaba Cost: $75.00/hour
Recommended Provider: alibaba

To approve: POST /approve/workload-123 with {"approved": true}
To reject: POST /approve/workload-123 with {"approved": false}
```

**Slack Notification:**
```json
{
    "text": "SWEN AI Alert: Workload workload-123 requires approval. Reason: Cost exceeds threshold",
    "severity": "warning",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Step 4: Manual Approval

```python
def approve_workload(workload_id, approved):
    if approved:
        # Deploy the workload
        self._deploy_workload(workload_id)
        logger.info(f"Workload {workload_id} approved and deployed")
    else:
        # Reject the workload
        logger.info(f"Workload {workload_id} rejected by human")
```

## 🔄 Complete Workflow

### Automatic Deployment (Low Cost)

```python
# 1. Workload arrives
workload = Workload(cpu_cores=2, memory_gb=4, priority="medium")

# 2. AI processes workload
engine.process_workload(workload)
    ↓
# 3. AI calculates optimal placement
provider, region, confidence = engine.calculate_optimal_placement(workload)
    ↓
# 4. AI checks cost threshold
if estimated_cost <= $50/hour:
    continue_processing()  # Auto-approve
else:
    queue_for_approval()  # Manual approval required
    ↓
# 5. AI generates Terraform changes
terraform_changes = engine.generate_terraform_changes(workload, provider, region)
    ↓
# 6. AI applies changes automatically
engine._apply_terraform_changes(terraform_changes)
    ↓
# 7. AI updates DNS records
engine._update_dns_records(lb_dns_names)
    ↓
# 8. AI monitors costs continuously
engine._continuous_monitoring()
```

### Manual Approval (High Cost)

```python
# 1. Workload arrives
workload = Workload(cpu_cores=8, memory_gb=16, priority="critical")

# 2. AI processes workload
engine.process_workload(workload)
    ↓
# 3. AI calculates optimal placement
provider, region, confidence = engine.calculate_optimal_placement(workload)
    ↓
# 4. AI checks cost threshold
if estimated_cost > $50/hour:
    queue_for_approval()  # Manual approval required
    ↓
# 5. Human reviews and approves/rejects
human.approve_workload(workload_id, approved=True)
    ↓
# 6. AI deploys after approval
engine._deploy_workload(workload_id)
```

## 📊 Decision History & Logging

Every AI decision is logged with full context:

```python
decision = {
    'timestamp': '2024-01-15T10:30:00Z',
    'workload_id': 'workload-123',
    'selected_provider': 'alibaba',
    'estimated_cost': 0.019,
    'all_costs': {'aws': 0.032, 'alibaba': 0.019},
    'ml_predictions': {'aws': 0.3, 'alibaba': 0.8},
    'combined_scores': {'aws': 21.965, 'alibaba': 37.081},
    'confidence_score': 0.85,
    'cost_confidence': 0.9,
    'ml_confidence': 0.8,
    'reasoning': 'Alibaba selected due to 40% cost savings and high ML confidence'
}
```

## 🎯 Key Configuration

### Environment Variables

```bash
# Cost threshold for automatic approval
AI_COST_THRESHOLD=50.0  # $50/hour

# ML model path
AI_ML_MODEL_PATH=./models/routing_model.pkl

# Approval settings
AUTO_DEPLOY_ENABLED=false  # Manual approval by default
APPROVAL_THRESHOLD=0.01    # $0.01/hour savings threshold
MAX_COST_PER_HOUR=1.0      # $1/hour max cost
```

### ML Model Training

The ML model automatically trains on historical decision data:

```python
def _train_ml_model(self):
    if len(self.decision_history) < 10:
        return  # Need at least 10 decisions to train
    
    # Prepare training data
    features = []
    targets = []
    
    for decision in self.decision_history:
        features.append([
            decision['workload_cpu_cores'],
            decision['workload_memory_gb'],
            decision['aws_cost'],
            decision['alibaba_cost'],
            decision['aws_latency'],
            decision['alibaba_latency']
        ])
        targets.append(1 if decision['selected_provider'] == 'alibaba' else 0)
    
    # Train model
    self.ml_model.fit(features, targets)
    self._save_model()
```

## 🚀 The Bottom Line

The SWEN AI Engine is a fully autonomous cloud manager that:

1. **Analyzes** costs and performance data in real-time
2. **Decides** which cloud is optimal using ML + cost analysis
3. **Checks** if approval is needed based on cost thresholds
4. **Deploys** infrastructure automatically (if approved)
5. **Monitors** costs continuously
6. **Switches** providers when better options are available
7. **Updates** DNS for zero-downtime switching

It's fully autonomous but has safety gates for expensive workloads, ensuring human oversight when needed.
