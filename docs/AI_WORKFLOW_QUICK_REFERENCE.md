# SWEN AI Workflow Quick Reference

## 🎯 AI Decision Process (Quick Overview)

### 1. Workload Arrives
```
Application → Webhook → AI Engine → process_workload()
```

### 2. AI Analyzes Real Data
```
AWS EC2 API → CloudWatch Metrics → Load Balancer Ping → ML Model
Alibaba Simulated Data (Risk Control Disabled)
```

### 3. AI Makes Decision
```
70% Cost Analysis + 30% ML Prediction = Optimal Provider
```

### 4. Approval Check
```
Cost > $50/hour? → Manual Approval Required
Cost ≤ $50/hour? → Auto-Deploy
```

### 5. Infrastructure Deployment
```
Terraform Changes → Apply → Real Data Collection → DNS Update → Monitoring
```

## 🚨 Approval Triggers

| Trigger | Condition | Action |
|---------|-----------|--------|
| **Cost Threshold** | `cost > $50/hour` | Manual approval |
| **High Risk** | `priority="critical"` + `cost > $100/hour` | Manual approval |
| **Low ML Confidence** | `ml_confidence < 0.3` | Manual approval |
| **Budget Limit** | Monthly budget exceeded | Manual approval |

## 📊 Decision Scoring

### Cost Score Calculation
```python
cost_score = 1.0 / (provider_cost + 0.001)
# Lower cost = Higher score
```

### ML Score Calculation
```python
ml_score = ml_model.predict_proba([features])[0][1]
# 0-1, higher = more likely to be optimal
```

### Combined Score
```python
combined_score = 0.7 * cost_score + 0.3 * ml_score
# 70% cost + 30% ML
```

## 🔄 Complete Workflow

### Automatic Deployment
```
Workload → AI Decision → Cost Check → Auto-Deploy → Monitor
```

### Manual Approval
```
Workload → AI Decision → Cost Check → Queue → Human Review → Deploy/Reject
```

## 📧 Notification System

### Email Notifications
- **Approval Requests**: High-cost workloads
- **Deployment Success**: Infrastructure deployed
- **Cost Alerts**: Budget thresholds
- **Failure Alerts**: Deployment errors

### Slack Notifications
- **Real-time Alerts**: Immediate notifications
- **Status Updates**: Deployment progress
- **Error Alerts**: System failures

## 🎛️ Configuration

### Key Environment Variables
```bash
AI_COST_THRESHOLD=50.0          # $50/hour threshold
AI_ML_MODEL_PATH=./models/      # ML model location
AUTO_DEPLOY_ENABLED=false       # Manual approval default
APPROVAL_THRESHOLD=0.01         # $0.01/hour savings threshold
```

### ML Model Features
- Workload CPU cores
- Workload memory
- Provider cost per hour
- Provider latency
- Provider reliability
- Historical success rate

## 📈 Monitoring & Metrics

### Prometheus Metrics
- `swen_workload_requests_total`
- `swen_cost_savings_dollars`
- `swen_ai_decisions_total`
- `swen_approval_requests_total`
- `swen_terraform_applies_total`

### Dashboard Views
- Real-time telemetry
- Cost vs latency graphs
- AI decision history
- Approval queue status
- Infrastructure status

## 🚀 Quick Commands

### Start System
```bash
./start_swen_system.sh
```

### Check Status
```bash
curl http://localhost:8080/health
curl http://localhost:8080/telemetry
```

### View Dashboard
```
http://localhost:3000
```

### Test Workload
```bash
python test_complete_system.py
```

## 🎯 The Bottom Line

**SWEN AI = Smart Cloud Manager**

- ✅ **Autonomous**: Makes decisions automatically
- ✅ **Safe**: Requires approval for expensive workloads
- ✅ **Optimized**: Continuously improves with ML
- ✅ **Transparent**: Full decision logging and explainability
- ✅ **Efficient**: Zero-downtime switching between clouds
