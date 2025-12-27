# 📊 Inventario de Servicios - AWS Cloud Architecture Diagnostic

**Fecha de Generación:** {{ date }}  
**Account ID:** {{ account_id }}

---

## 📈 Resumen Ejecutivo

### Métricas Principales

| Métrica | Valor |
|---------|-------|
| **Servicios Detectados** | **{{ services_count }}** |
| **Regiones Activas** | **{{ regions_count }}** |
| **Operaciones Ejecutadas** | **{{ total_operations }}** |
| **Recursos Estimados** | **{{ total_resources }}** |

---

## 📑 Detalle por Servicio

> **Nota:** A continuación se muestra el detalle completo de cada servicio, incluyendo operaciones por región y lista de operaciones ejecutadas.

{% for service_name, service_data in services.items() %}

### {{ service_name }}

- **Regiones Activas:** {{ service_data.get('regions', []) | join(', ') if service_data.get('regions') else 'N/A' }}
- **Total de Operaciones:** {{ service_data.get('total_operations', 0) }}
- **Operaciones Exitosas:** {{ service_data.get('successful_operations', 0) }}
- **Operaciones Fallidas:** {{ service_data.get('failed_operations', 0) }}
- **Recursos Estimados:** {{ service_data.get('resource_count', 0) }}

#### Operaciones por Región

{% if service_data.get('regions_data') %}
{% for region_name, region_data in service_data.get('regions_data', {}).items() %}
- **{{ region_name }}**:
  - Operaciones: {{ region_data.get('count', 0) }}
  - Exitosas: {{ region_data.get('successful', 0) }}
  - Fallidas: {{ region_data.get('failed', 0) }}
{% endfor %}
{% elif service_data.get('regions') %}
{% for region in service_data.get('regions', []) %}
- **{{ region }}**
{% endfor %}
{% else %}
- No hay datos de regiones disponibles
{% endif %}

#### Lista de Operaciones

{% for op in service_data.get('operations', [])[:20] %}
- {{ op }}
{% endfor %}
{% if service_data.get('operations', []) | length > 20 %}
- ... y {{ service_data.get('operations', []) | length - 20 }} más
{% endif %}

---

{% endfor %}

## Regiones Activas

{% for region in regions %}
- **{{ region }}**
{% endfor %}

---

## Top Servicios por Operaciones

{% for service in top_services_by_operations %}
- **{{ service.service }}**: {{ service.count }} operaciones
{% endfor %}

---

## Estadísticas de Recolección

- **Tiempo Total:** {{ stats.get('elapsed_seconds', 0) | round(2) }} segundos
- **Operaciones Ejecutadas:** {{ stats.get('operations_executed', 0) }}
- **Operaciones Exitosas:** {{ stats.get('operations_successful', 0) }}
- **Operaciones Fallidas:** {{ stats.get('operations_failed', 0) }}
- **Operaciones Omitidas:** {{ stats.get('operations_skipped', 0) }}

---

**Nota:** Este inventario se genera desde los datos recolectados. Algunos servicios pueden mostrar 0 recursos si todas las operaciones fallaron o si no hay recursos en esa región.

