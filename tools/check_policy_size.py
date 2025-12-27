#!/usr/bin/env python3
"""Verificar tamaño de políticas IAM"""
import json
from pathlib import Path

# Cambiar al directorio raíz del proyecto
project_root = Path(__file__).parent.parent

files = [
    'policies/iam-policy-ecad-part1.json',
    'policies/iam-policy-ecad-part2.json'
]

limit = 6144

for file in files:
    file_path = project_root / file
    if not file_path.exists():
        print(f"⚠️  {file}: No encontrado")
        continue
    
    with open(file_path, 'r') as f:
        policy = json.load(f)
        compact = json.dumps(policy, separators=(',', ':'))
        size = len(compact)
        diff = size - limit
        print(f"{file}:")
        print(f"  Caracteres: {size}")
        print(f"  Límite: {limit}")
        print(f"  Diferencia: {diff} ({'+' if diff > 0 else ''}{diff})")
        print(f"  Status: {'❌ EXCEDE' if diff > 0 else '✅ OK'}")
        print()

