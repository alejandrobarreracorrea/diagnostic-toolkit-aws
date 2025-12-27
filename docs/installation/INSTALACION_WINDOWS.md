# Instalación de ECAD en Windows

Esta guía te ayudará a instalar y configurar ECAD en sistemas Windows.

## Requisitos Previos

### 1. Python 3.9 o superior

1. **Descargar Python:**
   - Visita: https://www.python.org/downloads/
   - Descarga la versión más reciente de Python 3.9 o superior
   - **IMPORTANTE:** Durante la instalación, marca la opción **"Add Python to PATH"**

2. **Verificar instalación:**
   ```cmd
   python --version
   ```
   Deberías ver algo como: `Python 3.9.x` o superior

3. **Si Python no está en PATH:**
   - Abre "Variables de entorno" desde el Panel de Control
   - Agrega la ruta de Python a la variable `Path`
   - Ejemplo: `C:\Python39\` y `C:\Python39\Scripts\`

### 2. pip (Gestor de paquetes Python)

pip generalmente viene incluido con Python. Verifica que esté instalado:

```cmd
pip --version
```

Si no está instalado, reinstala Python marcando "Add Python to PATH".

### 3. AWS CLI (Opcional pero recomendado)

```cmd
pip install awscli
```

## Instalación de ECAD

### Opción 1: Usando el Script Interactivo (Recomendado)

1. **Abrir PowerShell o CMD:**
   - Presiona `Win + X` y selecciona "Windows PowerShell" o "Símbolo del sistema"
   - Navega al directorio de ECAD:
     ```cmd
     cd C:\ruta\a\diagnostic-toolkit-aws
     ```

2. **Ejecutar el script interactivo:**
   ```cmd
   python ecad.py
   ```
   
   O si prefieres PowerShell:
   ```powershell
   python ecad.py
   ```

3. **Seleccionar opción 8 (INSTALAR):**
   - El script verificará e instalará automáticamente las dependencias

### Opción 2: Instalación Manual

1. **Abrir PowerShell o CMD en el directorio de ECAD**

2. **Instalar dependencias:**
   ```cmd
   pip install -r requirements.txt
   ```

3. **Verificar instalación:**
   ```cmd
   python -c "import boto3, botocore, jinja2; print('✓ Dependencias instaladas')"
   ```

## Configuración de Credenciales AWS

### Opción 1: AWS CLI (Recomendado)

```cmd
aws configure
```

Ingresa:
- AWS Access Key ID
- AWS Secret Access Key
- Default region name (ej: `us-east-1`)
- Default output format (puedes dejar `json`)

### Opción 2: Variables de Entorno

**En CMD:**
```cmd
set AWS_ACCESS_KEY_ID=tu-access-key
set AWS_SECRET_ACCESS_KEY=tu-secret-key
set AWS_DEFAULT_REGION=us-east-1
```

**En PowerShell:**
```powershell
$env:AWS_ACCESS_KEY_ID="tu-access-key"
$env:AWS_SECRET_ACCESS_KEY="tu-secret-key"
$env:AWS_DEFAULT_REGION="us-east-1"
```

**Permanente (PowerShell):**
```powershell
[System.Environment]::SetEnvironmentVariable("AWS_ACCESS_KEY_ID", "tu-access-key", "User")
[System.Environment]::SetEnvironmentVariable("AWS_SECRET_ACCESS_KEY", "tu-secret-key", "User")
```

### Opción 3: Archivo de Credenciales

Crea el archivo: `%USERPROFILE%\.aws\credentials`

```ini
[default]
aws_access_key_id = tu-access-key
aws_secret_access_key = tu-secret-key
```

Y el archivo: `%USERPROFILE%\.aws\config`

```ini
[default]
region = us-east-1
```

## Uso de ECAD en Windows

### Método 1: Script Interactivo (Más Fácil)

```cmd
python ecad.py
```

Este script te mostrará un menú interactivo con todas las opciones disponibles.

### Método 2: Scripts Batch (.bat)

**Instalar dependencias:**
```cmd
scripts\windows\ecad.bat install
```

**Recolectar datos:**
```cmd
scripts\windows\ecad.bat collect
```

**Analizar un run:**
```cmd
scripts\windows\ecad.bat analyze RUN_DIR=runs\run-20240101-120000
```

**Generar reportes:**
```cmd
scripts\windows\ecad.bat reports RUN_DIR=runs\run-20240101-120000
```

**Ejecutar demo:**
```cmd
scripts\windows\ecad.bat demo
```

### Método 3: PowerShell (.ps1)

**Nota:** Si PowerShell muestra un error de política de ejecución, ejecuta primero:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Instalar dependencias:**
```powershell
.\scripts\windows\ecad.ps1 install
```

**Recolectar datos:**
```powershell
.\scripts\windows\ecad.ps1 collect
```

**Analizar un run:**
```powershell
.\scripts\windows\ecad.ps1 analyze -RunDir runs\run-20240101-120000
```

**Generar reportes:**
```powershell
.\scripts\windows\ecad.ps1 reports -RunDir runs\run-20240101-120000
```

**Ejecutar demo:**
```powershell
.\scripts\windows\ecad.ps1 demo
```

### Método 4: Comandos Python Directos

**Recolectar datos:**
```cmd
python -m collector.main --output-dir runs\run-20240101-120000
```

**Analizar:**
```cmd
python -m analyzer.main --run-dir runs\run-20240101-120000
```

**Generar reportes:**
```cmd
python -m analyzer.report_generator --run-dir runs\run-20240101-120000
```

## Verificación de Instalación

### Verificar Credenciales AWS

**CMD:**
```cmd
scripts\windows\verificar_credenciales.bat
```

**PowerShell:**
```powershell
.\scripts\windows\verificar_credenciales.ps1
```

O manualmente:
```cmd
aws sts get-caller-identity
```

### Ejecutar Demo

```cmd
scripts\windows\run_demo.bat
```

O:
```powershell
.\scripts\windows\run_demo.ps1
```

## Solución de Problemas

### Error: "python no se reconoce como comando"

**Solución:**
1. Verifica que Python esté instalado: `python --version`
2. Si no funciona, agrega Python al PATH:
   - Panel de Control → Sistema → Variables de entorno
   - Edita la variable `Path` y agrega:
     - `C:\Python39\`
     - `C:\Python39\Scripts\`
3. Reinicia la terminal después de cambiar el PATH

### Error: "pip no se reconoce como comando"

**Solución:**
1. Usa `python -m pip` en lugar de `pip`:
   ```cmd
   python -m pip install -r requirements.txt
   ```

### Error: "No se puede cargar el archivo porque la ejecución de scripts está deshabilitada"

**Solución (PowerShell):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error: "ModuleNotFoundError: No module named 'boto3'"

**Solución:**
```cmd
python -m pip install -r requirements.txt
```

### Rutas con Espacios

Si tu ruta contiene espacios, usa comillas:
```cmd
python ecad.py
```

O en PowerShell:
```powershell
cd "C:\Mi Carpeta\diagnostic-toolkit-aws"
python ecad.py
```

## Diferencias con Linux/macOS

1. **Separadores de ruta:** Windows usa `\` en lugar de `/`
   - El código Python usa `pathlib.Path` que maneja esto automáticamente
   - Los scripts batch usan `\` pero también funcionan con `/`

2. **Variables de entorno:**
   - CMD: `set VARIABLE=valor`
   - PowerShell: `$env:VARIABLE="valor"`

3. **Ejecución de scripts:**
   - `.bat` para CMD
   - `.ps1` para PowerShell
   - Ambos requieren permisos de ejecución

## Recursos Adicionales

- **Documentación completa:** Ver `README.md`
- **Solución de problemas:** Ver `docs/guides/TROUBLESHOOTING.md`
- **Políticas IAM:** Ver `policies/README-IAM-POLICIES.md`

## Soporte

Si encuentras problemas específicos de Windows, verifica:
1. Versión de Python: `python --version` (debe ser 3.9+)
2. Permisos de ejecución de scripts (PowerShell)
3. Variables de entorno configuradas correctamente
4. Credenciales AWS configuradas


