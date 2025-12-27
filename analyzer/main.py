#!/usr/bin/env python3
"""
ECAD Analyzer - Análisis offline de datos recolectados

Procesa datos recolectados sin necesidad de conexión a AWS,
generando inventarios, hallazgos y tablas ejecutivas.
"""

import argparse
import json
import gzip
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import csv

from analyzer.indexer import DataIndexer
from analyzer.inventory import InventoryGenerator
from analyzer.findings import FindingsGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Analyzer:
    """Analizador principal de datos recolectados."""
    
    def __init__(self, run_dir: str):
        self.run_dir = Path(run_dir)
        self.raw_dir = self.run_dir / "raw"
        self.index_dir = self.run_dir / "index"
        self.output_dir = self.run_dir / "outputs"
        self.inventory_dir = self.output_dir / "inventory"
        
        # Crear directorios
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.inventory_dir.mkdir(parents=True, exist_ok=True)
        
        # Componentes
        self.indexer = DataIndexer(self.raw_dir, self.index_dir)
        self.inventory_gen = InventoryGenerator(self.index_dir, self.inventory_dir)
        self.findings_gen = FindingsGenerator(self.index_dir, self.output_dir)
    
    def analyze(self):
        """Ejecutar análisis completo."""
        logger.info(f"Analizando run: {self.run_dir}")
        
        # 1. Indexar datos
        logger.info("Indexando datos recolectados...")
        index = self.indexer.index_all()
        logger.info(f"Índice creado: {len(index.get('services', {}))} servicios")
        
        # 2. Generar inventario
        logger.info("Generando inventarios...")
        inventory = self.inventory_gen.generate()
        logger.info(f"Inventario generado: {len(inventory.get('services', {}))} servicios")
        
        # 3. Generar hallazgos
        logger.info("Generando hallazgos...")
        findings = self.findings_gen.generate()
        logger.info(f"Hallazgos generados: {len(findings.get('findings', []))} hallazgos")
        
        # 4. Generar resumen ejecutivo
        logger.info("Generando resumen ejecutivo...")
        summary = self._generate_summary(index, inventory, findings)
        summary_file = self.output_dir / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        logger.info(f"Resumen guardado en {summary_file}")
        
        logger.info("Análisis completado")
    
    def _generate_summary(
        self,
        index: Dict,
        inventory: Dict,
        findings: Dict
    ) -> Dict:
        """Generar resumen ejecutivo del análisis."""
        return {
            "run_dir": str(self.run_dir),
            "services_count": len(index.get("services", {})),
            "regions_count": len(inventory.get("regions", [])),
            "total_resources": inventory.get("total_resources", 0),
            "findings_count": len(findings.get("findings", [])),
            "findings_by_severity": findings.get("findings_by_severity", {}),
            "top_services": inventory.get("top_services", []),
            "top_regions": inventory.get("top_regions", [])
        }


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="ECAD Analyzer - Análisis offline de datos AWS"
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Directorio del run a analizar"
    )
    
    args = parser.parse_args()
    
    if not Path(args.run_dir).exists():
        logger.error(f"Directorio no existe: {args.run_dir}")
        sys.exit(1)
    
    analyzer = Analyzer(args.run_dir)
    
    try:
        analyzer.analyze()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error en análisis: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()


