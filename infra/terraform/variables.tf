# SWEN Multi-Cloud Infrastructure Variables

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "public_key" {
  description = "Public key for EC2/ECS instances"
  type        = string
  default     = ""
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "alibaba_region" {
  description = "Alibaba Cloud region"
  type        = string
  default     = "ap-southeast-1"  # Singapore region - more reliable
}

variable "aws_instance_types" {
  description = "AWS instance types for AI workloads"
  type        = list(string)
  default     = ["t3.medium", "t3.large", "t3.xlarge"]
}

variable "alibaba_instance_types" {
  description = "Alibaba Cloud instance types for AI workloads"
  type        = list(string)
  default     = ["ecs.c6.large", "ecs.c6.xlarge", "ecs.c6.2xlarge"]
}

variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = true
}

variable "cost_optimization" {
  description = "Enable cost optimization features"
  type        = bool
  default     = true
}
