# AWS Cloud Architecture Diagnostic (ECAD)

## Descripción

ECAD es un producto de diagnóstico técnico para clientes B2B en AWS que proporciona inventario completo de recursos, análisis arquitectónico y evidencias para Well-Architected Review. El producto está diseñado para ser ejecutado como un servicio puntual, sin SLA ni soporte 24/7.

## Características Principales

- **Inventario Completo**: Descubrimiento automático de todos los recursos AWS desde cero
- **Análisis Offline**: Procesamiento sin conexión a AWS usando datos pre-recolectados
- **Evidence Pack**: Generación automática de evidencias para Well-Architected Framework
- **Reportes Ejecutivos**: Reportes y Plan de mejoras (Well-Architected Improvement Plan) listos para presentar a clientes
- **Modo Demo**: Ejecución con datos de ejemplo sin necesidad 0de credenciales AWS

## Estructura del Repositorio

```
.
├── collector/          # Recolección de datos desde AWS
├── analyzer/           # Análisis offline de datos recolectados
├── evidence/           # Generación de evidence pack Well-Architected
├── fixtures/           # Datos de ejemplo para demo
├── templates/          # Plantillas de reportes
├── scripts/            # Scripts por plataforma (Windows/Linux)
│   ├── windows/        # Scripts .bat y .ps1
│   └── linux/          # Scripts .sh
├── tools/              # Herramientas y scripts de utilidad
├── policies/           # Políticas IAM pre-configuradas
├── docs/               # Documentación completa
│   ├── installation/   # Guías de instalación
│   └── guides/         # Guías y tutoriales
├── ecad.py             # Script interactivo principal
├── Makefile            # Comandos principales (Linux/macOS)
└── requirements.txt    # Dependencias Python
```

Ver estructura detallada en [`docs/STRUCTURE.md`](docs/STRUCTURE.md)

## Requisitos Previos

- Python 3.9+
- Credenciales AWS con permisos ReadOnly (ver `docs/security.md`)
- 10GB+ de espacio en disco (dependiendo del tamaño del entorno)

## Instalación Rápida

### Linux / macOS

```bash
# Clonar o descargar el repositorio
cd diagnostic-toolkit-aws

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno (opcional)
export AWS_ROLE_ARN=arn:aws:iam::ACCOUNT:role/ECADRole
export AWS_EXTERNAL_ID=your-external-id
export AWS_REGION=us-east-1
```

### Windows

**Ver guía completa:** [`docs/installation/INSTALACION_WINDOWS.md`](docs/installation/INSTALACION_WINDOWS.md)

**Instalación rápida:**

1. **Instalar Python 3.9+** desde https://www.python.org/downloads/
   - ⚠️ **IMPORTANTE:** Marcar "Add Python to PATH" durante la instalación

2. **Abrir PowerShell o CMD** en el directorio de ECAD

3. **Instalar dependencias:**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Ejecutar script interactivo:**
   ```cmd
   python ecad.py
   ```

**Scripts disponibles para Windows:**
- `scripts/windows/ecad.bat` - Script batch (CMD)
- `scripts/windows/ecad.ps1` - Script PowerShell
- `scripts/windows/verificar_credenciales.bat` / `verificar_credenciales.ps1` - Verificar credenciales AWS
- `scripts/windows/run_demo.bat` - Ejecutar demo

**Ejemplos:**
```cmd
scripts\windows\ecad.bat install      # Instalar dependencias
scripts\windows\ecad.bat collect      # Recolectar datos
scripts\windows\ecad.bat demo         # Ejecutar demo
```

## Uso Rápido

### 🚀 Inicio Rápido con Script Interactivo (Recomendado)

**Linux / macOS:**
```bash
# Ejecutar script interactivo
python3 ecad.py
```

**Windows:**
```cmd
python ecad.py
```

El script te mostrará un menú con todas las opciones disponibles.

---

## Uso Rápido (Comandos Individuales)

### Linux / macOS (Makefile)

### 1. Recolección de Datos (Online)

```bash
# Recolectar todos los recursos AWS
make collect

# O con configuración personalizada
python3 -m collector.main \
    --role-arn arn:aws:iam::ACCOUNT:role/ECADRole \
    --external-id your-id \
    --output-dir ./runs/run-$(date +%Y%m%d-%H%M%S) \
    --max-threads 20 \
    --max-pages 100
```

### 2. Análisis Offline

```bash
# Analizar un run específico
make analyze RUN_DIR=./runs/run-20240101-120000

# O directamente
python3 -m analyzer.main --run-dir ./runs/run-20240101-120000
```

### 3. Generar Evidence Pack

```bash
# Generar evidence pack para Well-Architected
make evidence RUN_DIR=./runs/run-20240101-120000
```

### 4. Generar Reportes Completos

```bash
# Generar todos los reportes
make reports RUN_DIR=./runs/run-20240101-120000
```

### 5. Modo Demo (Sin AWS)

```bash
# Ejecutar demo con datos de ejemplo
make demo
```

## Comandos Make Principales (Linux/macOS)

- `make collect` - Recolectar datos desde AWS
- `make analyze RUN_DIR=...` - Analizar un run específico
- `make evidence RUN_DIR=...` - Generar evidence pack
- `make reports RUN_DIR=...` - Generar todos los reportes
- `make demo` - Ejecutar demo completo con fixtures
- `make clean` - Limpiar archivos temporales

### Windows (Scripts Batch/PowerShell)

**Usando scripts batch (.bat):**
```cmd
scripts\windows\ecad.bat install          # Instalar dependencias
scripts\windows\ecad.bat collect          # Recolectar datos
scripts\windows\ecad.bat analyze RUN_DIR=runs\run-20240101-120000
scripts\windows\ecad.bat evidence RUN_DIR=runs\run-20240101-120000
scripts\windows\ecad.bat reports RUN_DIR=runs\run-20240101-120000
scripts\windows\ecad.bat demo             # Ejecutar demo
scripts\windows\ecad.bat clean            # Limpiar archivos temporales
```

**Usando PowerShell (.ps1):**
```powershell
.\scripts\windows\ecad.ps1 install
.\scripts\windows\ecad.ps1 collect
.\scripts\windows\ecad.ps1 analyze -RunDir runs\run-20240101-120000
.\scripts\windows\ecad.ps1 evidence -RunDir runs\run-20240101-120000
.\scripts\windows\ecad.ps1 reports -RunDir runs\run-20240101-120000
.\scripts\windows\ecad.ps1 demo
.\scripts\windows\ecad.ps1 clean
```

**Comandos Python directos (funcionan en todos los sistemas):**
```cmd
python -m collector.main --output-dir runs\run-20240101-120000
python -m analyzer.main --run-dir runs\run-20240101-120000
python -m analyzer.report_generator --run-dir runs\run-20240101-120000
```

## Configuración Avanzada

### Variables de Entorno

**Linux / macOS:**
```bash
# Credenciales AWS (AssumeRole)
export AWS_ROLE_ARN=arn:aws:iam::ACCOUNT:role/ECADRole
export AWS_EXTERNAL_ID=your-external-id

# Configuración de región
export AWS_REGION=us-east-1
export AWS_REGIONS=us-east-1,us-west-2,eu-west-1  # Múltiples regiones

# Límites y configuración
export ECAD_MAX_THREADS=20
export ECAD_MAX_PAGES=100
export ECAD_MAX_FOLLOWUPS=5

# Filtros de servicios
export ECAD_SERVICE_ALLOWLIST=ec2,rds,s3,lambda  # Solo estos servicios
export ECAD_SERVICE_DENYLIST=workspaces,connect  # Excluir estos servicios
```

**Windows (CMD):**
```cmd
set AWS_ROLE_ARN=arn:aws:iam::ACCOUNT:role/ECADRole
set AWS_EXTERNAL_ID=your-external-id
set AWS_REGION=us-east-1
set ECAD_MAX_THREADS=20
set ECAD_MAX_PAGES=100
```

**Windows (PowerShell):**
```powershell
$env:AWS_ROLE_ARN="arn:aws:iam::ACCOUNT:role/ECADRole"
$env:AWS_EXTERNAL_ID="your-external-id"
$env:AWS_REGION="us-east-1"
$env:ECAD_MAX_THREADS="20"
$env:ECAD_MAX_PAGES="100"
```

### Archivo de Configuración

Crea un archivo `config.yaml` en la raíz:

```yaml
collector:
  max_threads: 20
  max_pages: 100
  max_followups_per_list: 5
  regions:
    - us-east-1
    - us-west-2
  service_allowlist: []  # Vacío = todos
  service_denylist:
    - workspaces
    - connect
  assume_role:
    role_arn: "arn:aws:iam::ACCOUNT:role/ECADRole"
    external_id: "your-external-id"
    session_name: "ECAD-Session"
```

## Flujo de Trabajo Típico

1. **Engagement Inicial**: Revisar `docs/engagement-model.md`
2. **Configuración de Permisos**: Seguir `docs/security.md` para crear rol IAM
3. **Recolección**: Ejecutar `make collect` (puede tardar horas en entornos grandes)
4. **Análisis**: Ejecutar `make analyze` para generar inventarios y hallazgos
5. **Evidence Pack**: Ejecutar `make evidence` para Well-Architected
6. **Reportes**: Ejecutar `make reports` para generar documentos finales
7. **Entrega**: Revisar outputs en `RUN_DIR/outputs/`

## Estructura de Outputs

Después de ejecutar el análisis, encontrarás:

```
RUN_DIR/
├── raw/                    # Dumps JSON comprimidos originales
├── index/                  # Índices para búsqueda rápida
├── outputs/
│   ├── inventory/          # Inventarios en CSV/JSON
│   ├── evidence/           # Evidence pack Well-Architected
│   ├── reports/            # Reportes ejecutivos
│   └── scorecards/         # Scorecards por dominio
└── metadata.json           # Metadatos del run
```

## Seguridad

- **Permisos Mínimos**: Solo ReadOnly + Cost Explorer lectura
- **AssumeRole**: Uso obligatorio de roles con ExternalId
- **Datos Locales**: Todos los datos se almacenan localmente, cifrados recomendado
- Ver `docs/security.md` para detalles completos
- Ver `policies/README-IAM-POLICIES.md` para implementación de políticas IAM

## Limitaciones y Consideraciones

- **Sin SLA**: Este es un producto de diagnóstico puntual, no un servicio operativo
- **Sin Soporte 24/7**: Soporte durante horario comercial según contrato
- **Rate Limiting**: El collector respeta límites de AWS y aplica backoff automático
- **Cobertura**: Algunos servicios pueden requerir parámetros específicos que no se pueden inferir automáticamente

## Troubleshooting

### Error: AccessDenied
- Verificar que el rol IAM tenga los permisos correctos
- Verificar ExternalId si se usa AssumeRole

### Error: Throttling
- Reducir `max_threads` en la configuración
- El collector aplica backoff automático, pero puede tardar más

### Servicio no descubierto
- Algunos servicios pueden no estar disponibles en todas las regiones
- Verificar `service_denylist` en configuración

## Soporte

Para soporte técnico:
- **Documentación**: Consultar `docs/` para guías completas
- **Troubleshooting**: Ver `docs/guides/TROUBLESHOOTING.md` para problemas comunes
- **Instalación Windows**: Ver `docs/installation/INSTALACION_WINDOWS.md`
- **Políticas IAM**: Ver `policies/README-IAM-POLICIES.md`
- **Contacto**: Consultar la documentación del proyecto para más información

## Licencia

Este proyecto está licenciado bajo la [MIT License](LICENSE).

### Resumen de la Licencia MIT

- ✅ **Uso comercial permitido**: Puedes usar este software en proyectos comerciales
- ✅ **Modificación permitida**: Puedes modificar el código según tus necesidades
- ✅ **Distribución permitida**: Puedes distribuir el software original o modificado
- ✅ **Uso privado permitido**: Puedes usar el software en proyectos privados
- ⚠️ **Requisito**: Debes incluir el aviso de copyright y la licencia en todas las copias

Para más detalles, consulta:
- [LICENSE](LICENSE) - Texto completo de la licencia
- [NOTICES.md](NOTICES.md) - Licencias de dependencias de terceros
- [docs/LEGAL.md](docs/LEGAL.md) - Consideraciones legales y de licenciamiento

## Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

Al contribuir, aceptas que tus contribuciones serán licenciadas bajo la misma licencia MIT del proyecto.
