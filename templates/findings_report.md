# Reporte de Hallazgos - AWS Cloud Architecture Diagnostic

**Fecha:** {{ date }}

---

## Resumen

- **Total de Hallazgos:** {{ total_findings }}
- **Por Severidad:**
  - **Alta:** {{ findings_by_severity.get('high', 0) }}
  - **Media:** {{ findings_by_severity.get('medium', 0) }}
  - **Baja:** {{ findings_by_severity.get('low', 0) }}
  - **Informativo:** {{ findings_by_severity.get('info', 0) }}

---

## Hallazgos por Dominio

{% for domain, domain_findings in findings_by_domain.items() %}

### {{ domain }}

{% for finding in domain_findings %}
#### {{ finding.title }} ({{ finding.id }})

- **Severidad:** {{ finding.severity }}
- **Impacto:** {{ finding.impact }}
- **Esfuerzo:** {{ finding.effort }}
- **Descripción:** {{ finding.description }}
- **Recomendación:** {{ finding.recommendation }}

{% endfor %}

{% endfor %}

---

## Tabla Resumen de Hallazgos

| ID | Dominio | Severidad | Impacto | Esfuerzo | Título |
|----|---------|-----------|---------|----------|--------|
{% for finding in all_findings %}| {{ finding.id }} | {{ finding.domain }} | {{ finding.severity }} | {{ finding.impact }} | {{ finding.effort }} | {{ finding.title }} |
{% endfor %}

---

## Priorización Recomendada

Los hallazgos están priorizados considerando:
- **Severidad**: Impacto en seguridad, confiabilidad o costo
- **Esfuerzo**: Complejidad de implementación
- **Impacto**: Beneficio esperado

Se recomienda abordar primero los hallazgos de **severidad alta** con **esfuerzo bajo**, seguidos de aquellos con **mayor impacto** en el negocio.


