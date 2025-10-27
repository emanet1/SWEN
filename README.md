# SWEN GitOps + AIOps Technical Test
## Self-Healing, Cost-Optimizing Cloud Backbone

This project implements a prototype of SWEN's intelligent infrastructure that autonomously manages AI workloads across multiple clouds for optimal cost and performance.

### 🎯 Project Overview

SWEN is building a global AI-powered news intelligence platform. This prototype demonstrates the core brain of that system — an intelligent GitOps + AIOps platform that:

- **Self-heals**: Detects and fixes infrastructure issues automatically
- **Self-optimizes**: Continuously learns from telemetry to reduce costs
- **Self-aware**: Visualizes every decision, cost, and metric in real-time

### 🏗️ Architecture Components

1. **GitOps + IaC Foundation**
   - Multi-cloud Terraform modules (AWS + Alibaba Cloud)
   - Automated GitOps pipeline with ArgoCD
   - Policy-based approvals and audit trails

2. **AI-Driven Cost-Routing Engine**
   - Real-time cost and latency analysis
   - ML model for workload optimization
   - Automated infrastructure changes via Git

3. **Live Telemetry Dashboard**
   - Real-time metrics visualization
   - Cost vs performance analytics
   - AI decision history and explainability

4. **Observability & Self-Healing**
   - Prometheus/Grafana integration
   - Automated recovery mechanisms
   - Health monitoring and alerting

5. **FinOps & Policy Intelligence**
   - Budget management and cost governance
   - Auto-approval policies
   - Cost optimization recommendations

### 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd swen-gitops-aiops

# Set up environment
cp env.template .env
# Edit .env with your cloud credentials

# Deploy zero-cost infrastructure
cd infra/terraform
terraform init
terraform plan
terraform apply

# Start all services (recommended)
./start_swen_system.sh

# OR start manually:
# Terminal 1: AI Engine
cd ai-engine
pip install -r requirements.txt
python main.py

# Terminal 2: Webhook Server
cd ai-engine
python webhook_server.py

# Terminal 3: Dashboard
cd dashboard
npm install
npm run dev

# Test the system
python test_complete_system.py
```

### 📊 Live Dashboard

Access the live telemetry dashboard at: `http://localhost:3000`

### 🔧 Health Check

Check system status: `http://localhost:8080/healthz`

### 📁 Project Structure

```
swen-gitops-aiops/
├── infra/                    # Infrastructure as Code
│   ├── terraform/           # Terraform modules (zero-cost deployment)
│   └── gitops/              # GitOps configurations
├── ai-engine/               # AI routing engine
│   ├── main.py              # Core AI engine
│   ├── webhook_server.py    # Webhook API server
│   └── simulated_app.py     # Simulated application monitoring
├── dashboard/               # Live telemetry dashboard
│   ├── pages/               # Dashboard pages
│   └── pages/api/           # API endpoints
├── observability/           # Prometheus/Grafana setup
├── policies/                # FinOps policies
├── docs/                    # Documentation
│   ├── AI_DECISION_PROCESS.md      # Detailed AI decision workflow
│   ├── AI_WORKFLOW_QUICK_REFERENCE.md # Quick reference guide
│   ├── ARCHITECTURE.md              # System architecture
│   └── SETUP_INSTRUCTIONS.md        # Setup guide
├── start_swen_system.sh     # System startup script
└── test_complete_system.py  # Complete system test suite
```

### 📋 Deliverables

- ✅ Public Git Repository
- ✅ Live Dashboard with Real-time Telemetry
- ✅ Video Demo (5-10 minutes)
- ✅ Comprehensive Documentation
- ✅ Health Endpoint
- ✅ Grafana Integration
- ✅ AI Decision Logging

### 🤖 AI-Human Collaboration

This project was built with extensive AI assistance. See `AI_LOG.md` for detailed documentation of AI tools used and development acceleration techniques.

### 📈 Evaluation Criteria

- **Infrastructure-as-Code**: Modular, reproducible IaC
- **GitOps Pipeline**: End-to-end automated deployments
- **AI Engine Logic**: Cost + latency analysis with explainable routing
- **Live Telemetry**: Real-time data updates and system visibility
- **Dashboard UX**: Clear, informative interface for all stakeholders
- **FinOps Governance**: Policies, budgets, and cost insights
- **AI-Human Collaboration**: Quality of AI-assisted development

---

*This is a prototype of SWEN's brain — demonstrating how infrastructure can see itself, think for itself, and optimize itself in real-time.*
