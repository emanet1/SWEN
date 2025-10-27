# SWEN Terraform Cleanup Script
# Safely destroys costly infrastructure

param(
    [switch]$Force,
    [switch]$DryRun,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
SWEN Terraform Cleanup Script

Usage: .\cleanup_terraform.ps1 [options]

Options:
    -Force      Skip confirmation prompts
    -DryRun     Show what would be destroyed without actually destroying
    -Help       Show this help message

Examples:
    .\cleanup_terraform.ps1              # Interactive cleanup
    .\cleanup_terraform.ps1 -DryRun      # See what would be destroyed
    .\cleanup_terraform.ps1 -Force       # Force cleanup without prompts
"@
    exit 0
}

Write-Host "SWEN Terraform Cleanup Script" -ForegroundColor Red
Write-Host "================================" -ForegroundColor Red

# Check if Terraform directory exists
if (-not (Test-Path "infra\terraform")) {
    Write-Host "No Terraform directory found" -ForegroundColor Red
    Write-Host "Nothing to clean up!" -ForegroundColor Green
    exit 0
}

Set-Location "infra\terraform"

# Check if Terraform is initialized
if (-not (Test-Path ".terraform")) {
    Write-Host "Terraform not initialized - no infrastructure deployed" -ForegroundColor Green
    Set-Location "..\.."
    exit 0
}

try {
    # Get Terraform state
    Write-Host "Analyzing Terraform state..." -ForegroundColor Yellow
    $terraformState = terraform show -json 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Could not read Terraform state" -ForegroundColor Red
        Set-Location "..\.."
        exit 1
    }
    
    $state = $terraformState | ConvertFrom-Json
    
    # Analyze resources
    $costlyResources = @()
    $totalEstimatedCost = 0
    $resourceCount = 0
    
    # Check root module resources
    foreach ($resource in $state.values.root_module.resources) {
        $resourceType = $resource.type
        $resourceName = $resource.name
        $resourceCount++
        
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
        
        # Check for EBS volumes
        if ($resourceType -eq "aws_ebs_volume") {
            $costlyResources += "EBS Volume"
            $totalEstimatedCost += 0.01
        }
    }
    
    # Check child module resources (where most resources are)
    foreach ($childModule in $state.values.root_module.child_modules) {
        foreach ($resource in $childModule.resources) {
            $resourceType = $resource.type
            $resourceName = $resource.name
            $resourceCount++
            
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
                $costlyResources += "AWS Load Balancer"
                $totalEstimatedCost += 0.0225
            }
            
            # Check for Alibaba Load Balancers
            if ($resourceType -eq "alicloud_slb") {
                $costlyResources += "Alibaba Load Balancer"
                $totalEstimatedCost += 0.01
            }
            
            # Check for RDS instances
            if ($resourceType -eq "aws_db_instance") {
                $costlyResources += "RDS Database"
                $totalEstimatedCost += 0.1
            }
            
            # Check for EBS volumes
            if ($resourceType -eq "aws_ebs_volume") {
                $costlyResources += "EBS Volume"
                $totalEstimatedCost += 0.01
            }
        }
    }
    
    Write-Host "Infrastructure Analysis:" -ForegroundColor Cyan
    Write-Host "   Total Resources: $resourceCount" -ForegroundColor White
    Write-Host "   Costly Resources: $($costlyResources.Count)" -ForegroundColor White
    Write-Host "   Estimated Cost: `$$($totalEstimatedCost.ToString('F4'))/hour" -ForegroundColor White
    
    if ($costlyResources.Count -gt 0) {
        Write-Host ""
        Write-Host "Costly Resources Found:" -ForegroundColor Yellow
        foreach ($resource in $costlyResources) {
            Write-Host "   - $resource" -ForegroundColor Yellow
        }
        
        if ($DryRun) {
            Write-Host ""
            Write-Host "DRY RUN - No resources will be destroyed" -ForegroundColor Green
            Write-Host "To actually destroy, run without -DryRun flag" -ForegroundColor Green
            Set-Location "..\.."
            exit 0
        }
        
        Write-Host ""
        Write-Host "WARNING: This will destroy ALL infrastructure!" -ForegroundColor Red
        Write-Host "   Estimated savings: `$$($totalEstimatedCost.ToString('F4'))/hour" -ForegroundColor Green
        
        if (-not $Force) {
            $confirm = Read-Host "Are you sure you want to destroy all infrastructure? (yes/NO)"
            if ($confirm -ne "yes") {
                Write-Host "Cleanup cancelled" -ForegroundColor Yellow
                Set-Location "..\.."
                exit 0
            }
        }
        
        # Show destruction plan
        Write-Host ""
        Write-Host "Destruction Plan:" -ForegroundColor Yellow
        terraform plan -destroy
        
        if (-not $Force) {
            $finalConfirm = Read-Host "Proceed with destruction? (yes/NO)"
            if ($finalConfirm -ne "yes") {
                Write-Host "Destruction cancelled" -ForegroundColor Yellow
                Set-Location "..\.."
                exit 0
            }
        }
        
        # Destroy infrastructure
        Write-Host ""
        Write-Host "Destroying infrastructure..." -ForegroundColor Red
        terraform destroy -auto-approve
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "Infrastructure destroyed successfully!" -ForegroundColor Green
            Write-Host "Estimated savings: `$$($totalEstimatedCost.ToString('F4'))/hour" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "Error destroying infrastructure" -ForegroundColor Red
            Set-Location "..\.."
            exit 1
        }
    } else {
        Write-Host ""
        Write-Host "No costly infrastructure found" -ForegroundColor Green
        Write-Host "Nothing to clean up!" -ForegroundColor Green
    }
}
catch {
    Write-Host "Error during cleanup: $($_.Exception.Message)" -ForegroundColor Red
    Set-Location "..\.."
    exit 1
}
finally {
    Set-Location "..\.."
}

Write-Host ""
Write-Host "Cleanup completed!" -ForegroundColor Green