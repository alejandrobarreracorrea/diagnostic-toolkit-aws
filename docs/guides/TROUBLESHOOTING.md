# Troubleshooting - Problemas Comunes

## Problema: No se recolectan datos (directorio raw vacío)

### Síntomas
- El collector se ejecuta sin errores
- `collection_stats.json` muestra `operations_executed: 0`
- El directorio `raw/` está vacío

### Posibles Causas y Soluciones

#### 1. Permisos Insuficientes

**Verificar:**
```bash
aws sts get-caller-identity
```

**Solución:**
- Verificar que las credenciales tengan permisos ReadOnly
- Revisar `docs/security.md` para la política IAM recomendada
- Verificar que el rol IAM tenga la política correcta adjunta
- Ver `policies/README-IAM-POLICIES.md` para implementación de políticas

#### 2. Operaciones Filtradas

El collector filtra operaciones que:
- No existen en el cliente boto3 (normal, no es un error)
- Requieren múltiples parámetros que no se pueden inferir

**Solución:**
- Esto es normal. El collector prioriza cobertura sobre completitud
- Algunos servicios pueden no tener operaciones "safe-to-call"
- Revisar logs con `--log-level DEBUG` para ver qué operaciones se están filtrando

#### 3. Región Incorrecta

**Verificar:**
```bash
# Ver qué región se está usando
cat runs/run-*/metadata.json | grep region
```

**Solución:**
- Especificar regiones explícitamente:
  ```bash
  export AWS_REGIONS=us-east-1,us-west-2
  make collect
  ```

#### 4. Servicios Filtrados

**Verificar:**
- Revisar `service_allowlist` o `service_denylist` en configuración

**Solución:**
- Si usas allowlist, asegúrate de incluir servicios comunes:
  ```bash
  export ECAD_SERVICE_ALLOWLIST=ec2,s3,rds,lambda,iam
  ```

### Diagnóstico

Ejecutar con logging detallado:

```bash
python3 -m collector.main \
  --output-dir ./runs/test-run \
  --max-threads 5 \
  2>&1 | tee collection.log
```

Luego revisar:
- ¿Cuántas operaciones se descubren?
- ¿Cuántas son "safe_to_call"?
- ¿Hay errores de permisos?

### Verificación Manual

Probar manualmente una operación:

```python
import boto3
client = boto3.client('ec2', region_name='us-east-1')
result = client.describe_regions()
print(result)
```

Si esto funciona, el problema está en el collector. Si no, es un problema de permisos/credenciales.

---

## Problema: Muchos Warnings de "has no attribute"

### Síntomas
- Muchos mensajes: `'ServiceName' object has no attribute 'OperationName'`

### Explicación
Esto es **normal**. El modelo de botocore puede tener operaciones definidas que no están disponibles en todas las versiones de boto3 o en todos los clientes.

### Solución
- Los warnings se han cambiado a DEBUG en la versión actualizada
- No afecta la funcionalidad
- El collector filtra estas operaciones automáticamente

---

## Problema: Throttling (Rate Limiting)

### Síntomas
- Errores: `Throttling`, `TooManyRequestsException`
- Recolección muy lenta

### Solución
```bash
# Reducir threads
export ECAD_MAX_THREADS=5
make collect

# O especificar en el comando
python3 -m collector.main --max-threads 5 ...
```

El collector aplica backoff automático, pero puede tardar más.

---

## Problema: AccessDenied

### Síntomas
- Errores: `AccessDenied`, `UnauthorizedOperation`

### Solución
1. Verificar política IAM (ver `docs/security.md` y `policies/README-IAM-POLICIES.md`)
2. Verificar que el rol tenga los permisos correctos
3. Si usas AssumeRole, verificar ExternalId

---

## Verificar Datos Recolectados

```bash
# Ver estructura
find runs/run-*/raw -type f | head -20

# Ver estadísticas
cat runs/run-*/collection_stats.json

# Ver metadatos
cat runs/run-*/metadata.json

# Contar archivos recolectados
find runs/run-*/raw -name "*.json.gz" | wc -l
```

---

## Herramientas de Diagnóstico

El proyecto incluye herramientas en `tools/` para diagnosticar problemas:

- `tools/analyze_errors.py` - Analizar errores en un run
- `tools/diagnose_collection.py` - Diagnosticar problemas de recolección
- `tools/test_collect_simple.py` - Test simple de recolección

---

## Contacto

Si el problema persiste después de revisar estas soluciones, proporcionar:
1. Salida de `collection_stats.json`
2. Logs con `--log-level DEBUG`
3. Resultado de `aws sts get-caller-identity`


