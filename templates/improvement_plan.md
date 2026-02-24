# Plan de mejoras (Well-Architected Improvement Plan)

**Fecha:** {{ date }}

**Framework evaluado:** AWS Well-Architected Framework (versión {{ well_arch_version }})

<p>
Este documento estructura las mejoras en <strong>dos clasificaciones</strong>:
</p>
<ul>
  <li><strong>Pronta solución (30 días)</strong>: tareas realizables en el corto plazo (esfuerzo bajo, quick wins).</li>
  <li><strong>Medium Risk Issues (MRI)</strong>: mejoras que requieren mayor planificación, coordinación o esfuerzo.</li>
</ul>

<p>Las acciones se construyen a partir de tres fuentes:</p>
<ul>
  <li><strong>Hallazgos</strong>: problemas detectados automáticamente en la cuenta.</li>
  <li><strong>Evidence Pack</strong>: preguntas del Well-Architected con cumplimiento parcial o no cumplido.</li>
  <li><strong>Modelo de Madurez</strong>: capacidades de seguridad en estado parcial o no cumplido.</li>
</ul>

---

<div class="improvement-section improvement-pronta">

<h2>1. Pronta solución (30 días)</h2>

<p><strong>Objetivo:</strong> Tareas que se pueden abordar en un plazo de 30 días (esfuerzo bajo, quick wins). Priorizar estas para obtener avances visibles de forma rápida.</p>

{% for finding in improvement_plan_pronta %}
<h3>{{ finding.title }} ({{ finding.id }})</h3>

<ul>
  <li><strong>Dominio:</strong> {{ finding.domain }}</li>
  {% if finding.source %}<li><strong>Origen:</strong> {{ finding.source }}{% if finding.category %} – {{ finding.category }}{% endif %}</li>{% endif %}
  <li><strong>Impacto estimado:</strong> {{ finding.impact }}</li>
  <li><strong>Descripción actual:</strong> {{ finding.description }}</li>
  <li><strong>Recomendación prioritaria:</strong> {{ finding.recommendation }}</li>
</ul>

<hr />

{% endfor %}
{% if not improvement_plan_pronta %}
<p><em>No se identificaron tareas de pronta solución (30 días) en este diagnóstico.</em></p>
{% endif %}

</div>

---

<div class="improvement-section improvement-mri">

<h2>2. Mejoras de mayor complejidad (MRI)</h2>

<p><strong>Objetivo:</strong> Mejoras de riesgo medio que requieren mayor planificación, coordinación o esfuerzo (más de 30 días). Incluye hallazgos de mayor impacto y capacidades que exigen cambios estructurales o organizacionales.</p>

{% for finding in improvement_plan_mri %}
<h3>{{ finding.title }} ({{ finding.id }})</h3>

<ul>
  <li><strong>Dominio:</strong> {{ finding.domain }}</li>
  <li><strong>Riesgo:</strong> Medio (MRI)</li>
  {% if finding.source %}<li><strong>Origen:</strong> {{ finding.source }}{% if finding.category %} – {{ finding.category }}{% endif %}</li>{% endif %}
  <li><strong>Impacto estimado:</strong> {{ finding.impact }}</li>
  {% if finding.effort %}<li><strong>Esfuerzo estimado:</strong> {{ finding.effort }}</li>{% endif %}
  <li><strong>Descripción actual:</strong> {{ finding.description }}</li>
  <li><strong>Recomendación prioritaria:</strong> {{ finding.recommendation }}</li>
</ul>

<hr />

{% endfor %}
{% if not improvement_plan_mri %}
<p><em>No hay MRI en este diagnóstico.</em></p>
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
