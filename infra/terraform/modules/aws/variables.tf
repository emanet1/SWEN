# AWS Module Variables

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "min_capacity" {
  description = "Minimum capacity for auto-scaling"
  type        = number
  default     = 0
}

variable "max_capacity" {
  description = "Maximum capacity for auto-scaling"
  type        = number
  default     = 10
}

variable "instance_types" {
  description = "Instance types for AI workloads"
  type        = list(string)
  default     = ["t3.medium", "t3.large", "t3.xlarge"]
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

variable "desired_capacity" {
  description = "Desired capacity for auto-scaling"
  type        = number
  default     = 1
}

variable "public_key" {
  description = "Public key for EC2 instances"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
