# SWEN AI System Startup Script
# PowerShell version with Terraform cleanup functionality

param(
    [switch]$SkipTerraformCheck,
    [switch]$ForceCleanup,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
SWEN AI System Startup Script

Usage: .\start_swen.ps1 [options]

Options:
    -SkipTerraformCheck    Skip checking for costly Terraform infrastructure
    -ForceCleanup         Force cleanup of all Terraform resources
    -Help                 Show this help message

Examples:
    .\start_swen.ps1                    # Normal startup with Terraform check
    .\start_swen.ps1 -SkipTerraformCheck # Skip Terraform check
    .\start_swen.ps1 -ForceCleanup      # Clean up all resources first
"@
    exit 0
}

Write-Host "Starting SWEN AI System..." -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host ".env file not found!" -ForegroundColor Red
    Write-Host "Please copy env.template to .env and configure your credentials" -ForegroundColor Yellow
    exit 1
}

# Function to check if a port is in use
function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    }
    catch {
        return $false
    }
}

# Function to check Terraform infrastructure costs
function Test-TerraformCosts {
    Write-Host "Checking Terraform infrastructure costs..." -ForegroundColor Yellow
    
    if (-not (Test-Path "infra\terraform")) {
        Write-Host "No Terraform directory found" -ForegroundColor Green
        return $false
    }
    
    Set-Location "infra\terraform"
    
    try {
        # Check if Terraform is initialized
        if (-not (Test-Path ".terraform")) {
            Write-Host "Terraform not initialized - no infrastructure deployed" -ForegroundColor Green
            Set-Location "..\.."
            return $false
        }
        
        # Get Terraform state
        $terraformState = terraform show -json 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Could not read Terraform state" -ForegroundColor Yellow
            Set-Location "..\.."
            return $false
        }
        
        $state = $terraformState | ConvertFrom-Json
        
        # Check for costly resources
        $costlyResources = @()
        $totalEstimatedCost = 0
        
        foreach ($resource in $state.values.root_module.resources) {
            $resourceType = $resource.type
            $resourceName = $resource.name
            
            # Check for EC2 instances
            if ($resourceType -eq "aws_instance") {
                $instanceType = $resource.values.instance_type
                $costlyResources += "EC2 Instance ($instanceType)"
                
                # Estimate cost based on instance type
                switch ($instanceType) {
                    "t3.micro" { $totalEstimatedCost += 0.0104 }
                    "t3.small" { $totalEstimatedCost += 0.0208 }
                    "t3.medium" { $totalEstimatedCost += 0.0416 }
                    "t3.large" { $totalEstimatedCost += 0.0832 }
                    "t3.xlarge" { $totalEstimatedCost += 0.1664 }
                    default { $totalEstimatedCost += 0.05 }
                }
            }
            
            # Check for Load Balancers
            if ($resourceType -eq "aws_elb" -or $resourceType -eq "aws_lb") {
                $costlyResources += "Load Balancer"
                $totalEstimatedCost += 0.0225
            }
            
            # Check for RDS instances
            if ($resourceType -eq "aws_db_instance") {
                $costlyResources += "RDS Database"
                $totalEstimatedCost += 0.1
            }
        }
        
        Set-Location "..\.."
        
        if ($costlyResources.Count -gt 0) {
            Write-Host "Costly infrastructure detected:" -ForegroundColor Yellow
            foreach ($resource in $costlyResources) {
                Write-Host "   - $resource" -ForegroundColor Yellow
            }
            Write-Host "   Estimated cost: `$$($totalEstimatedCost.ToString('F4'))/hour" -ForegroundColor Yellow
            
            if ($ForceCleanup) {
                Write-Host "Force cleanup requested - destroying infrastructure..." -ForegroundColor Red
                return $true
            }
            
            $response = Read-Host "Do you want to destroy this infrastructure to avoid costs? (y/N)"
            if ($response -eq "y" -or $response -eq "Y") {
                return $true
            } else {
                Write-Host "Continuing with existing infrastructure..." -ForegroundColor Yellow
                return $false
            }
        } else {
            Write-Host "No costly infrastructure detected" -ForegroundColor Green
            return $false
        }
    }
    catch {
        Write-Host "Error checking Terraform state: $($_.Exception.Message)" -ForegroundColor Yellow
        Set-Location "..\.."
        return $false
    }
}

# Function to destroy Terraform infrastructure
function Remove-TerraformInfrastructure {
    Write-Host "Destroying Terraform infrastructure..." -ForegroundColor Red
    
    Set-Location "infra\terraform"
    
    try {
        # Show what will be destroyed
        Write-Host "Planning destruction..." -ForegroundColor Yellow
        terraform plan -destroy
        
        $confirm = Read-Host "Are you sure you want to destroy all infrastructure? (yes/NO)"
        if ($confirm -eq "yes") {
            Write-Host "Destroying infrastructure..." -ForegroundColor Red
            terraform destroy -auto-approve
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Infrastructure destroyed successfully" -ForegroundColor Green
            } else {
                Write-Host "Error destroying infrastructure" -ForegroundColor Red
            }
        } else {
            Write-Host "Destruction cancelled" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "Error during destruction: $($_.Exception.Message)" -ForegroundColor Red
    }
    finally {
        Set-Location "..\.."
    }
}

# Check Terraform costs unless skipped
if (-not $SkipTerraformCheck) {
    $shouldDestroy = Test-TerraformCosts
    if ($shouldDestroy) {
        Remove-TerraformInfrastructure
    }
}

# Check required ports
Write-Host "Checking ports..." -ForegroundColor Yellow
if (Test-Port 3000) {
    Write-Host "Port 3000 is already in use" -ForegroundColor Red
    Write-Host "Please stop the service using port 3000 or use a different port" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "Port 3000 is available" -ForegroundColor Green
}

if (Test-Port 8080) {
    Write-Host "Port 8080 is already in use" -ForegroundColor Red
    Write-Host "Please stop the service using port 8080 or use a different port" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "Port 8080 is available" -ForegroundColor Green
}

# Check Python dependencies
Write-Host "Checking Python dependencies..." -ForegroundColor Yellow
Set-Location "ai-engine"
try {
    python -c "import flask, requests, sklearn, numpy, boto3" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
        pip install -r requirements.txt
    } else {
        Write-Host "Python dependencies are installed" -ForegroundColor Green
    }
}
catch {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Start AI Engine
Write-Host "Starting AI Engine..." -ForegroundColor Yellow
Write-Host "   Port: 8080" -ForegroundColor Cyan
Write-Host "   API Endpoints: /health, /telemetry, /workloads, /workload" -ForegroundColor Cyan
Write-Host "   Real AWS Data: Enabled" -ForegroundColor Cyan
Write-Host "   Flask Web Server: Enabled" -ForegroundColor Cyan
Write-Host ""

# Start AI Engine in background
$aiProcess = Start-Process -FilePath "python" -ArgumentList "main.py" -PassThru -WindowStyle Normal

# Wait for AI Engine to start
Write-Host "Waiting for AI Engine to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test AI Engine health
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8080/health" -Method GET -TimeoutSec 10
    if ($healthResponse.status -eq "healthy") {
        Write-Host "AI Engine is healthy and running" -ForegroundColor Green
    } else {
        Write-Host "AI Engine started but health check failed" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "AI Engine may not be fully ready yet" -ForegroundColor Yellow
}

# Start Dashboard
Write-Host "Starting Dashboard..." -ForegroundColor Yellow
Set-Location "..\dashboard"

# Check Node.js dependencies
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
    npm install
}

# Start Dashboard in background
$dashboardProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -PassThru -WindowStyle Normal

# Wait for Dashboard to start
Write-Host "Waiting for Dashboard to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test Dashboard
try {
    $dashboardResponse = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 10
    if ($dashboardResponse.StatusCode -eq 200) {
        Write-Host "Dashboard is running" -ForegroundColor Green
    }
}
catch {
    Write-Host "Dashboard may not be fully ready yet" -ForegroundColor Yellow
}

Set-Location ".."

Write-Host ""
Write-Host "SWEN AI System Started Successfully!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "AI Engine: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Endpoints:" -ForegroundColor Cyan
Write-Host "  Health: http://localhost:8080/health" -ForegroundColor White
Write-Host "  Telemetry: http://localhost:8080/telemetry" -ForegroundColor White
Write-Host "  Workloads: http://localhost:8080/workloads" -ForegroundColor White
Write-Host "  Submit Workload: POST http://localhost:8080/workload" -ForegroundColor White
Write-Host ""
Write-Host "Process IDs:" -ForegroundColor Cyan
Write-Host "  AI Engine PID: $($aiProcess.Id)" -ForegroundColor White
Write-Host "  Dashboard PID: $($dashboardProcess.Id)" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow

# Function to cleanup on exit
function Stop-SWENSystem {
    Write-Host ""
    Write-Host "Stopping SWEN AI System..." -ForegroundColor Red
    
    try {
        if ($aiProcess -and !$aiProcess.HasExited) {
            Stop-Process -Id $aiProcess.Id -Force
            Write-Host "AI Engine stopped" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "Error stopping AI Engine" -ForegroundColor Yellow
    }
    
    try {
        if ($dashboardProcess -and !$dashboardProcess.HasExited) {
            Stop-Process -Id $dashboardProcess.Id -Force
            Write-Host "Dashboard stopped" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "Error stopping Dashboard" -ForegroundColor Yellow
    }
    
    Write-Host "All services stopped" -ForegroundColor Green
    exit 0
}

# Set trap for cleanup
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Stop-SWENSystem }

# Wait for user to stop
Write-Host "System is running... Press Ctrl+C to stop" -ForegroundColor Green
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
catch {
    Stop-SWENSystem
}