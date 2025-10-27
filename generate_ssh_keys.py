#!/usr/bin/env python3
"""
SSH Key Generator for SWEN Multi-Cloud Deployment
Generates SSH key pairs for AWS EC2 and Alibaba ECS instances
"""

import os
import subprocess
import sys
from pathlib import Path

def generate_ssh_key_pair(key_name="swen-key"):
    """Generate SSH key pair for cloud instances"""
    
    # Create keys directory
    keys_dir = Path("keys")
    keys_dir.mkdir(exist_ok=True)
    
    private_key_path = keys_dir / f"{key_name}"
    public_key_path = keys_dir / f"{key_name}.pub"
    
    print(f"🔑 Generating SSH key pair: {key_name}")
    print(f"📁 Private key: {private_key_path}")
    print(f"📁 Public key: {public_key_path}")
    
    # Generate SSH key pair
    try:
        subprocess.run([
            "ssh-keygen", 
            "-t", "rsa", 
            "-b", "4096",
            "-f", str(private_key_path),
            "-N", "",  # No passphrase
            "-C", f"swen-{key_name}@swen-ai.com"
        ], check=True)
        
        print("✅ SSH key pair generated successfully!")
        
        # Read the public key
        with open(public_key_path, 'r') as f:
            public_key = f.read().strip()
        
        print(f"\n📋 Public Key Content:")
        print("=" * 60)
        print(public_key)
        print("=" * 60)
        
        print(f"\n🔧 Next Steps:")
        print(f"1. Copy the public key above")
        print(f"2. Set it in your .env file:")
        print(f"   PUBLIC_KEY='{public_key}'")
        print(f"3. Or pass it to Terraform:")
        print(f"   terraform apply -var='public_key={public_key}'")
        
        return public_key
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating SSH key: {e}")
        return None
    except FileNotFoundError:
        print("❌ ssh-keygen not found. Please install OpenSSH:")
        print("   Windows: Install OpenSSH Client")
        print("   macOS: brew install openssh")
        print("   Linux: sudo apt-get install openssh-client")
        return None

def main():
    print("🚀 SWEN SSH Key Generator")
    print("=" * 40)
    
    # Check if keys already exist
    keys_dir = Path("keys")
    if keys_dir.exists():
        existing_keys = list(keys_dir.glob("swen-key*"))
        if existing_keys:
            print(f"⚠️  Found existing keys: {existing_keys}")
            response = input("Do you want to regenerate? (y/N): ").lower()
            if response != 'y':
                print("Using existing keys...")
                public_key_path = keys_dir / "swen-key.pub"
                if public_key_path.exists():
                    with open(public_key_path, 'r') as f:
                        public_key = f.read().strip()
                    print(f"\n📋 Existing Public Key:")
                    print("=" * 60)
                    print(public_key)
                    print("=" * 60)
                return
    
    # Generate new key pair
    public_key = generate_ssh_key_pair()
    
    if public_key:
        print(f"\n🎯 Key Management Summary:")
        print(f"✅ AWS EC2: Uses key pair '{public_key.split()[-1]}'")
        print(f"✅ Alibaba ECS: Uses key pair '{public_key.split()[-1]}'")
        print(f"✅ Both clouds use the same SSH key for consistency")
        
        print(f"\n🔐 Security Notes:")
        print(f"• Private key: keys/swen-key (keep secure!)")
        print(f"• Public key: keys/swen-key.pub (safe to share)")
        print(f"• Both clouds will use the same key for easy access")

if __name__ == "__main__":
    main()
