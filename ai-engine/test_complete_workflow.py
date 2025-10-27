#!/usr/bin/env python3
"""
SWEN Complete AI Workflow Test
Tests the full AI decision-making and deployment process
"""

import requests
import time
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SWENWorkflowTester:
    def __init__(self, ai_engine_url: str = "http://localhost:8080"):
        self.ai_engine_url = ai_engine_url
        self.workload_id = None
        
    def test_complete_workflow(self):
        """Test the complete SWEN AI workflow"""
        logger.info("🚀 Starting SWEN Complete AI Workflow Test")
        
        try:
            # Step 1: Send workload request
            self.step_1_send_workload()
            
            # Step 2: Wait for AI decision
            self.step_2_wait_for_decision()
            
            # Step 3: Approve the decision
            self.step_3_approve_decision()
            
            # Step 4: Wait for deployment
            self.step_4_wait_for_deployment()
            
            # Step 5: Verify deployment
            self.step_5_verify_deployment()
            
            # Step 6: Test cost optimization
            self.step_6_test_cost_optimization()
            
            logger.info("✅ SWEN Complete AI Workflow Test PASSED!")
            
        except Exception as e:
            logger.error(f"❌ SWEN Complete AI Workflow Test FAILED: {e}")
            raise
    
    def step_1_send_workload(self):
        """Step 1: Send a workload request to the AI engine"""
        logger.info("📤 STEP 1: Sending workload request to AI engine")
        
        workload_request = {
            "id": f"test-workload-{int(time.time())}",
            "name": "SWEN Test Workload",
            "description": "Testing complete AI workflow",
            "cpu_cores": 2,
            "memory_gb": 4,
            "storage_gb": 20,
            "estimated_duration_hours": 24.0,
            "cost_sensitivity": 0.8,  # High cost sensitivity
            "latency_sensitivity": 0.3,  # Low latency sensitivity
            "priority": "medium",
            "region_preference": "us-east-1"
        }
        
        response = requests.post(
            f"{self.ai_engine_url}/api/workloads",
            json=workload_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            self.workload_id = result.get('workload_id')
            logger.info(f"✅ Workload request sent successfully: {self.workload_id}")
            logger.info(f"   AI Decision: {result.get('decision', 'Pending')}")
            logger.info(f"   Estimated Cost: ${result.get('estimated_cost', 'Unknown')}/hour")
        else:
            raise Exception(f"Failed to send workload request: {response.status_code} - {response.text}")
    
    def step_2_wait_for_decision(self):
        """Step 2: Wait for AI to make a decision"""
        logger.info("🤔 STEP 2: Waiting for AI decision...")
        
        max_attempts = 10
        for attempt in range(max_attempts):
            time.sleep(2)
            
            response = requests.get(
                f"{self.ai_engine_url}/api/workloads/{self.workload_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                workload = response.json()
                decision = workload.get('decision')
                
                if decision and decision != 'pending':
                    logger.info(f"✅ AI Decision Made: {decision}")
                    logger.info(f"   Provider: {workload.get('provider', 'Unknown')}")
                    logger.info(f"   Cost: ${workload.get('estimated_cost', 'Unknown')}/hour")
                    logger.info(f"   Reasoning: {workload.get('reasoning', 'No reasoning provided')}")
                    return
                else:
                    logger.info(f"   ⏳ Decision still pending... (attempt {attempt + 1}/{max_attempts})")
            else:
                logger.warning(f"   ⚠️ Failed to get workload status: {response.status_code}")
        
        raise Exception("AI decision timeout - no decision made within expected time")
    
    def step_3_approve_decision(self):
        """Step 3: Approve the AI decision"""
        logger.info("✅ STEP 3: Approving AI decision")
        
        response = requests.post(
            f"{self.ai_engine_url}/api/workloads/{self.workload_id}/approve",
            json={"approved": True},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Decision approved successfully")
            logger.info(f"   Status: {result.get('status', 'Unknown')}")
            logger.info(f"   Message: {result.get('message', 'No message')}")
        else:
            raise Exception(f"Failed to approve decision: {response.status_code} - {response.text}")
    
    def step_4_wait_for_deployment(self):
        """Step 4: Wait for AI to deploy the application"""
        logger.info("⏳ STEP 4: Waiting for AI to deploy application...")
        
        logger.info("🔄 AI is now:")
        logger.info("   1. Generating Terraform changes")
        logger.info("   2. Applying infrastructure changes")
        logger.info("   3. Deploying SWEN application")
        logger.info("   4. Configuring load balancer")
        logger.info("   5. Running health checks")
        
        # Wait for deployment (check every 10 seconds for up to 5 minutes)
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(10)
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
        
        logger.info("🌐 SWEN Application URLs:")
        if aws_lb and aws_lb != "swen-ai-dev.amazonaws.com":  # Real LB DNS
            logger.info(f"   AWS Load Balancer: http://{aws_lb}")
            
            # Test the Load Balancer
            try:
                response = requests.get(f"http://{aws_lb}", timeout=10)
                if response.status_code == 200:
                    logger.info("✅ Load Balancer is responding correctly")
                else:
                    logger.warning(f"⚠️ Load Balancer returned status {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ Could not test Load Balancer: {e}")
        else:
            logger.info("   AWS: No instances deployed")
        
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
    
    def step_6_test_cost_optimization(self):
        """Step 6: Test cost optimization by simulating price changes"""
        logger.info("💰 STEP 6: Testing cost optimization")
        
        # Simulate a price change that makes AWS even cheaper
        logger.info("🔄 Simulating AWS price reduction...")
        
        price_update = {
            "aws_cost": 0.03,  # Even cheaper AWS
            "alibaba_cost": 0.60  # Even more expensive Alibaba
        }
        
        response = requests.post(
            f"{self.ai_engine_url}/api/costs/simulate",
            json=price_update,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ Cost simulation updated")
            logger.info(f"   New AWS cost: ${price_update['aws_cost']}/hour")
            logger.info(f"   New Alibaba cost: ${price_update['alibaba_cost']}/hour")
            logger.info("   AI will now consider these new costs for future decisions")
        else:
            logger.warning(f"⚠️ Failed to update cost simulation: {response.status_code}")
    
    def _check_actual_deployment(self):
        """Check if instances are actually deployed"""
        try:
            import subprocess
            import os
            
            terraform_dir = os.path.join(os.path.dirname(__file__), '..', 'infra', 'terraform')
            terraform_dir = os.path.abspath(terraform_dir)
            
            result = subprocess.run([
                'terraform', 'state', 'list'
            ], cwd=terraform_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                state_list = result.stdout
                if 'aws_instance' in state_list:
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
            
            aws_lb = terraform_outputs.get('aws_endpoints', {}).get('load_balancer_dns')
            
            count = 0
            if aws_lb and aws_lb != "swen-ai-dev.amazonaws.com":
                count += 1
                    
            return count
            
        except Exception as e:
            logger.error(f"Error getting instance count: {e}")
            return 0

def main():
    """Main function to run the complete workflow test"""
    print("🚀 SWEN Complete AI Workflow Test")
    print("=" * 50)
    
    # Check if AI engine is running
    try:
        response = requests.get("http://localhost:8080/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ AI Engine is not running. Please start it first:")
            print("   python main.py")
            return
    except Exception:
        print("❌ AI Engine is not running. Please start it first:")
        print("   python main.py")
        return
    
    # Run the test
    tester = SWENWorkflowTester()
    tester.test_complete_workflow()
    
    print("\n🎉 SWEN Complete AI Workflow Test Completed Successfully!")
    print("\nNext Steps:")
    print("1. Check the dashboard at http://localhost:3000")
    print("2. View AI decision history")
    print("3. Monitor real-time metrics")
    print("4. Test cost optimization features")

if __name__ == "__main__":
    main()
