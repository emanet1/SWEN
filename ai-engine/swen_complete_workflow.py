#!/usr/bin/env python3
"""
SWEN Complete Workflow Demo
Demonstrates the complete AI-driven deployment workflow:
1. Send workload request
2. AI analyzes costs and chooses cheapest provider
3. AI asks for approval
4. User approves
5. AI deploys application to chosen provider
"""

import requests
import time
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SWENWorkflowDemo:
    """Complete SWEN workflow demonstration"""
    
    def __init__(self, ai_engine_url="http://localhost:8080"):
        self.ai_engine_url = ai_engine_url
        self.workload_id = None
        
    def step_1_send_workload_request(self):
        """Step 1: Send a workload request to the AI engine"""
        logger.info("🚀 STEP 1: Sending workload request to AI engine")
        
        workload_data = {
            "id": f"swen-demo-{int(time.time())}",
            "cpu_cores": 2,
            "memory_gb": 4,
            "priority": "medium",
            "cost_sensitivity": 0.8,  # High cost sensitivity - prefer cheaper option
            "latency_sensitivity": 0.3,  # Low latency sensitivity
            "estimated_duration_hours": 24.0,
            "reason": "SWEN Demo Application Deployment"
        }
        
        try:
            response = requests.post(
                f"{self.ai_engine_url}/workload",
                json=workload_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.workload_id = result['workload_id']
                logger.info(f"✅ Workload request sent: {self.workload_id}")
                logger.info(f"📋 Approval required: {result['approval_required']}")
                return True
            else:
                logger.error(f"❌ Failed to send workload: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending workload: {e}")
            return False
    
    def step_2_check_ai_decision(self):
        """Step 2: Check what decision the AI made"""
        logger.info("🧠 STEP 2: Checking AI decision and pending approvals")
        
        try:
            response = requests.get(f"{self.ai_engine_url}/pending", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Handle both direct array and wrapped response
                if isinstance(data, list):
                    workloads = data
                elif isinstance(data, dict) and 'pending_workloads' in data:
                    workloads = data['pending_workloads']
                else:
                    workloads = []
                
                logger.info(f"📋 Found {len(workloads)} pending workloads")
                
                for workload in workloads:
                    if workload['workload_id'] == self.workload_id:
                        logger.info(f"🎯 AI Decision for {self.workload_id}:")
                        logger.info(f"   Recommended Provider: {workload['recommended_provider']}")
                        logger.info(f"   AWS Cost: ${workload['aws_cost']:.3f}/hour")
                        logger.info(f"   Alibaba Cost: ${workload['alibaba_cost']:.3f}/hour")
                        logger.info(f"   Estimated Savings: ${workload['estimated_savings']:.3f}/hour")
                        logger.info(f"   Reason: {workload['reason']}")
                        return workload
                
                logger.warning("⚠️ Workload not found in pending list")
                return None
            else:
                logger.error(f"❌ Failed to check pending workloads: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error checking AI decision: {e}")
            return None
    
    def step_3_approve_decision(self, workload_data):
        """Step 3: Approve the AI decision"""
        logger.info("✅ STEP 3: Approving AI decision")
        
        try:
            response = requests.post(
                f"{self.ai_engine_url}/approve/{self.workload_id}",
                json={"approved": True},
                timeout=60  # Increased timeout to 60 seconds for deployment
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Workload {self.workload_id} approved")
                logger.info(f"🎯 AI will now deploy to: {workload_data['recommended_provider']}")
                return True
            else:
                logger.error(f"❌ Failed to approve workload: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error approving workload: {e}")
            return False
    
    def step_4_wait_for_deployment(self):
        """Step 4: Wait for AI to deploy the application"""
        logger.info("⏳ STEP 4: Waiting for AI to deploy application...")
        
        logger.info("🔄 AI is now:")
        logger.info("   1. Generating Terraform changes")
        logger.info("   2. Applying infrastructure changes")
        logger.info("   3. Deploying SWEN application")
        logger.info("   4. Configuring load balancer")
        logger.info("   5. Running health checks")
        
        # Wait for actual deployment (check every 5 seconds for up to 2 minutes)
        max_attempts = 24  # 2 minutes
        for attempt in range(max_attempts):
            time.sleep(5)
            logger.info(f"   ⏳ Checking deployment status... (attempt {attempt + 1}/{max_attempts})")
            
            # Check if instances are actually deployed
            if self._check_actual_deployment():
                logger.info("✅ Deployment verified! Instances are running.")
                return True
        
        logger.warning("⚠️ Deployment timeout - instances may still be starting")
        return False
    
    def step_5_verify_deployment(self):
        """Step 5: Verify the deployment"""
        logger.info("🔍 STEP 5: Verifying deployment")
        
        # Get actual Terraform outputs
        terraform_outputs = self._get_terraform_outputs()
        if not terraform_outputs:
            logger.error("❌ Failed to get Terraform outputs")
            return False
        
        # Check which provider was deployed
        aws_lb = terraform_outputs.get('aws_endpoints', {}).get('load_balancer_dns')
        alibaba_lb = terraform_outputs.get('alibaba_endpoints', {}).get('load_balancer_dns')
        
        logger.info("🌐 SWEN Application URLs:")
        if aws_lb and aws_lb != "swen-ai-dev.amazonaws.com":  # Real LB DNS
            logger.info(f"   AWS: http://{aws_lb}")
        else:
            logger.info("   AWS: No instances deployed")
            
        if alibaba_lb and alibaba_lb != "swen-ai-dev.alibabacloud.com":  # Real LB DNS
            logger.info(f"   Alibaba: http://{alibaba_lb}")
        else:
            logger.info("   Alibaba: No instances deployed")
        
        # Check if any instances are actually running
        instance_count = self._get_running_instance_count()
        if instance_count > 0:
            logger.info(f"✅ {instance_count} instances are running")
            logger.info("📊 Dashboard should now show:")
            logger.info("   - Real instance counts")
            logger.info("   - Real costs")
            logger.info("   - Real latency measurements")
            logger.info("   - AI decision history")
            return True
        else:
            logger.warning("⚠️ No instances detected - deployment may have failed")
            return False
    
    def run_complete_workflow(self):
        """Run the complete SWEN workflow"""
        logger.info("🎯 STARTING SWEN COMPLETE WORKFLOW DEMO")
        logger.info("=" * 50)
        
        # Check if AI engine is running
        try:
            response = requests.get(f"{self.ai_engine_url}/health", timeout=5)
            if response.status_code != 200:
                logger.error("❌ AI Engine not running. Please start: python webhook_server.py")
                return False
        except:
            logger.error("❌ Cannot connect to AI Engine. Please start: python webhook_server.py")
            return False
        
        logger.info("✅ AI Engine is running")
        logger.info("")
        
        # Step 1: Send workload request
        if not self.step_1_send_workload_request():
            return False
        
        logger.info("")
        
        # Step 2: Check AI decision
        workload_data = self.step_2_check_ai_decision()
        if not workload_data:
            return False
        
        logger.info("")
        
        # Step 3: Approve decision
        if not self.step_3_approve_decision(workload_data):
            return False
        
        logger.info("")
        
        # Step 4: Wait for deployment
        if not self.step_4_wait_for_deployment():
            return False
        
        logger.info("")
        
        # Step 5: Verify deployment
        if not self.step_5_verify_deployment():
            return False
        
        logger.info("")
        logger.info("🎉 SWEN WORKFLOW COMPLETED SUCCESSFULLY!")
        logger.info("=" * 50)
    
    def _check_actual_deployment(self):
        """Check if instances are actually deployed"""
        try:
            # Check Terraform state for instances
            import subprocess
            import os
            
            terraform_dir = os.path.join(os.path.dirname(__file__), '..', 'infra', 'terraform')
            terraform_dir = os.path.abspath(terraform_dir)
            
            # Check for AWS instances
            aws_result = subprocess.run([
                'terraform', 'state', 'list'
            ], cwd=terraform_dir, capture_output=True, text=True)
            
            if aws_result.returncode == 0:
                state_list = aws_result.stdout
                # Look for instance resources
                if 'aws_instance' in state_list or 'alicloud_instance' in state_list:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking deployment: {e}")
            return False
    
    def _get_terraform_outputs(self):
        """Get Terraform outputs"""
        try:
            import subprocess
            import os
            import json
            
            terraform_dir = os.path.join(os.path.dirname(__file__), '..', 'infra', 'terraform')
            terraform_dir = os.path.abspath(terraform_dir)
            
            result = subprocess.run([
                'terraform', 'output', '-json'
            ], cwd=terraform_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Failed to get Terraform outputs: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Terraform outputs: {e}")
            return None
    
    def _get_running_instance_count(self):
        """Get count of running instances"""
        try:
            terraform_outputs = self._get_terraform_outputs()
            if not terraform_outputs:
                return 0
            
            # Check AWS instances
            aws_lb = terraform_outputs.get('aws_endpoints', {}).get('load_balancer_dns')
            alibaba_lb = terraform_outputs.get('alibaba_endpoints', {}).get('load_balancer_dns')
            
            count = 0
            if aws_lb and aws_lb != "swen-ai-dev.amazonaws.com":
                count += 1
            if alibaba_lb and alibaba_lb != "swen-ai-dev.alibabacloud.com":
                count += 1
                
            return count
            
        except Exception as e:
            logger.error(f"Error getting instance count: {e}")
            return 0

def main():
    """Main function"""
    print("🎯 SWEN Complete Workflow Demo")
    print("=" * 40)
    print("This demo shows the complete AI-driven deployment workflow:")
    print("1. Send workload request")
    print("2. AI analyzes costs and chooses cheapest provider")
    print("3. AI asks for approval")
    print("4. User approves")
    print("5. AI deploys application to chosen provider")
    print()
    
    demo = SWENWorkflowDemo()
    
    try:
        success = demo.run_complete_workflow()
        if success:
            print("\n🎉 Demo completed successfully!")
        else:
            print("\n❌ Demo failed. Check the logs above.")
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")

if __name__ == "__main__":
    main()
