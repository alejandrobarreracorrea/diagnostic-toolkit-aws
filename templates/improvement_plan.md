# Plan de mejoras (Well-Architected Improvement Plan)

**Fecha:** {{ date }}

**Framework evaluado:** AWS Well-Architected Framework (versión {{ well_arch_version }})

Este documento estructura las mejoras en **dos clasificaciones**: **Pronta solución (30 días)** —tareas realizables en el corto plazo— y **Medium Risk Issues (MRI)** —mejoras que requieren mayor planificación o esfuerzo.

---

<div class="improvement-section improvement-pronta">

## 1. Pronta solución (30 días)

**Objetivo:** Tareas que se pueden abordar en un plazo de 30 días (esfuerzo bajo, quick wins). Priorizar estas para obtener avances visibles de forma rápida.

{% for finding in improvement_plan_pronta %}
### {{ finding.title }} ({{ finding.id }})

- **Dominio:** {{ finding.domain }}
{% if finding.source %}- **Origen:** {{ finding.source }}{% if finding.category %} – {{ finding.category }}{% endif %}
{% endif %}- **Impacto:** {{ finding.impact }}
- **Descripción:** {{ finding.description }}
- **Recomendación:** {{ finding.recommendation }}

{% endfor %}
{% if not improvement_plan_pronta %}
*No se identificaron tareas de pronta solución (30 días) en este diagnóstico.*
{% endif %}

</div>

---

<div class="improvement-section improvement-mri">

## 2. Mejoras de mayor complejidad (MRI)

**Objetivo:** Mejoras de riesgo medio que requieren mayor planificación, coordinación o esfuerzo (más de 30 días). Incluye hallazgos de mayor impacto y capacidades que exigen cambios estructurales o organizacionales.

{% for finding in improvement_plan_mri %}
### {{ finding.title }} ({{ finding.id }})

- **Dominio:** {{ finding.domain }}
- **Riesgo:** Medio (MRI)
{% if finding.source %}- **Origen:** {{ finding.source }}{% if finding.category %} – {{ finding.category }}{% endif %}
{% endif %}- **Impacto:** {{ finding.impact }}
{% if finding.effort %}- **Esfuerzo:** {{ finding.effort }}
{% endif %}- **Descripción:** {{ finding.description }}
- **Recomendación:** {{ finding.recommendation }}

{% endfor %}
{% if not improvement_plan_mri %}
*No hay MRI en este diagnóstico.*
{% endif %}

</div>

---

## Notas de implementación

- Este plan está alineado con el [AWS Well-Architected Tool](https://docs.aws.amazon.com/wellarchitected/latest/userguide/waf.html) y el modelo de mejora por plazo (pronta solución / MRI).
- Validar prioridades con el equipo técnico y stakeholders.
- Algunas mejoras pueden requerir aprobaciones adicionales o cambios organizacionales.
- Revisar dependencias entre mejoras antes de implementar.

---

## Métricas de éxito

- **Pronta solución (30 días):** % de tareas de pronta solución completadas.
- **MRI:** % de mejoras de mayor complejidad iniciadas o completadas.

Re-evaluar la arquitectura tras implementar las mejoras para medir el impacto.
