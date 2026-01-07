#!/usr/bin/env python3
"""Script para verificar el JSON del evidence pack"""

import json
from pathlib import Path

# Encontrar el último run
runs = sorted([d for d in Path('runs').iterdir() if d.is_dir()], 
              key=lambda x: x.stat().st_mtime, reverse=True)
if not runs:
    print("No se encontraron runs")
    exit(1)

latest_run = runs[0]
json_file = latest_run / 'outputs' / 'evidence' / 'evidence_pack.json'

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Estructura del JSON:")
print(f"Keys principales: {list(data.keys())}")

# Buscar la sección de Security
if 'pillars' in data:
    for pillar in data['pillars']:
        if pillar.get('pillar') == 'Security':
            print("\n=== Security Pillar ===")
            evidence = pillar.get('evidence', [])
            for ev in evidence:
                if ev.get('category') == 'public_resources':
                    print(f"\nPublic Resources Evidence:")
                    print(f"  Description: {ev.get('description', 'N/A')}")
                    print(f"  Elastic IPs count: {ev.get('elastic_ips_count', 0)}")
                    print(f"  Elastic IPs: {ev.get('elastic_ips', [])[:5]}")
                    print(f"  Suggested review:")
                    for item in ev.get('suggested_review', [])[:5]:
                        print(f"    - {item}")

