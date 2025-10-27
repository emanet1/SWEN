#!/usr/bin/env python3
"""
SWEN Cost Simulation Script
Simulates different cost scenarios to test AI decision making
"""

import requests
import json
import time

def simulate_cost_scenario(scenario_name, aws_cost, alibaba_cost):
    """Simulate a cost scenario"""
    print(f"\n💰 Simulating: {scenario_name}")
    print(f"   AWS Cost: ${aws_cost}/hour")
    print(f"   Alibaba Cost: ${alibaba_cost}/hour")
    
    cost_data = {
        "aws_cost": aws_cost,
        "alibaba_cost": alibaba_cost,
        "scenario": scenario_name
    }
    
    try:
        response = requests.post(
            "http://localhost:8080/api/costs/simulate",
            json=cost_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Cost scenario updated successfully")
            return True
        else:
            print(f"❌ Failed to update cost scenario: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating cost scenario: {e}")
        return False

def test_cost_scenarios():
    """Test different cost scenarios"""
    print("🧪 Testing Different Cost Scenarios")
    print("=" * 50)
    
    scenarios = [
        ("AWS Cheaper", 0.03, 0.50),  # AWS much cheaper
        ("AWS Slightly Cheaper", 0.04, 0.05),  # AWS slightly cheaper
        ("Equal Costs", 0.05, 0.05),  # Equal costs
        ("Alibaba Cheaper", 0.10, 0.03),  # Alibaba cheaper (but restricted)
        ("AWS Expensive", 0.60, 0.05),  # AWS expensive
    ]
    
    for scenario_name, aws_cost, alibaba_cost in scenarios:
        simulate_cost_scenario(scenario_name, aws_cost, alibaba_cost)
        time.sleep(2)  # Wait between scenarios
    
    print("\n✅ All cost scenarios tested!")
    print("   The AI will now use these costs for future decisions")

def get_current_costs():
    """Get current cost configuration"""
    print("📊 Current Cost Configuration")
    print("=" * 30)
    
    try:
        response = requests.get(
            "http://localhost:8080/api/costs",
            timeout=10
        )
        
        if response.status_code == 200:
            costs = response.json()
            print(f"   AWS Cost: ${costs.get('aws_cost', 'Unknown')}/hour")
            print(f"   Alibaba Cost: ${costs.get('alibaba_cost', 'Unknown')}/hour")
            print(f"   Last Updated: {costs.get('last_updated', 'Unknown')}")
        else:
            print(f"❌ Failed to get current costs: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting current costs: {e}")

def main():
    """Main function"""
    print("💰 SWEN Cost Simulation Test")
    print("=" * 40)
    
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
    
    # Get current costs
    get_current_costs()
    
    # Test different scenarios
    test_cost_scenarios()
    
    print("\n🎉 Cost simulation test completed!")
    print("\nNext Steps:")
    print("1. Send a workload request: python send_workload.py")
    print("2. Check the dashboard: http://localhost:3000")
    print("3. Observe AI decision making with different costs")

if __name__ == "__main__":
    main()
