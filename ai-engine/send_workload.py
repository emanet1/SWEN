#!/usr/bin/env python3
"""
Simple SWEN Workload Request Script
Sends a workload request to the AI engine for testing
"""

import requests
import json
import time

def send_workload_request():
    """Send a simple workload request to the AI engine"""
    
    # Workload request data
    workload = {
        "id": f"test-workload-{int(time.time())}",
        "name": "SWEN Test Workload",
        "description": "Testing AI decision making",
        "cpu_cores": 2,
        "memory_gb": 4,
        "storage_gb": 20,
        "estimated_duration_hours": 24.0,
        "cost_sensitivity": 0.8,  # High cost sensitivity (80%)
        "latency_sensitivity": 0.3,  # Low latency sensitivity (30%)
        "priority": "medium",
        "region_preference": "us-east-1"
    }
    
    print("🚀 Sending workload request to AI engine...")
    print(f"   Workload ID: {workload['id']}")
    print(f"   CPU Cores: {workload['cpu_cores']}")
    print(f"   Memory: {workload['memory_gb']} GB")
    print(f"   Cost Sensitivity: {workload['cost_sensitivity']*100}%")
    print(f"   Latency Sensitivity: {workload['latency_sensitivity']*100}%")
    
    try:
        # Send request to AI engine
        response = requests.post(
            "http://localhost:8080/api/workloads",
            json=workload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Workload request sent successfully!")
            print(f"   AI Decision: {result.get('decision', 'Pending')}")
            print(f"   Provider: {result.get('provider', 'Unknown')}")
            print(f"   Estimated Cost: ${result.get('estimated_cost', 'Unknown')}/hour")
            print(f"   Reasoning: {result.get('reasoning', 'No reasoning provided')}")
            
            if result.get('requires_approval'):
                print(f"\n🔔 Approval Required!")
                print(f"   Workload ID: {result.get('workload_id')}")
                print(f"   Go to dashboard to approve: http://localhost:3000/approval")
                print(f"   Or approve via API: POST /api/workloads/{result.get('workload_id')}/approve")
            
            return result.get('workload_id')
        else:
            print(f"❌ Failed to send workload request: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to AI engine. Make sure it's running:")
        print("   python main.py")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def approve_workload(workload_id):
    """Approve a workload request"""
    print(f"\n✅ Approving workload {workload_id}...")
    
    try:
        response = requests.post(
            f"http://localhost:8080/api/workloads/{workload_id}/approve",
            json={"approved": True},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Workload approved successfully!")
            print(f"   Status: {result.get('status', 'Unknown')}")
            print(f"   Message: {result.get('message', 'No message')}")
            return True
        else:
            print(f"❌ Failed to approve workload: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error approving workload: {e}")
        return False

def main():
    """Main function"""
    print("🚀 SWEN Workload Request Test")
    print("=" * 40)
    
    # Send workload request
    workload_id = send_workload_request()
    
    if workload_id:
        print(f"\n⏳ Waiting 5 seconds before approval...")
        time.sleep(5)
        
        # Approve the workload
        approve_workload(workload_id)
        
        print(f"\n🎉 Workflow completed!")
        print(f"   Check the dashboard: http://localhost:3000")
        print(f"   Check Load Balancer: http://dev-swen-app-elb-685466146.us-east-1.elb.amazonaws.com")

if __name__ == "__main__":
    main()
