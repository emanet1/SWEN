# AWS Infrastructure Module - Simplified Version

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-vpc"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-igw"
  })
}

# Public Subnet
resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-public-${count.index + 1}"
  })
}

# Private Subnet
resource "aws_subnet" "private" {
  count = 2

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-private-${count.index + 1}"
  })
}

# Route Table for Public Subnet
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-public-rt"
  })
}

# Route Table Association for Public Subnet
resource "aws_route_table_association" "public" {
  count = 2

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Security Group for AI Workloads
resource "aws_security_group" "ai_workloads" {
  name_prefix = "${var.environment}-swen-ai-workloads"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-ai-workloads-sg"
  })
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

# Key Pair for EC2 instances
resource "aws_key_pair" "swen_key" {
  key_name   = "${var.environment}-swen-key"
  public_key = var.public_key

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-key"
  })
}

# EC2 Instance for SWEN Application
resource "aws_instance" "swen_app" {
  count = var.desired_capacity

  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_types[0]
  subnet_id      = aws_subnet.public[count.index % 2].id
  security_groups = [aws_security_group.ai_workloads.id]
  key_name      = aws_key_pair.swen_key.key_name

  # Enable public IP
  associate_public_ip_address = true

  user_data = base64encode(<<-EOF
    #!/bin/bash
    set -e  # Exit on any error
    set -x  # Debug mode
    
    # Log everything
    exec > >(tee /var/log/user-data.log) 2>&1
    echo "Starting AWS user data script..."
    
    # Install nginx using amazon-linux-extras (correct for Amazon Linux 2)
    amazon-linux-extras install -y nginx1
    echo "Nginx installed successfully"
    
    # Start nginx
    systemctl start nginx
    systemctl enable nginx
    echo "Nginx started and enabled"
    
    # Create the SWEN application (Amazon Linux 2 uses /usr/share/nginx/html)
    cat > /usr/share/nginx/html/index.html << 'HTML'
    <!DOCTYPE html>
    <html>
    <head>
        <title>SWEN AI Workload - AWS</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #ff9900 0%, #ff6600 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
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
                <h2>Provider: AWS</h2>
                <p class="status">✅ Instance Running Successfully</p>
                <p>Region: us-east-1</p>
                        <p>Instance Type: ${var.instance_types[0]}</p>
                <p>Deployed: $(date)</p>
            </div>
            <div class="cost">
                <p>Cost per Hour</p>
                <div class="cost-value">$0.05</div>
                <p style="margin-top: 10px; color: #666;">Optimized by AI</p>
            </div>
        </div>
    </body>
    </html>
    HTML
    
    # Set proper permissions
    chown -R nginx:nginx /usr/share/nginx/html/
    chmod -R 755 /usr/share/nginx/html/
    
    # Restart nginx to ensure it picks up the new content
    systemctl restart nginx
    echo "Nginx restarted with new content"
    
    echo "AWS user data script completed successfully!"
  EOF
  )

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-app-v3-${count.index + 1}"
    Project = "SWEN-AI"
    Type = "Application-Server"
  })
}

# Classic Load Balancer (more permissive)
resource "aws_elb" "swen_app" {
  name               = "${var.environment}-swen-app-elb"
  security_groups    = [aws_security_group.ai_workloads.id]
  subnets            = aws_subnet.public[*].id

  listener {
    instance_port     = 80
    instance_protocol = "http"
    lb_port           = 80
    lb_protocol       = "http"
  }

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    target              = "HTTP:80/"
    interval            = 30
  }

  instances                   = aws_instance.swen_app[*].id
  cross_zone_load_balancing   = true
  idle_timeout                = 400
  connection_draining         = true
  connection_draining_timeout = 400

  tags = merge(var.tags, {
    Name = "${var.environment}-swen-app-elb"
  })
}

# Classic Load Balancer doesn't need target groups - instances are attached directly

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "load_balancer_dns" {
  description = "Load balancer DNS name"
  value       = aws_elb.swen_app.dns_name
}

output "load_balancer_url" {
  description = "URL to access the SWEN application via Load Balancer"
  value       = "http://${aws_elb.swen_app.dns_name}"
}

output "instance_public_ip" {
  description = "Public IP of the SWEN application instance"
  value       = length(aws_instance.swen_app) > 0 ? aws_instance.swen_app[0].public_ip : null
}

output "instance_url" {
  description = "Direct URL to access the SWEN application instance"
  value       = length(aws_instance.swen_app) > 0 ? "http://${aws_instance.swen_app[0].public_ip}" : null
}

output "estimated_cost_per_hour" {
  description = "Estimated cost per hour (instance + LB)"
  value       = var.desired_capacity * 0.05 + 0.02  # $0.05 per instance + $0.02 for LB
}

output "instance_count" {
  description = "Number of running instances"
  value       = var.desired_capacity
}
