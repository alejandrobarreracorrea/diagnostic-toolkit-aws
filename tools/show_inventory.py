#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para mostrar el inventario consolidado directamente.
"""

import sys
import json
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
sys.path.insert(0, str(project_root))

# Importar función de selección de run
from ecad import select_run, show_inventory_console

def main():
    # Seleccionar automáticamente el último run
    runs_dir = project_root / "runs"
    if not runs_dir.exists():
        print("❌ No se encontraron runs disponibles")
        return
    
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    if not runs:
        print("❌ No se encontraron runs disponibles")
        return
    
    # Usar el último run
    run_dir = runs[0]
    print(f"📁 Usando run: {run_dir.name}\n")
    
    # Cargar índice y mostrar inventario
    index_file = run_dir / "index" / "index.json"
    if not index_file.exists():
        print(f"❌ No se encontró el índice en {run_dir.name}")
        print("   Ejecuta primero la opción 3 (ANALIZAR) para generar el índice")
        return
    
    try:
        with open(index_file, 'r') as f:
            index = json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo índice: {e}")
        return
    
    services = index.get("services", {})
    if not services:
        print(f"⚠️  No hay servicios en el índice de {run_dir.name}")
        return
    
    # Importar y ejecutar la lógica de show_inventory_console pero con el run ya seleccionado
    from ecad import show_inventory_console
    
    # Modificar temporalmente select_run y input para que no pida interacción
    import ecad
    import builtins
    original_select_run = ecad.select_run
    original_input = builtins.input
    
    def mock_select_run():
        return run_dir
    
    def mock_input(prompt=""):
        # Si es la pregunta de exportar CSV, retornar 'n' por defecto
        if "exportar" in prompt.lower() or "csv" in prompt.lower():
            return 'n'
        return original_input(prompt)
    
    ecad.select_run = mock_select_run
    builtins.input = mock_input
    
    try:
        show_inventory_console()
    finally:
        ecad.select_run = original_select_run
        builtins.input = original_input

if __name__ == "__main__":
    main()

