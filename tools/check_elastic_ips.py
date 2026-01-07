#!/usr/bin/env python3
"""Script para verificar Elastic IPs"""

import json
import gzip
from pathlib import Path

# Encontrar el último run
runs = sorted([d for d in Path('runs').iterdir() if d.is_dir()], 
              key=lambda x: x.stat().st_mtime, reverse=True)
if not runs:
    print("No se encontraron runs")
    exit(1)

latest_run = runs[0]
print(f"Analizando run: {latest_run.name}\n")

ec2_dir = latest_run / 'raw' / 'ec2' / 'us-east-1'

# Verificar DescribeAddresses (Elastic IPs)
addresses_file = ec2_dir / 'DescribeAddresses.json.gz'
if addresses_file.exists():
    with gzip.open(addresses_file, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=== DescribeAddresses (Elastic IPs) ===")
    print(f"Success: {data.get('metadata', {}).get('success', False)}")
    print(f"Paginated: {data.get('metadata', {}).get('paginated', False)}")
    
    data_content = data.get('data', {})
    if isinstance(data_content, dict):
        # Manejar datos paginados
        if "pages" in data_content and "data" in data_content:
            pages = data_content.get("data", [])
            all_addresses = []
            for page in pages:
                addresses = page.get("Addresses", [])
                if addresses:
                    all_addresses.extend(addresses)
            print(f"Total Elastic IPs (paginado): {len(all_addresses)}")
        else:
            addresses = data_content.get("Addresses", [])
            print(f"Total Elastic IPs: {len(addresses)}")
            all_addresses = addresses
        
        if all_addresses:
            print("\nElastic IPs encontradas:")
            for i, addr in enumerate(all_addresses, 1):
                public_ip = addr.get('PublicIp', 'N/A')
                allocation_id = addr.get('AllocationId', 'N/A')
                instance_id = addr.get('InstanceId', 'N/A')
                domain = addr.get('Domain', 'N/A')
                print(f"  {i}. PublicIP: {public_ip}, AllocationId: {allocation_id}, InstanceId: {instance_id}, Domain: {domain}")
        else:
            print("No se encontraron Elastic IPs")
    else:
        print("Estructura inesperada")

