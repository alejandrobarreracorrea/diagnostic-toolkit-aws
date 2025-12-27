# Well-Architected Framework - Evidence Pack

**Generado:** 2025-12-25T23:17:35.375359
**Account ID:** 123456789012

## Operational Excellence

**Resumen:** 2 servicios operacionales detectados

### Evidencias

- ✅ **CloudWatch**: CloudWatch está en uso
- ✅ **CloudFormation**: CloudFormation está en uso

### Preguntas Sugeridas para Workshop

1. ¿Se están usando métricas personalizadas?
2. ¿Hay dashboards configurados?
3. ¿Se están configurando alarmas para métricas críticas?
4. ¿Se está usando Infrastructure as Code para todos los recursos?
5. ¿Se están usando StackSets para múltiples cuentas/regiones?

---

## Security

**Resumen:** 2 servicios de seguridad detectados

### Evidencias

- ✅ **Security Hub**: AWS Security Hub está habilitado o accesible
- ❌ **AWS Config**: AWS Config no está habilitado o no es accesible
  - *Gap:* Falta de auditoría de cambios de configuración
- ❌ **CloudTrail**: AWS CloudTrail no está habilitado o no es accesible
  - *Gap:* CRÍTICO: Falta de auditoría de actividad de API
- ✅ **IAM**: IAM está accesible
- ❌ **GuardDuty**: Amazon GuardDuty no está habilitado
  - *Gap:* Falta de detección de amenazas
- ℹ️ **public_resources**: Revisar manualmente recursos con IPs públicas o acceso público

### Preguntas Sugeridas para Workshop

1. ¿Está Security Hub configurado para todas las regiones activas?
2. ¿Se están revisando regularmente los findings de Security Hub?
3. ¿Cómo se auditan los cambios de configuración sin Config?
4. ¿Por qué no se está usando CloudTrail? (CRÍTICO)
5. ¿Se está usando MFA para usuarios con privilegios?
6. ¿Se revisan regularmente las políticas IAM?
7. ¿Se usan roles en lugar de usuarios para aplicaciones?
8. ¿Qué recursos tienen acceso público y por qué?
9. ¿Se están usando Security Groups y NACLs correctamente?

---

## Reliability

**Resumen:** 2 servicios de confiabilidad detectados

### Evidencias

- ✅ **Auto Scaling**: Auto Scaling Groups están en uso
- ✅ **RDS**: RDS está en uso

### Preguntas Sugeridas para Workshop

1. ¿Las Auto Scaling Groups están configuradas con health checks adecuados?
2. ¿Las políticas de escalado están optimizadas?
3. ¿Las instancias RDS críticas están configuradas con Multi-AZ?
4. ¿Se están usando backups automáticos?
5. ¿Se han probado los procedimientos de failover?

---

## Performance Efficiency

**Resumen:** 1 servicios de performance detectados

### Evidencias

- ✅ **Auto Scaling**: Auto Scaling puede ayudar con performance

### Preguntas Sugeridas para Workshop

1. ¿Las políticas de escalado responden adecuadamente a la carga?

---

## Cost Optimization

**Resumen:** 1 regiones activas, 0 servicios de costo detectados

### Evidencias

- ❌ **Cost Explorer**: Cost Explorer no accesible
  - *Gap:* Limitada visibilidad de costos
- ℹ️ **reserved_instances**: Revisar oportunidad de Reserved Instances o Savings Plans

### Preguntas Sugeridas para Workshop

1. ¿Se están usando Reserved Instances o Savings Plans?
2. ¿Se han evaluado instancias que podrían usar tipos más económicos?

---

## Sustainability

**Resumen:** 2 servicios relevantes para sostenibilidad

### Evidencias

- ℹ️ **regions**: 1 regiones en uso
- ✅ **Auto Scaling**: Auto Scaling ayuda a usar solo recursos necesarios
- ✅ **Lambda**: Lambda (serverless) es más eficiente energéticamente

### Preguntas Sugeridas para Workshop

1. ¿Se han considerado regiones con energía renovable?
2. ¿Se están usando servicios serverless cuando es posible?

---
