# Anexo Técnico - AWS Cloud Architecture Diagnostic

**Fecha:** {{ date }}

---

## Inventario Detallado

Este anexo contiene el inventario técnico completo de recursos AWS detectados durante el diagnóstico.

---

## Resumen de Recolección

{% if stats %}
- **Tiempo de Recolección:** {{ stats.get('elapsed_seconds', 0) | round(2) }} segundos
- **Operaciones Ejecutadas:** {{ stats.get('operations_executed', 0) }}
- **Operaciones Exitosas:** {{ stats.get('operations_successful', 0) }}
- **Operaciones Fallidas:** {{ stats.get('operations_failed', 0) }}
- **Timestamp:** {{ stats.get('timestamp', 'N/A') }}
{% endif %}

---

## Servicios Detectados

{% for service_name, service_data in services.items() %}

### {{ service_name }}

- **Regiones:** {{ service_data.get('regions', []) | join(', ') }}
- **Operaciones Totales:** {{ service_data.get('total_operations', 0) }}
- **Operaciones Únicas:** {{ service_data.get('operations', []) | length }}

#### Operaciones por Región

{% for region_name, region_data in service_data.get('regions', {}).items() %}
- **{{ region_name }}**: {{ region_data.get('count', 0) }} operaciones
{% endfor %}

{% endfor %}

---

## Regiones Activas

{% for region in regions %}
- **{{ region }}**
{% endfor %}

---

## Inventario por Servicio

{% if inventory %}
### Top Servicios por Recursos

{% for service in inventory.get('top_services', [])[:20] %}
- **{{ service.service }}**: {{ service.count }} recursos
{% endfor %}

### Top Regiones por Recursos

{% for region in inventory.get('top_regions', [])[:10] %}
- **{{ region.region }}**: {{ region.count }} recursos
{% endfor %}

### Total de Recursos Estimados

**{{ inventory.get('total_resources', 0) }}** recursos en total

{% endif %}

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


