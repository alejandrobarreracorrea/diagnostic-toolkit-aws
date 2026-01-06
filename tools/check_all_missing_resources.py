#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar todos los recursos faltantes del inventario.
"""

import json
import sys
from pathlib import Path

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent

def find_latest_run():
    """Encontrar el run más reciente."""
    runs_dir = project_root / "runs"
    if not runs_dir.exists():
        return None
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    return runs[0] if runs else None

def main():
    print("="*80)
    print("🔍 VERIFICACIÓN DE TODOS LOS RECURSOS FALTANTES")
    print("="*80)
    
    # Valores esperados de AWS Config
    expected = {
        'Backup::BackupPlan': 5,
        'AppConfig::DeploymentStrategy': 4,
        'Cassandra::Keyspace': 4,
        'EC2::EC2Fleet': 4,
        'EC2::RouteTable': 4,
        'EC2::Subnet': 4,
        'EC2::SubnetRouteTableAssociation': 4,
        'RDS::DBInstance': 4,
        'EC2::LaunchTemplate': 3,
        'EC2::NetworkAcl': 3,
        'EC2::NetworkInsightsPath': 3,
        'EC2::TransitGatewayRouteTable': 3,
        'RDS::DBCluster': 3,
        'RDS::DBSubnetGroup': 3,
        'RDS::OptionGroup': 3,
        'SecretsManager::Secret': 3,
        'AutoScaling::AutoScalingGroup': 2,
        'Config::ConfigurationRecorder': 2,
        'EC2::VPNConnection': 2,
        'ECS::CapacityProvider': 2,
        'SNS::Topic': 2,
        'ACM::Certificate': 1,
        'Athena::WorkGroup': 1,
        'Backup::BackupVault': 1,
        'CloudTrail::Trail': 1,
        'EC2::CustomerGateway': 1,
        'EC2::DHCPOptions': 1,
        'EC2::FlowLog': 1,
        'EC2::InternetGateway': 1,
        'EC2::NatGateway': 1,
        'EC2::TransitGateway': 1,
        'EC2::TransitGatewayAttachment': 1,
        'EC2::VPC': 1,
        'EC2::VPCBlockPublicAccessOptions': 1,
        'EKS::Cluster': 1,
        'Events::EventBus': 1,
        'GuardDuty::Detector': 1,
        'IAM::OIDCProvider': 1,
        'IAM::SAMLProvider': 1,
        'InspectorV2::Activation': 1,
        'ResourceExplorer2::Index': 1,
        'Route53::HostedZone': 1,
        'Route53Resolver::ResolverRule': 1,
        'Route53Resolver::ResolverRuleAssociation': 1,
        'S3::StorageLens': 1,
        'SSM::AssociationCompliance': 1,
        'SSM::ManagedInstanceInventory': 1,
    }
    
    # Mapeo de recursos a operaciones
    resource_operations = {
        'Backup::BackupPlan': {'service': 'backup', 'operations': ['ListBackupPlans']},
        'AppConfig::DeploymentStrategy': {'service': 'appconfig', 'operations': ['ListDeploymentStrategies']},
        'Cassandra::Keyspace': {'service': 'keyspaces', 'operations': ['ListKeyspaces']},
        'EC2::EC2Fleet': {'service': 'ec2', 'operations': ['DescribeFleets']},
        'EC2::RouteTable': {'service': 'ec2', 'operations': ['DescribeRouteTables']},
        'EC2::Subnet': {'service': 'ec2', 'operations': ['DescribeSubnets']},
        'EC2::SubnetRouteTableAssociation': {'service': 'ec2', 'operations': ['DescribeRouteTables']},  # Se obtiene de RouteTables
        'RDS::DBInstance': {'service': 'rds', 'operations': ['DescribeDBInstances']},
        'EC2::LaunchTemplate': {'service': 'ec2', 'operations': ['DescribeLaunchTemplates']},
        'EC2::NetworkAcl': {'service': 'ec2', 'operations': ['DescribeNetworkAcls']},
        'EC2::NetworkInsightsPath': {'service': 'ec2', 'operations': ['DescribeNetworkInsightsPaths']},
        'EC2::TransitGatewayRouteTable': {'service': 'ec2', 'operations': ['DescribeTransitGatewayRouteTables']},
        'RDS::DBCluster': {'service': 'rds', 'operations': ['DescribeDBClusters']},
        'RDS::DBSubnetGroup': {'service': 'rds', 'operations': ['DescribeDBSubnetGroups']},
        'RDS::OptionGroup': {'service': 'rds', 'operations': ['DescribeOptionGroups']},
        'SecretsManager::Secret': {'service': 'secretsmanager', 'operations': ['ListSecrets']},
        'AutoScaling::AutoScalingGroup': {'service': 'autoscaling', 'operations': ['DescribeAutoScalingGroups']},
        'Config::ConfigurationRecorder': {'service': 'config', 'operations': ['DescribeConfigurationRecorders']},
        'EC2::VPNConnection': {'service': 'ec2', 'operations': ['DescribeVpnConnections']},
        'ECS::CapacityProvider': {'service': 'ecs', 'operations': ['DescribeCapacityProviders']},
        'SNS::Topic': {'service': 'sns', 'operations': ['ListTopics']},
        'ACM::Certificate': {'service': 'acm', 'operations': ['ListCertificates']},
        'Athena::WorkGroup': {'service': 'athena', 'operations': ['ListWorkGroups']},
        'Backup::BackupVault': {'service': 'backup', 'operations': ['ListBackupVaults']},
        'CloudTrail::Trail': {'service': 'cloudtrail', 'operations': ['ListTrails']},
        'EC2::CustomerGateway': {'service': 'ec2', 'operations': ['DescribeCustomerGateways']},
        'EC2::DHCPOptions': {'service': 'ec2', 'operations': ['DescribeDhcpOptions']},
        'EC2::FlowLog': {'service': 'ec2', 'operations': ['DescribeFlowLogs']},
        'EC2::InternetGateway': {'service': 'ec2', 'operations': ['DescribeInternetGateways']},
        'EC2::NatGateway': {'service': 'ec2', 'operations': ['DescribeNatGateways']},
        'EC2::TransitGateway': {'service': 'ec2', 'operations': ['DescribeTransitGateways']},
        'EC2::TransitGatewayAttachment': {'service': 'ec2', 'operations': ['DescribeTransitGatewayAttachments']},
        'EC2::VPC': {'service': 'ec2', 'operations': ['DescribeVpcs']},
        'EC2::VPCBlockPublicAccessOptions': {'service': 'ec2', 'operations': ['DescribeVpcBlockPublicAccessExclusions']},  # Puede requerir parámetros
        'EKS::Cluster': {'service': 'eks', 'operations': ['ListClusters']},
        'Events::EventBus': {'service': 'events', 'operations': ['ListEventBuses']},
        'GuardDuty::Detector': {'service': 'guardduty', 'operations': ['ListDetectors']},
        'IAM::OIDCProvider': {'service': 'iam', 'operations': ['ListOpenIDConnectProviders']},
        'IAM::SAMLProvider': {'service': 'iam', 'operations': ['ListSAMLProviders']},
        'InspectorV2::Activation': {'service': 'inspector2', 'operations': ['ListFindings']},  # Puede requerir parámetros
        'ResourceExplorer2::Index': {'service': 'resource-explorer-2', 'operations': ['ListIndexes']},
        'Route53::HostedZone': {'service': 'route53', 'operations': ['ListHostedZones']},
        'Route53Resolver::ResolverRule': {'service': 'route53resolver', 'operations': ['ListResolverRules']},
        'Route53Resolver::ResolverRuleAssociation': {'service': 'route53resolver', 'operations': ['ListResolverRuleAssociations']},
        'S3::StorageLens': {'service': 's3', 'operations': ['ListStorageLensConfigurations']},
        'SSM::AssociationCompliance': {'service': 'ssm', 'operations': ['ListAssociations']},
        'SSM::ManagedInstanceInventory': {'service': 'ssm', 'operations': ['DescribeInstanceInformation']},
    }
    
    run_dir = find_latest_run()
    if not run_dir:
        print("\n❌ No se encontraron runs disponibles")
        return
    
    print(f"\n📁 Analizando run: {run_dir.name}")
    
    # Cargar índice
    index_file = run_dir / "index" / "index.json"
    if not index_file.exists():
        print(f"\n❌ No se encontró índice en {run_dir.name}")
        return
    
    with open(index_file, 'r', encoding='utf-8') as f:
        idx = json.load(f)
    
    print(f"\n{'Recurso':<50} {'Esperado':<10} {'Encontrado':<12} {'Estado':<15}")
    print("="*90)
    
    results = []
    
    for resource_name, expected_count in expected.items():
        resource_info = resource_operations.get(resource_name, {})
        service_name = resource_info.get('service', '')
        expected_ops = resource_info.get('operations', [])
        
        if not service_name:
            results.append((resource_name, expected_count, 0, '❌ No mapeado', []))
            continue
        
        service_data = idx.get("services", {}).get(service_name, {})
        
        if not service_data:
            results.append((resource_name, expected_count, 0, '❌ Servicio no encontrado', []))
            continue
        
        found_count = 0
        found_ops = []
        
        for region_name, region_data in service_data.get("regions", {}).items():
            for op_info in region_data.get("operations", []):
                op_name = op_info.get("operation", "")
                op_normalized = op_name.replace('_', '').lower()
                
                for expected_op in expected_ops:
                    expected_normalized = expected_op.replace('_', '').lower()
                    if expected_normalized in op_normalized or op_normalized in expected_normalized:
                        success = op_info.get("success", False)
                        resource_count = op_info.get("resource_count", 0) or 0
                        if success:
                            found_count += resource_count
                            found_ops.append({
                                'operation': op_name,
                                'count': resource_count,
                                'region': region_name
                            })
        
        if found_count == expected_count:
            state = "✅ Correcto"
        elif found_count < expected_count:
            state = f"⚠️  Faltan {expected_count - found_count}"
        elif found_count > expected_count:
            state = f"⚠️  {found_count - expected_count} más"
        else:
            state = "❌ No encontrado"
        
        results.append((resource_name, expected_count, found_count, state, found_ops))
    
    # Ordenar por cantidad esperada (mayor a menor)
    results.sort(key=lambda x: (-x[1], x[0]))
    
    for resource_name, expected_count, found_count, state, found_ops in results:
        print(f"{resource_name:<50} {expected_count:<10} {found_count:<12} {state:<15}")
        if found_ops:
            for op in found_ops[:2]:  # Mostrar solo las primeras 2 operaciones
                print(f"  → {op['operation']} ({op['region']}): {op['count']} recursos")
    
    print("="*90)
    
    # Resumen
    correctos = sum(1 for _, _, _, state, _ in results if "✅" in state)
    faltantes = sum(1 for _, _, _, state, _ in results if "⚠️" in state or "❌" in state)
    
    print(f"\n📊 RESUMEN:")
    print(f"   ✅ Correctos: {correctos}")
    print(f"   ⚠️  Faltantes/Incorrectos: {faltantes}")
    print(f"   Total: {len(results)}")

if __name__ == "__main__":
    main()

