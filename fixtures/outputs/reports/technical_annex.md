# Anexo Técnico - AWS Cloud Architecture Diagnostic

**Fecha:** 2026-01-06

---

## Inventario Detallado

Este anexo contiene el inventario técnico completo de recursos AWS detectados durante el diagnóstico.

---

## Resumen de Recolección


- **Tiempo de Recolección:** 1234.56 segundos
- **Operaciones Ejecutadas:** 234
- **Operaciones Exitosas:** 220
- **Operaciones Fallidas:** 14
- **Timestamp:** 2024-01-15T10:30:00


---

## Servicios Detectados



### autoscaling

- **Regiones:** us-east-1
- **Operaciones Totales:** 1
- **Operaciones Únicas:** 1

#### Operaciones por Región


- **us-east-1**: 1 operaciones




### cloudformation

- **Regiones:** us-east-1
- **Operaciones Totales:** 1
- **Operaciones Únicas:** 1

#### Operaciones por Región


- **us-east-1**: 1 operaciones




### cloudwatch

- **Regiones:** us-east-1
- **Operaciones Totales:** 1
- **Operaciones Únicas:** 1

#### Operaciones por Región


- **us-east-1**: 1 operaciones




### ec2

- **Regiones:** us-east-1
- **Operaciones Totales:** 2
- **Operaciones Únicas:** 2

#### Operaciones por Región


- **us-east-1**: 2 operaciones




### iam

- **Regiones:** us-east-1
- **Operaciones Totales:** 2
- **Operaciones Únicas:** 2

#### Operaciones por Región


- **us-east-1**: 2 operaciones




### lambda

- **Regiones:** us-east-1
- **Operaciones Totales:** 1
- **Operaciones Únicas:** 1

#### Operaciones por Región


- **us-east-1**: 1 operaciones




### rds

- **Regiones:** us-east-1
- **Operaciones Totales:** 1
- **Operaciones Únicas:** 1

#### Operaciones por Región


- **us-east-1**: 1 operaciones




### s3

- **Regiones:** us-east-1
- **Operaciones Totales:** 2
- **Operaciones Únicas:** 2

#### Operaciones por Región


- **us-east-1**: 2 operaciones




### securityhub

- **Regiones:** us-east-1
- **Operaciones Totales:** 1
- **Operaciones Únicas:** 1

#### Operaciones por Región


- **us-east-1**: 1 operaciones




---

## Regiones Activas


- **us-east-1**


---

## Inventario por Servicio


### Top Servicios por Recursos


- **iam**: 2 recursos

- **lambda**: 2 recursos

- **s3**: 2 recursos

- **ec2**: 1 recursos

- **autoscaling**: 0 recursos

- **cloudformation**: 0 recursos

- **cloudwatch**: 0 recursos

- **rds**: 0 recursos

- **securityhub**: 0 recursos


### Top Regiones por Recursos


- **us-east-1**: 7 recursos


### Total de Recursos Estimados

**7** recursos en total



---

## Estructura de Datos Recolectados

Los datos recolectados se almacenan en la siguiente estructura:

```
raw/
├── {service}/
│   ├── {region}/
│   │   ├── {operation}.json.gz
│   │   └── ...
│   └── ...
└── ...
```

Cada archivo `.json.gz` contiene:
- **Metadata**: Información sobre la operación (servicio, región, timestamp, etc.)
- **Data**: Resultado de la operación (si fue exitosa)
- **Error**: Información de error (si aplica)

---

## Limitaciones del Inventario

- Algunos servicios pueden requerir parámetros específicos que no se pueden inferir automáticamente
- El conteo de recursos es una estimación basada en respuestas de operaciones List/Describe
- Algunos recursos pueden no ser detectados si requieren permisos adicionales
- Los recursos en regiones no especificadas pueden no ser detectados

---

## Notas Técnicas

- Todos los datos se recolectaron usando permisos ReadOnly
- Se aplicaron límites de paginación para evitar llamadas excesivas
- Se implementó retry automático para manejo de throttling
- Los datos están comprimidos en formato gzip para eficiencia de almacenamiento

