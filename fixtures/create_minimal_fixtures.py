#!/usr/bin/env python3
"""
Script para crear fixtures mínimos de ejemplo.
Ejecutar este script para generar datos de ejemplo para el demo.
"""

import json
import gzip
from pathlib import Path
from datetime import datetime

FIXTURES_DIR = Path("./fixtures")
RAW_DIR = FIXTURES_DIR / "raw"

# Crear estructura de directorios
RAW_DIR.mkdir(parents=True, exist_ok=True)

def create_fixture_file(service, region, operation, data, success=True, error=None):
    """Crear archivo fixture comprimido."""
    service_dir = RAW_DIR / service / region
    service_dir.mkdir(parents=True, exist_ok=True)
    
    output = {
        "metadata": {
            "service": service,
            "region": region,
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat(),
            "paginated": False,
            "success": success
        },
        "data": data,
        "error": error
    }
    
    filepath = service_dir / f"{operation}.json.gz"
    with gzip.open(filepath, 'wt', encoding='utf-8') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"Created: {filepath}")

# EC2 - DescribeInstances
create_fixture_file(
    "ec2", "us-east-1", "describe_instances",
    {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-1234567890abcdef0",
                        "InstanceType": "t3.medium",
                        "State": {"Name": "running"},
                        "VpcId": "vpc-12345678",
                        "SubnetId": "subnet-12345678",
                        "SecurityGroups": [{"GroupId": "sg-12345678"}],
                        "Tags": [{"Key": "Name", "Value": "web-server-1"}]
                    },
                    {
                        "InstanceId": "i-0987654321fedcba0",
                        "InstanceType": "t3.small",
                        "State": {"Name": "running"},
                        "VpcId": "vpc-12345678",
                        "SubnetId": "subnet-87654321",
                        "SecurityGroups": [{"GroupId": "sg-87654321"}],
                        "Tags": [{"Key": "Name", "Value": "app-server-1"}]
                    }
                ]
            }
        ]
    }
)

# EC2 - DescribeVpcs
create_fixture_file(
    "ec2", "us-east-1", "describe_vpcs",
    {
        "Vpcs": [
            {
                "VpcId": "vpc-12345678",
                "CidrBlock": "10.0.0.0/16",
                "State": "available",
                "Tags": [{"Key": "Name", "Value": "main-vpc"}]
            }
        ]
    }
)

# S3 - ListBuckets
create_fixture_file(
    "s3", "us-east-1", "list_buckets",
    {
        "Buckets": [
            {"Name": "my-app-bucket", "CreationDate": "2024-01-01T00:00:00Z"},
            {"Name": "backup-bucket", "CreationDate": "2024-01-02T00:00:00Z"}
        ],
        "Owner": {"DisplayName": "demo-account"}
    }
)

# S3 - GetBucketLocation (ejemplo de operación con parámetro)
create_fixture_file(
    "s3", "us-east-1", "get_bucket_location",
    {"LocationConstraint": "us-east-1"},
    success=True
)

# RDS - DescribeDBInstances
create_fixture_file(
    "rds", "us-east-1", "describe_db_instances",
    {
        "DBInstances": [
            {
                "DBInstanceIdentifier": "mydb-instance-1",
                "DBInstanceClass": "db.t3.medium",
                "Engine": "mysql",
                "EngineVersion": "8.0",
                "MultiAZ": False,
                "PubliclyAccessible": False,
                "StorageEncrypted": True,
                "BackupRetentionPeriod": 7
            }
        ]
    }
)

# Lambda - ListFunctions
create_fixture_file(
    "lambda", "us-east-1", "list_functions",
    {
        "Functions": [
            {
                "FunctionName": "my-function",
                "Runtime": "python3.9",
                "MemorySize": 256,
                "Timeout": 30,
                "LastModified": "2024-01-10T00:00:00Z"
            },
            {
                "FunctionName": "another-function",
                "Runtime": "nodejs18.x",
                "MemorySize": 512,
                "Timeout": 60,
                "LastModified": "2024-01-12T00:00:00Z"
            }
        ]
    }
)

# CloudWatch - DescribeAlarms
create_fixture_file(
    "cloudwatch", "us-east-1", "describe_alarms",
    {
        "MetricAlarms": [
            {
                "AlarmName": "HighCPUUtilization",
                "MetricName": "CPUUtilization",
                "Namespace": "AWS/EC2",
                "StateValue": "OK"
            }
        ]
    }
)

# IAM - ListUsers
create_fixture_file(
    "iam", "us-east-1", "list_users",
    {
        "Users": [
            {
                "UserName": "admin-user",
                "UserId": "AIDAEXAMPLE",
                "CreateDate": "2024-01-01T00:00:00Z"
            }
        ]
    }
)

# IAM - ListRoles
create_fixture_file(
    "iam", "us-east-1", "list_roles",
    {
        "Roles": [
            {
                "RoleName": "ECADRole",
                "RoleId": "AROAEXAMPLE",
                "Arn": "arn:aws:iam::123456789012:role/ECADRole",
                "CreateDate": "2024-01-01T00:00:00Z"
            }
        ]
    }
)

# Auto Scaling - DescribeAutoScalingGroups
create_fixture_file(
    "autoscaling", "us-east-1", "describe_auto_scaling_groups",
    {
        "AutoScalingGroups": [
            {
                "AutoScalingGroupName": "web-asg",
                "MinSize": 2,
                "MaxSize": 10,
                "DesiredCapacity": 4,
                "HealthCheckType": "ELB",
                "Instances": [
                    {"InstanceId": "i-1234567890abcdef0", "HealthStatus": "Healthy"},
                    {"InstanceId": "i-0987654321fedcba0", "HealthStatus": "Healthy"}
                ]
            }
        ]
    }
)

# CloudFormation - DescribeStacks
create_fixture_file(
    "cloudformation", "us-east-1", "describe_stacks",
    {
        "Stacks": [
            {
                "StackName": "my-stack",
                "StackStatus": "CREATE_COMPLETE",
                "CreationTime": "2024-01-01T00:00:00Z"
            }
        ]
    }
)

# Ejemplo de error (para demostrar manejo de errores)
create_fixture_file(
    "securityhub", "us-east-1", "describe_hub",
    None,
    success=False,
    error={
        "code": "InvalidAccessException",
        "message": "Security Hub is not enabled"
    }
)

print("\n✓ Fixtures mínimos creados exitosamente!")
print(f"Ubicación: {RAW_DIR}")
print("\nAhora puedes ejecutar: make demo")


