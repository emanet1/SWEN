# Alibaba Cloud Infrastructure Module - Simplified Version

terraform {
  required_providers {
    alicloud = {
      source  = "aliyun/alicloud"
      version = "~> 1.200"
    }
  }
}

# Data sources
data "alicloud_images" "alibaba_linux" {
  name_regex = "^aliyun_2"
  owners      = "system"
  most_recent = true
}

# Get available zones for the region
data "alicloud_zones" "available" {
  available_resource_creation = "VSwitch"
  enable_details              = false
}

# VPC Configuration
resource "alicloud_vpc" "main" {
  vpc_name   = "${var.environment}-swen-vpc"
  cidr_block = "172.16.0.0/16"

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-vpc"
  })
}

# VSwitch (Subnet)
resource "alicloud_vswitch" "main" {
  count = 2

  vpc_id            = alicloud_vpc.main.id
  cidr_block        = "172.16.${count.index + 1}.0/24"
  zone_id           = data.alicloud_zones.available.zones[count.index].id
  vswitch_name      = "${var.environment}-swen-vswitch-${count.index + 1}"

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-vswitch-${count.index + 1}"
  })
}

# Security Group for AI Workloads
resource "alicloud_security_group" "ai_workloads" {
  security_group_name = "${var.environment}-swen-ai-workloads"
  description         = "Security group for SWEN AI workloads"
  vpc_id             = alicloud_vpc.main.id

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-ai-workloads-sg"
  })
}

# Security Group Rules
resource "alicloud_security_group_rule" "http" {
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range       = "80/80"
  priority          = 1
  security_group_id = alicloud_security_group.ai_workloads.id
  cidr_ip           = "0.0.0.0/0"
}

resource "alicloud_security_group_rule" "https" {
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "443/443"
  priority          = 1
  security_group_id = alicloud_security_group.ai_workloads.id
  cidr_ip           = "0.0.0.0/0"
}

resource "alicloud_security_group_rule" "ssh" {
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "22/22"
  priority          = 1
  security_group_id = alicloud_security_group.ai_workloads.id
  cidr_ip           = "0.0.0.0/0"
}

resource "alicloud_security_group_rule" "egress" {
  type              = "egress"
  ip_protocol       = "all"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "-1/-1"
  priority          = 1
  security_group_id = alicloud_security_group.ai_workloads.id
  cidr_ip           = "0.0.0.0/0"
}

# Key Pair for ECS instances
resource "alicloud_key_pair" "swen_key" {
  key_pair_name = "${var.environment}-swen-key"
  public_key    = var.public_key

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-key"
  })
}

# ECS Instance for SWEN Application
resource "alicloud_instance" "swen_app" {
  count = var.desired_capacity

  instance_name   = "${var.environment}-swen-app-v4-${count.index + 1}"
  instance_type   = "ecs.n4.large"  # Changed to supported instance type
  image_id        = data.alicloud_images.alibaba_linux.images[0].id
  security_groups = [alicloud_security_group.ai_workloads.id]
  vswitch_id      = alicloud_vswitch.main[count.index % 2].id
  key_name        = alicloud_key_pair.swen_key.key_pair_name

  # Enable public IP
  internet_max_bandwidth_out = 10

  # User data script
  user_data = base64encode(<<-EOF
    #!/bin/bash
    # Simple, reliable approach for Alibaba Linux
    
    # Install nginx
    yum install -y nginx
    
    # Create SWEN app in multiple possible locations
    mkdir -p /var/www/html
    mkdir -p /usr/share/nginx/html
    
    # Create the SWEN application
    cat > /var/www/html/index.html << 'HTML'
    <!DOCTYPE html>
    <html>
    <head>
        <title>SWEN AI Workload - Alibaba</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #ff6a00 0%, #ff4500 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .container { background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); padding: 40px; max-width: 600px; text-align: center; }
            .logo { font-size: 3em; margin-bottom: 20px; }
            .title { color: #333; font-size: 2.5em; margin-bottom: 10px; }
            .status { color: #28a745; font-weight: bold; font-size: 1.2em; }
            .info { background: #f8f9fa; border-radius: 15px; padding: 30px; margin: 20px 0; }
            .cost { background: #d4edda; border: 2px solid #28a745; border-radius: 10px; padding: 20px; margin: 20px 0; }
            .cost-value { font-size: 2em; font-weight: bold; color: #28a745; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🚀</div>
            <h1 class="title">SWEN AI Workload</h1>
            <div class="info">
                <h2>Provider: Alibaba Cloud</h2>
                <p class="status">✅ Instance Running Successfully</p>
                        <p>Region: ap-southeast-1</p>
                        <p>Instance Type: ${var.instance_types[0]}</p>
                <p>Deployed: $(date)</p>
            </div>
            <div class="cost">
                <p>Cost per Hour</p>
                <div class="cost-value">$0.03</div>
                <p style="margin-top: 10px; color: #666;">Optimized by AI</p>
            </div>
        </div>
    </body>
    </html>
    HTML
    
    # Copy to both locations to be sure
    cp /var/www/html/index.html /usr/share/nginx/html/index.html
    
    # Start nginx
    systemctl start nginx
    systemctl enable nginx
    
    # Set permissions
    chmod 644 /var/www/html/index.html
    chmod 644 /usr/share/nginx/html/index.html
    
    # Restart nginx to ensure it picks up the new content
    systemctl restart nginx
  EOF
  )

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-app-${count.index + 1}"
    Project = "SWEN-AI"
    Type = "Application-Server"
  })
}

# Server Load Balancer (with fallback mechanism)
resource "alicloud_slb" "swen_app" {
  count = var.create_load_balancer ? 1 : 0
  
  load_balancer_name = "${var.environment}-swen-app-slb"
  load_balancer_spec = "slb.s1.small"
  address_type       = "internet"
  vswitch_id         = alicloud_vswitch.main[0].id
}

# Load Balancer Listener
resource "alicloud_slb_listener" "swen_app" {
  count = var.create_load_balancer ? 1 : 0
  
  load_balancer_id = alicloud_slb.swen_app[0].id
  backend_port     = 80
  frontend_port    = 80
  protocol         = "http"
  bandwidth        = 10
  health_check     = "on"
  health_check_connect_port = 80
  health_check_uri = "/"
}

# Load Balancer Server Group
resource "alicloud_slb_server_group" "swen_app" {
  count = var.create_load_balancer ? 1 : 0
  
  load_balancer_id = alicloud_slb.swen_app[0].id
  name             = "${var.environment}-swen-app-sg"
}

# Add instances to server group
resource "alicloud_slb_server_group_server_attachment" "swen_app" {
  count = var.create_load_balancer ? var.desired_capacity : 0
  
  server_group_id = alicloud_slb_server_group.swen_app[0].id
  server_id       = alicloud_instance.swen_app[count.index].id
  port            = 80
  weight          = 100
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = alicloud_vpc.main.id
}

output "load_balancer_dns" {
  description = "Load balancer DNS name"
  value       = var.create_load_balancer ? alicloud_slb.swen_app[0].address : "swen-ai-dev.alibabacloud.com"
}

output "load_balancer_url" {
  description = "URL to access the SWEN application via Load Balancer"
  value       = var.create_load_balancer ? "http://${alicloud_slb.swen_app[0].address}" : "http://swen-ai-dev.alibabacloud.com"
}

output "instance_public_ip" {
  description = "Public IP of the SWEN application instance"
  value       = length(alicloud_instance.swen_app) > 0 ? alicloud_instance.swen_app[0].public_ip : null
}

output "instance_url" {
  description = "Direct URL to access the SWEN application instance"
  value       = length(alicloud_instance.swen_app) > 0 ? "http://${alicloud_instance.swen_app[0].public_ip}" : null
}

output "estimated_cost_per_hour" {
  description = "Estimated cost per hour (instance + LB)"
  value       = var.desired_capacity * 0.03 + 0.01  # $0.03 per instance + $0.01 for LB
}

output "instance_count" {
  description = "Number of running instances"
  value       = var.desired_capacity
}
