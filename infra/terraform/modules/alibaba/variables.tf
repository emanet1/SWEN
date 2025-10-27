# Alibaba Cloud Module Variables

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "alibaba_region" {
  description = "Alibaba Cloud region"
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
  default     = ["ecs.n4.small", "ecs.n4.medium", "ecs.n4.large"]
}

variable "create_load_balancer" {
  description = "Whether to create a load balancer"
  type        = bool
  default     = true
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
  description = "Public key for ECS instances"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
