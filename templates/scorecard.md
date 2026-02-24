# Well-Architected Scorecard - AWS Cloud Architecture Diagnostic

**Fecha:** {{ date }}

**Framework evaluado:** AWS Well-Architected Framework (versión {{ well_arch_version }})

---

## Resumen de Scores

Este scorecard evalúa la arquitectura AWS según los 6 pilares del Well-Architected Framework (versión {{ well_arch_version }}). Los scores van de 1 (crítico) a 5 (excelente).

**Score Promedio:** {{ "%.1f" | format(average_score) }}/5.0

---

## Scores por Pilar

{% for domain, score in domain_scores.items() %}

### {{ domain }}

**Score: {{ score }}/5**

{% if score == 5 %}
✅ **Excelente** - No se identificaron problemas significativos en este pilar.
{% elif score == 4 %}
✅ **Bueno** - Arquitectura sólida con oportunidades menores de mejora.
{% elif score == 3 %}
⚠️ **Aceptable** - Arquitectura funcional pero con áreas de mejora identificadas.
{% elif score == 2 %}
⚠️ **Necesita Mejora** - Se identificaron problemas que requieren atención.
{% else %}
❌ **Crítico** - Se identificaron problemas críticos que requieren acción inmediata.
{% endif %}

{% endfor %}

---

## Criterios de Scoring

Los scores se calculan basándose en:

1. **Presencia de servicios clave** para cada pilar
2. **Hallazgos identificados** y su severidad
3. **Buenas prácticas** detectadas o ausentes

### Escala de Scoring

- **5 (Excelente)**: Sin hallazgos o solo hallazgos informativos
- **4 (Bueno)**: Hallazgos menores de severidad baja
- **3 (Aceptable)**: Hallazgos de severidad media o múltiples hallazgos bajos
- **2 (Necesita Mejora)**: Hallazgos de severidad alta o múltiples hallazgos medios
- **1 (Crítico)**: Múltiples hallazgos de severidad alta o problemas críticos

---

## Recomendaciones por Pilar

### Security ({{ domain_scores.get('Security', 0) }}/5)

{% if domain_scores.get('Security', 0) < 4 %}
- Revisar y habilitar servicios de seguridad faltantes (Security Hub, Config, CloudTrail)
- Implementar controles de acceso adecuados
- Revisar recursos con acceso público
{% else %}
- Mantener buenas prácticas actuales
- Continuar monitoreo y revisión periódica
{% endif %}

### Reliability ({{ domain_scores.get('Reliability', 0) }}/5)

{% if domain_scores.get('Reliability', 0) < 4 %}
- Implementar Auto Scaling donde sea apropiado
- Configurar Multi-AZ para recursos críticos
- Revisar y probar procedimientos de failover
{% else %}
- Mantener estrategias de alta disponibilidad actuales
{% endif %}

### Performance Efficiency ({{ domain_scores.get('Performance Efficiency', 0) }}/5)

{% if domain_scores.get('Performance Efficiency', 0) < 4 %}
- Optimizar uso de recursos
- Considerar servicios serverless cuando sea apropiado
- Revisar políticas de escalado
{% else %}
- Continuar optimizando según necesidad
{% endif %}

### Cost Optimization ({{ domain_scores.get('Cost Optimization', 0) }}/5)

{% if domain_scores.get('Cost Optimization', 0) < 4 %}
- Revisar uso de regiones y consolidar si es posible
- Evaluar Reserved Instances o Savings Plans
- Implementar budgets y alertas de costo
{% else %}
- Mantener prácticas de optimización de costos
{% endif %}

### Operational Excellence ({{ domain_scores.get('Operational Excellence', 0) }}/5)

{% if domain_scores.get('Operational Excellence', 0) < 4 %}
- Implementar monitoreo y observabilidad completo
- Adoptar Infrastructure as Code
- Automatizar procesos operacionales
{% else %}
- Continuar mejorando procesos operacionales
{% endif %}

### Sustainability ({{ domain_scores.get('Sustainability', 0) }}/5)

{% if domain_scores.get('Sustainability', 0) < 4 %}
- Considerar regiones con energía renovable
- Optimizar uso de recursos (usar solo lo necesario)
- Evaluar servicios serverless
{% else %}
- Mantener prácticas sostenibles actuales
{% endif %}

---

## Próximos Pasos

1. Revisar hallazgos detallados en reporte de findings
2. Priorizar mejoras según scores más bajos
3. Ejecutar workshop de Well-Architected usando evidence pack
4. Establecer plan de acción para mejorar scores

---

**Nota:** Estos scores son una evaluación inicial basada en inventario automatizado. Se recomienda complementar con revisión manual y workshops con el equipo técnico.


