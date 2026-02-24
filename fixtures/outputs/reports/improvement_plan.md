# Plan de mejoras (Well-Architected Improvement Plan)

**Fecha:** 2026-01-06

Este documento estructura las mejoras identificadas en el diagnóstico según el enfoque del **AWS Well-Architected Tool**: **High Risk Issues (HRI)** para pronta solución y **Medium Risk Issues (MRI)** clasificadas por complejidad de implementación.

---

## 1. Pronta solución (High Risk Issues – HRI)

**Objetivo:** Atender primero los hallazgos de alto riesgo que pueden impactar de forma significativa la operación, la seguridad o los activos.

### CloudTrail no detectado (SEC-003)

- **Dominio:** Security
- **Riesgo:** Alto (HRI)
- **Impacto:** Falta de auditoría de actividad de API
- **Descripción:** AWS CloudTrail no está habilitado o no se pudo acceder. CloudTrail es esencial para auditoría y cumplimiento.
- **Recomendación:** Habilitar CloudTrail en todas las regiones para registro de actividad de API.

---

## 2. Mejoras de complejidad media (Medium Risk Issues – MRI)

**Objetivo:** Mejoras de riesgo medio con esfuerzo de implementación bajo o moderado.

*No hay MRI de complejidad media en este diagnóstico.*

---

## 3. Mejoras de complejidad alta (Medium Risk Issues – MRI)

**Objetivo:** Mejoras de riesgo medio que requieren mayor planificación, coordinación o esfuerzo.

### AWS Config no detectado (SEC-002)

- **Dominio:** Security
- **Riesgo:** Medio (MRI) – complejidad alta
- **Impacto:** Falta de visibilidad de cambios de configuración
- **Esfuerzo:** Medio
- **Descripción:** AWS Config no está habilitado o no se pudo acceder. Config permite auditoría y cumplimiento continuo.
- **Recomendación:** Habilitar AWS Config para auditoría y cumplimiento continuo.

### RDS detectado - Verificar configuración Multi-AZ (REL-001)

- **Dominio:** Reliability
- **Riesgo:** Medio (MRI) – complejidad alta
- **Impacto:** Posible falta de alta disponibilidad en bases de datos
- **Esfuerzo:** Medio
- **Descripción:** Se detectó uso de RDS. Se recomienda verificar que las instancias críticas estén configuradas con Multi-AZ para alta disponibilidad.
- **Recomendación:** Revisar configuración de instancias RDS y habilitar Multi-AZ para bases de datos críticas.

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
