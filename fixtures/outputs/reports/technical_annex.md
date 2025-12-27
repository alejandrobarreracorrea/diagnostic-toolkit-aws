# Anexo Técnico - AWS Cloud Architecture Diagnostic

**Fecha:** 2025-12-25

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



### cloudwatch

- **Regiones:** us-east-1
- **Operaciones Totales:** 1
- **Operaciones Únicas:** 19

#### Operaciones por Región


- **us-east-1**: 1 operaciones




### s3

- **Regiones:** us-east-1
- **Operaciones Totales:** 2
- **Operaciones Únicas:** 39

#### Operaciones por Región


- **us-east-1**: 2 operaciones




### iam

- **Regiones:** us-east-1
- **Operaciones Totales:** 2
- **Operaciones Únicas:** 28

#### Operaciones por Región


- **us-east-1**: 2 operaciones




### lambda

- **Regiones:** us-east-1
- **Operaciones Totales:** 1
- **Operaciones Únicas:** 18

#### Operaciones por Región


- **us-east-1**: 1 operaciones




### autoscaling

- **Regiones:** us-east-1
- **Operaciones Totales:** 1
- **Operaciones Únicas:** 32

#### Operaciones por Región


- **us-east-1**: 1 operaciones




### securityhub

- **Regiones:** us-east-1
- **Operaciones Totales:** 1
- **Operaciones Únicas:** 16

#### Operaciones por Región


- **us-east-1**: 1 operaciones




### cloudformation

- **Regiones:** us-east-1
- **Operaciones Totales:** 1
- **Operaciones Únicas:** 19

#### Operaciones por Región


- **us-east-1**: 1 operaciones




### rds

- **Regiones:** us-east-1
- **Operaciones Totales:** 1
- **Operaciones Únicas:** 25

#### Operaciones por Región


- **us-east-1**: 1 operaciones




### ec2

- **Regiones:** us-east-1
- **Operaciones Totales:** 2
- **Operaciones Únicas:** 39

#### Operaciones por Región


- **us-east-1**: 2 operaciones




---

## Regiones Activas


- **us-east-1**


---

## Inventario por Servicio


### Top Servicios por Recursos


- **s3**: 2 recursos

- **iam**: 2 recursos

- **ec2**: 2 recursos

- **cloudwatch**: 1 recursos

- **lambda**: 1 recursos

- **autoscaling**: 1 recursos

- **cloudformation**: 1 recursos

- **rds**: 1 recursos

- **securityhub**: 0 recursos


### Top Regiones por Recursos


- **us-east-1**: 11 recursos


### Total de Recursos Estimados

**11** recursos en total



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
