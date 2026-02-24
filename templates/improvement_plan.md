# Plan de mejoras (Well-Architected Improvement Plan)

**Fecha:** {{ date }}

Este documento estructura las mejoras identificadas en el diagnóstico según el enfoque del **AWS Well-Architected Tool**: **High Risk Issues (HRI)** para pronta solución y **Medium Risk Issues (MRI)** clasificadas por complejidad de implementación.

---

## 1. Pronta solución (High Risk Issues – HRI)

**Objetivo:** Atender primero los hallazgos de alto riesgo que pueden impactar de forma significativa la operación, la seguridad o los activos.

{% for finding in improvement_plan_hri %}
### {{ finding.title }} ({{ finding.id }})

- **Dominio:** {{ finding.domain }}
- **Riesgo:** Alto (HRI)
{% if finding.source %}- **Origen:** {{ finding.source }}
{% endif %}- **Impacto:** {{ finding.impact }}
- **Descripción:** {{ finding.description }}
- **Recomendación:** {{ finding.recommendation }}

{% endfor %}
{% if not improvement_plan_hri %}
*No se identificaron hallazgos de alto riesgo (HRI) en este diagnóstico.*
{% endif %}

---

## 2. Mejoras de complejidad media (Medium Risk Issues – MRI)

**Objetivo:** Mejoras de riesgo medio con esfuerzo de implementación bajo o moderado.

{% for finding in improvement_plan_mri_media %}
### {{ finding.title }} ({{ finding.id }})

- **Dominio:** {{ finding.domain }}
- **Riesgo:** Medio (MRI) – complejidad media
{% if finding.source %}- **Origen:** {{ finding.source }}{% if finding.category %} – {{ finding.category }}{% endif %}
{% endif %}- **Impacto:** {{ finding.impact }}
- **Esfuerzo:** {{ finding.effort }}
- **Descripción:** {{ finding.description }}
- **Recomendación:** {{ finding.recommendation }}

{% endfor %}
{% if not improvement_plan_mri_media %}
*No hay MRI de complejidad media en este diagnóstico.*
{% endif %}

---

## 3. Mejoras de complejidad alta (Medium Risk Issues – MRI)

**Objetivo:** Mejoras de riesgo medio que requieren mayor planificación, coordinación o esfuerzo.

{% for finding in improvement_plan_mri_alto %}
### {{ finding.title }} ({{ finding.id }})

- **Dominio:** {{ finding.domain }}
- **Riesgo:** Medio (MRI) – complejidad alta
{% if finding.source %}- **Origen:** {{ finding.source }}{% if finding.category %} – {{ finding.category }}{% endif %}
{% endif %}- **Impacto:** {{ finding.impact }}
- **Esfuerzo:** {{ finding.effort }}
- **Descripción:** {{ finding.description }}
- **Recomendación:** {{ finding.recommendation }}

{% endfor %}
{% if not improvement_plan_mri_alto %}
*No hay MRI de complejidad alta en este diagnóstico.*
{% endif %}

---

## Notas de implementación

- Este plan de mejoras es una guía sugerida alineada con el [AWS Well-Architected Tool](https://docs.aws.amazon.com/wellarchitected/latest/userguide/waf.html) y el improvement plan por nivel de riesgo (HRI/MRI).
- Se recomienda validar prioridades con el equipo técnico y stakeholders.
- Algunas mejoras pueden requerir aprobaciones adicionales o cambios organizacionales.
- Revisar dependencias entre mejoras antes de implementar.

---

## Métricas de éxito

- **Pronta solución:** % de HRI abordados.
- **MRI complejidad media:** % de mejoras de complejidad media completadas.
- **MRI complejidad alta:** % de mejoras de complejidad alta iniciadas o completadas.

Re-evaluar la arquitectura tras implementar las mejoras para medir el impacto.
