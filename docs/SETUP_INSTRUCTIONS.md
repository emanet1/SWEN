# SWEN GitOps + AIOps Setup Instructions

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 20GB free disk space
- **Network**: Internet connection for cloud provider access

### Required Software
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Terraform**: Version 1.5+
- **Python**: Version 3.9+
- **Node.js**: Version 18+
- **Git**: Version 2.30+

### Cloud Provider Accounts
- **AWS Account**: With programmatic access
- **Alibaba Cloud Account**: With programmatic access
- **GitHub/GitLab**: For GitOps repository

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/swen-org/gitops-aiops.git
cd gitops-aiops
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.template .env

# Edit environment variables
nano .env
```

### 3. Infrastructure Deployment
```bash
# Navigate to infrastructure directory
cd infra/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply infrastructure
terraform apply
```

### 4. Start AI Engine
```bash
# Navigate to AI engine directory
cd ../../ai-engine

# Install dependencies
pip install -r requirements.txt

# Start AI routing engine
python main.py
```

### 5. Launch Dashboard
```bash
# Navigate to dashboard directory
cd ../dashboard

# Install dependencies
npm install

# Start development server
npm run dev
```

### 6. Start Observability Stack
```bash
# Navigate to observability directory
cd ../observability

# Start monitoring stack
docker-compose up -d
```

## Detailed Setup

### Infrastructure Setup

#### 1. AWS Configuration
```bash
# Configure AWS credentials
aws configure

# Set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"
```

#### 2. Alibaba Cloud Configuration
```bash
# Configure Alibaba Cloud credentials
aliyun configure

# Set environment variables
export ALIBABA_ACCESS_KEY_ID="your-access-key"
export ALIBABA_ACCESS_KEY_SECRET="your-secret-key"
export ALIBABA_REGION="us-west-1"
```

#### 3. Terraform Variables
```bash
# Create terraform.tfvars file
cat > infra/terraform/terraform.tfvars << EOF
environment = "dev"
aws_region = "us-west-2"
alibaba_region = "us-west-1"
budget_limit_usd = 1000
cost_alert_threshold = 80
EOF
```

### AI Engine Setup

#### 1. Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r ai-engine/requirements.txt
```

#### 2. Configuration
```bash
# Copy configuration template
cp ai-engine/config.yaml.template ai-engine/config.yaml

# Edit configuration
nano ai-engine/config.yaml
```

#### 3. Start AI Engine
```bash
# Start AI routing engine
cd ai-engine
python main.py
```

### Dashboard Setup

#### 1. Node.js Environment
```bash
# Install Node.js dependencies
cd dashboard
npm install
```

#### 2. Environment Configuration
```bash
# Create environment file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:3000
NEXT_PUBLIC_WS_URL=ws://localhost:3001
EOF
```

#### 3. Start Dashboard
```bash
# Start development server
npm run dev

# Dashboard will be available at http://localhost:3000
```

### Observability Setup

#### 1. Docker Environment
```bash
# Start observability stack
cd observability
docker-compose up -d
```

#### 2. Access Monitoring Tools
- **Grafana**: http://localhost:3000 (admin/swen-admin-2024)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093
- **Jaeger**: http://localhost:16686

### GitOps Setup

#### 1. ArgoCD Installation
```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Get ArgoCD admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

#### 2. Configure GitOps
```bash
# Apply ArgoCD application
kubectl apply -f infra/gitops/argocd-application.yaml
```

## Configuration

### Environment Variables

#### Required Variables
```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=us-west-2

# Alibaba Cloud Configuration
ALIBABA_ACCESS_KEY_ID=your-alibaba-access-key
ALIBABA_ACCESS_KEY_SECRET=your-alibaba-secret-key
ALIBABA_REGION=us-west-1

# GitOps Configuration
GITOPS_REPOSITORY=https://github.com/your-org/infrastructure.git
GITOPS_BRANCH=main

# Monitoring Configuration
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
```

#### Optional Variables
```bash
# AI Engine Configuration
AI_ENGINE_HOST=0.0.0.0
AI_ENGINE_PORT=8080
AI_CONFIDENCE_THRESHOLD=0.6
AI_COST_THRESHOLD=50.0

# Dashboard Configuration
DASHBOARD_PORT=3000
DASHBOARD_HOST=0.0.0.0

# Observability Configuration
PROMETHEUS_RETENTION=30d
GRAFANA_ADMIN_PASSWORD=swen-admin-2024
```

### Terraform Configuration

#### Main Configuration
```hcl
# infra/terraform/main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    alicloud = {
      source  = "alicloud/alicloud"
      version = "~> 1.200"
    }
  }
}
```

#### Variables
```hcl
# infra/terraform/variables.tf
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "budget_limit_usd" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 1000
}
```

### AI Engine Configuration

#### YAML Configuration
```yaml
# ai-engine/config.yaml
providers:
  aws:
    regions: ["us-west-2", "us-east-1"]
    base_cost: 0.05
    latency_base: 50
    
  alibaba:
    regions: ["us-west-1", "ap-southeast-1"]
    base_cost: 0.03
    latency_base: 60

routing:
  algorithm: "balanced"
  cost_weight: 0.4
  latency_weight: 0.3
  reliability_weight: 0.3
```

## Verification

### Health Checks

#### 1. Infrastructure Health
```bash
# Check AWS infrastructure
curl http://aws-load-balancer-url/health

# Check Alibaba infrastructure
curl http://alibaba-load-balancer-url/health
```

#### 2. AI Engine Health
```bash
# Check AI engine
curl http://localhost:8080/health

# Check AI engine metrics
curl http://localhost:8080/metrics
```

#### 3. Dashboard Health
```bash
# Check dashboard
curl http://localhost:3000/api/health

# Check telemetry API
curl http://localhost:3000/api/telemetry
```

#### 4. Observability Health
```bash
# Check Prometheus
curl http://localhost:9090/-/healthy

# Check Grafana
curl http://localhost:3000/api/health

# Check Alertmanager
curl http://localhost:9093/-/healthy
```

### Performance Testing

#### 1. Load Testing
```bash
# Install load testing tools
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:3000
```

#### 2. AI Engine Testing
```bash
# Test AI routing decisions
python tests/test_ai_engine.py

# Test cost optimization
python tests/test_cost_optimization.py
```

## Troubleshooting

### Common Issues

#### 1. Terraform Issues
```bash
# Terraform state issues
terraform refresh
terraform plan -refresh-only

# Provider authentication issues
terraform init -upgrade
```

#### 2. AI Engine Issues
```bash
# Python dependency issues
pip install --upgrade -r requirements.txt

# Configuration issues
python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"
```

#### 3. Dashboard Issues
```bash
# Node.js dependency issues
npm install --force

# Build issues
npm run build
npm run start
```

#### 4. Observability Issues
```bash
# Docker issues
docker-compose down
docker-compose up -d

# Port conflicts
netstat -tulpn | grep :3000
```

### Logs and Debugging

#### 1. AI Engine Logs
```bash
# View AI engine logs
tail -f /var/log/swen-ai-engine.log

# Debug mode
python main.py --debug
```

#### 2. Dashboard Logs
```bash
# View dashboard logs
npm run dev 2>&1 | tee dashboard.log
```

#### 3. Infrastructure Logs
```bash
# View Terraform logs
export TF_LOG=DEBUG
terraform apply
```

## Security Considerations

### 1. Access Control
- **IAM Policies**: Restrictive IAM policies
- **Network Security**: VPC isolation and security groups
- **API Security**: API key management and rotation
- **Authentication**: Multi-factor authentication

### 2. Data Protection
- **Encryption**: Data encryption at rest and in transit
- **Key Management**: Centralized key management
- **Backup Security**: Encrypted backups
- **Audit Logging**: Comprehensive audit logs

### 3. Compliance
- **GDPR**: Data protection compliance
- **SOC 2**: Security and availability compliance
- **ISO 27001**: Information security management
- **PCI DSS**: Payment card industry compliance

## Maintenance

### 1. Regular Updates
- **Dependencies**: Regular dependency updates
- **Security Patches**: Security patch management
- **Infrastructure**: Infrastructure updates
- **Monitoring**: Monitoring system updates

### 2. Backup and Recovery
- **Data Backup**: Regular data backups
- **Configuration Backup**: Configuration backups
- **Disaster Recovery**: Disaster recovery procedures
- **Testing**: Regular recovery testing

### 3. Performance Optimization
- **Resource Optimization**: Regular resource optimization
- **Cost Optimization**: Continuous cost optimization
- **Performance Monitoring**: Performance monitoring
- **Capacity Planning**: Capacity planning

## Support

### 1. Documentation
- **README**: Main documentation
- **API Docs**: API documentation
- **Troubleshooting**: Troubleshooting guides
- **Best Practices**: Best practices guide

### 2. Community
- **GitHub Issues**: Issue tracking
- **Discussions**: Community discussions
- **Wiki**: Community wiki
- **Contributing**: Contribution guidelines

### 3. Professional Support
- **Enterprise Support**: Enterprise support options
- **Consulting**: Professional consulting services
- **Training**: Training and certification programs
- **Custom Development**: Custom development services

---

*For additional support, please refer to the documentation or contact the SWEN team.*
