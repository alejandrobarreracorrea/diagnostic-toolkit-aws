# Estructura del Proyecto ECAD

## Organización de Directorios

```
diagnostic-toolkit-aws/
├── collector/              # Módulo de recolección de datos AWS
│   ├── discovery.py        # Descubrimiento de servicios y operaciones
│   ├── executor.py         # Ejecución de operaciones AWS
│   ├── main.py             # Punto de entrada del collector
│   └── metadata.py         # Recolección de metadatos de cuenta
│
├── analyzer/               # Módulo de análisis offline
│   ├── indexer.py          # Indexación de datos recolectados
│   ├── inventory.py        # Generación de inventarios
│   ├── findings.py         # Generación de hallazgos
│   ├── report_generator.py # Generación de reportes
│   └── main.py             # Punto de entrada del analyzer
│
├── evidence/               # Generación de evidence pack Well-Architected
│   └── generator.py       # Generador de evidencias
│
├── templates/              # Plantillas de reportes (Jinja2)
│   ├── executive_summary.md
│   ├── findings_report.md
│   ├── inventory_report.md
│   ├── roadmap.md
│   ├── scorecard.md
│   └── technical_annex.md
│
├── fixtures/               # Datos de ejemplo para demo
│   ├── raw/                # Datos raw de ejemplo
│   ├── index/               # Índices generados
│   └── outputs/            # Outputs de ejemplo
│
├── scripts/                # Scripts de ejecución por plataforma
│   ├── windows/             # Scripts para Windows
│   │   ├── ecad.bat        # Script batch principal
│   │   ├── ecad.ps1        # Script PowerShell principal
│   │   ├── run_demo.bat    # Demo en batch
│   │   ├── run_demo.ps1    # Demo en PowerShell
│   │   ├── verificar_credenciales.bat
│   │   └── verificar_credenciales.ps1
│   └── linux/              # Scripts para Linux/macOS
│       ├── run_demo.sh
│       └── verificar_credenciales.sh
│
├── tools/                  # Herramientas y scripts de utilidad
│   ├── analizar_iam.py     # Análisis de recursos IAM
│   ├── analyze_errors.py   # Análisis de errores
│   ├── check_policy_size.py # Verificar tamaño de políticas
│   ├── diagnose_collection.py # Diagnóstico de recolección
│   ├── generate_iam_policy.py # Generador de políticas IAM
│   ├── test_collect_simple.py # Test simple de recolección
│   └── ver_iam_recursos.py # Ver recursos IAM contados
│
├── policies/               # Políticas IAM
│   ├── iam-policy-ecad-part1.json
│   ├── iam-policy-ecad-part2.json
│   └── README-IAM-POLICIES.md
│
├── docs/                   # Documentación
│   ├── security.md         # Seguridad y permisos
│   ├── engagement-model.md # Modelo de engagement
│   ├── installation/       # Guías de instalación
│   │   └── INSTALACION_WINDOWS.md
│   └── guides/             # Guías y tutoriales
│       └── TROUBLESHOOTING.md
│
├── runs/                   # Directorio de ejecuciones (generado)
│   └── run-YYYYMMDD-HHMMSS/
│       ├── raw/            # Datos raw recolectados
│       ├── index/           # Índices generados
│       ├── outputs/         # Outputs generados
│       └── metadata.json    # Metadatos del run
│
├── ecad.py                 # Script interactivo principal (Python)
├── Makefile                # Comandos Make (Linux/macOS)
├── requirements.txt        # Dependencias Python
└── README.md                  # Documentación principal

```

## Descripción de Directorios

### `collector/`
Módulo principal para recolectar datos desde AWS. Descubre servicios, operaciones y ejecuta llamadas API de forma segura y eficiente.

### `analyzer/`
Módulo de análisis offline que procesa datos pre-recolectados sin necesidad de conexión a AWS. Genera inventarios, hallazgos y reportes.

### `evidence/`
Generador de evidence pack para Well-Architected Framework. Produce evidencias objetivas por pilar.

### `templates/`
Plantillas Jinja2 para generar reportes en Markdown. Incluye reportes ejecutivos, técnicos y roadmaps.

### `fixtures/`
Datos de ejemplo para ejecutar demos sin necesidad de credenciales AWS. Útil para pruebas y demostraciones.

### `scripts/`
Scripts de ejecución organizados por plataforma:
- **`windows/`**: Scripts batch (.bat) y PowerShell (.ps1)
- **`linux/`**: Scripts bash (.sh) para Linux/macOS

### `tools/`
Herramientas auxiliares y scripts de utilidad para diagnóstico, análisis y mantenimiento.

### `policies/`
Políticas IAM pre-configuradas para ECAD. Incluye políticas ReadOnly divididas en dos partes debido a límites de tamaño.

### `docs/`
Documentación completa del proyecto:
- **`security.md`**: Seguridad, permisos y mejores prácticas
- **`engagement-model.md`**: Modelo de engagement con clientes
- **`installation/`**: Guías de instalación por plataforma
- **`guides/`**: Guías y tutoriales adicionales

### `runs/`
Directorio donde se almacenan las ejecuciones. Cada ejecución crea un subdirectorio con timestamp.

## Archivos Principales en Raíz

- **`ecad.py`**: Script interactivo principal (funciona en todos los sistemas)
- **`Makefile`**: Comandos Make para Linux/macOS
- **`requirements.txt`**: Dependencias Python
- **`README.md`**: Documentación principal del proyecto


