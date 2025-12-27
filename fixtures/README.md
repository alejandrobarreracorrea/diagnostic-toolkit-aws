# Fixtures - Datos de Ejemplo para Demo

Este directorio contiene datos de ejemplo (golden files) para ejecutar ECAD en modo demo sin necesidad de credenciales AWS.

## Uso

Para ejecutar el demo:

```bash
make demo
```

O manualmente:

```bash
python -m analyzer.main --run-dir ./fixtures
python -m evidence.generator --run-dir ./fixtures
python -m analyzer.report_generator --run-dir ./fixtures
```

## Estructura

Los fixtures deben seguir la misma estructura que un run real:

```
fixtures/
├── raw/
│   ├── {service}/
│   │   ├── {region}/
│   │   │   ├── {operation}.json.gz
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── metadata.json
└── collection_stats.json
```

## Crear Fixtures desde un Run Real

Para crear fixtures desde un run real (útil para demos con datos reales anonimizados):

```bash
# Copiar un run completo
cp -r ./runs/run-YYYYMMDD-HHMMSS ./fixtures

# O crear fixtures mínimos para demo
mkdir -p fixtures/raw
# Agregar archivos de ejemplo manualmente
```

## Fixtures Mínimos

Los fixtures mínimos deben incluir al menos:

- `metadata.json`: Metadatos de cuenta (con account_id anonimizado)
- `raw/`: Al menos algunos servicios de ejemplo (EC2, S3, RDS, etc.)
- `collection_stats.json`: Estadísticas de recolección

## Nota sobre Datos Sensibles

Si se crean fixtures desde datos reales:

1. **Anonimizar Account IDs**: Reemplazar con valores de ejemplo
2. **Remover Datos Sensibles**: No incluir contenido de datos, solo metadatos
3. **Revisar ARNs**: Asegurar que no contengan información sensible
4. **Tags**: Revisar tags que puedan contener información sensible


