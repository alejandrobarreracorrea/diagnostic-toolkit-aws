.PHONY: collect analyze evidence reports demo clean install

# Variables
FIXTURES_DIR = ./fixtures

# Instalación
install:
	pip3 install -r requirements.txt

# Recolección de datos desde AWS
# IMPORTANTE: Evaluar timestamp UNA SOLA VEZ para evitar crear múltiples runs
collect:
	@if [ -z "$(RUN_DIR)" ]; then \
		RUN_DIR="./runs/run-$$(date +%Y%m%d-%H%M%S)"; \
	else \
		RUN_DIR="$(RUN_DIR)"; \
	fi; \
	echo "Iniciando recolección de datos AWS..."; \
	echo "Run directory: $$RUN_DIR"; \
	mkdir -p $$RUN_DIR/raw; \
	python3 -m collector.main \
		--output-dir $$RUN_DIR \
		--max-threads $$(echo $${ECAD_MAX_THREADS:-20}) \
		--max-pages $$(echo $${ECAD_MAX_PAGES:-100})

# Análisis offline
analyze:
	@if [ -z "$(RUN_DIR)" ]; then \
		echo "Error: RUN_DIR no especificado. Uso: make analyze RUN_DIR=./runs/run-YYYYMMDD-HHMMSS"; \
		exit 1; \
	fi
	@echo "Analizando run: $(RUN_DIR)"
	python3 -m analyzer.main --run-dir $(RUN_DIR)

# Generar evidence pack
evidence:
	@if [ -z "$(RUN_DIR)" ]; then \
		echo "Error: RUN_DIR no especificado. Uso: make evidence RUN_DIR=./runs/run-YYYYMMDD-HHMMSS"; \
		exit 1; \
	fi
	@echo "Generando evidence pack para: $(RUN_DIR)"
	python3 -m evidence.generator --run-dir $(RUN_DIR)

# Generar todos los reportes
reports:
	@if [ -z "$(RUN_DIR)" ]; then \
		echo "Error: RUN_DIR no especificado. Uso: make reports RUN_DIR=./runs/run-YYYYMMDD-HHMMDD"; \
		exit 1; \
	fi
	@echo "Generando reportes para: $(RUN_DIR)"
	python3 -m analyzer.report_generator --run-dir $(RUN_DIR)

# Demo completo con fixtures
demo:
	@echo "Ejecutando demo con fixtures..."
	@mkdir -p $(FIXTURES_DIR)/outputs
	python3 -m analyzer.main --run-dir $(FIXTURES_DIR)
	python3 -m evidence.generator --run-dir $(FIXTURES_DIR)
	python3 -m analyzer.report_generator --run-dir $(FIXTURES_DIR)
	@echo "Demo completado. Revisa $(FIXTURES_DIR)/outputs/"

# Limpiar archivos temporales
clean:
	@echo "Limpiando archivos temporales..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Help
help:
	@echo "Comandos disponibles:"
	@echo "  make install          - Instalar dependencias"
	@echo "  make collect          - Recolectar datos desde AWS"
	@echo "  make analyze RUN_DIR=... - Analizar un run específico"
	@echo "  make evidence RUN_DIR=... - Generar evidence pack"
	@echo "  make reports RUN_DIR=... - Generar todos los reportes"
	@echo "  make demo             - Ejecutar demo con fixtures"
	@echo "  make clean            - Limpiar archivos temporales"

