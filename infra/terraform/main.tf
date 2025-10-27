# SWEN Multi-Cloud Infrastructure
# Terraform configuration for AWS and Alibaba Cloud

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    alicloud = {
      source  = "aliyun/alicloud"
      version = "~> 1.200"
    }
  }
}

# AWS Provider Configuration
provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "SWEN-GitOps-AIOps"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Alibaba Cloud Provider Configuration (COMMENTED OUT - Not needed for now)
# provider "alicloud" {
#   region = var.alibaba_region
# }

# Local values for common configurations
locals {
  common_tags = {
    Project     = "SWEN-GitOps-AIOps"
    Environment = var.environment
    ManagedBy   = "Terraform"
    CreatedBy   = "AI-Routing-Engine"
  }
}

# AWS Infrastructure Module (Real Infrastructure Deployment)
module "aws_infrastructure" {
  source = "./modules/aws"
  
  environment = var.environment
  aws_region  = var.aws_region
  
  # REAL INFRASTRUCTURE: Deploy actual instances
  instance_types    = ["t3.medium"]  # Cost-effective instance type
  min_capacity      = 1            # Start with 1 instance
  max_capacity      = 3            # Allow scaling up to 3 instances
  desired_capacity  = 2            # Deploy 1 instance initially
  public_key        = var.public_key
  
  # Cost optimization settings
  enable_spot_instances = var.enable_spot_instances
  cost_optimization     = var.cost_optimization
  
  tags = local.common_tags
}

# Alibaba Cloud Infrastructure Module (COMMENTED OUT - Not needed for now)
# module "alibaba_infrastructure" {
#   source = "./modules/alibaba"
#   
#   environment = var.environment
#   alibaba_region = var.alibaba_region
#   
#   # REAL INFRASTRUCTURE: Deploy actual instances
#   instance_types    = ["ecs.n4.small"]  # Compatible with Alibaba Linux
#   min_capacity      = 1               # Start with 1 instance
#   max_capacity      = 3               # Allow scaling up to 3 instances
#   desired_capacity  = 0               # Disabled due to Alibaba risk control
#   public_key        = var.public_key
#   create_load_balancer = true         # Try to create Load Balancer
#   
#   # Cost optimization settings
#   enable_spot_instances = var.enable_spot_instances
#   cost_optimization     = var.cost_optimization
#   
#   tags = local.common_tags
# }

# Cross-cloud networking and monitoring (disabled - module not available)

# Output values for AI routing engine
output "aws_endpoints" {
  description = "AWS service endpoints for AI routing"
  value = {
    region        = var.aws_region
    vpc_id        = module.aws_infrastructure.vpc_id
    load_balancer_dns = module.aws_infrastructure.load_balancer_dns
    cost_per_hour = module.aws_infrastructure.estimated_cost_per_hour
  }
}

# Alibaba endpoints output (COMMENTED OUT - Not needed for now)
# output "alibaba_endpoints" {
#   description = "Alibaba Cloud service endpoints for AI routing"
#   value = {
#     region        = var.alibaba_region
#     vpc_id        = module.alibaba_infrastructure.vpc_id
#     load_balancer_dns = module.alibaba_infrastructure.load_balancer_dns
#     cost_per_hour = module.alibaba_infrastructure.estimated_cost_per_hour
#   }
# }

# Cross-cloud info output removed (module not available)
