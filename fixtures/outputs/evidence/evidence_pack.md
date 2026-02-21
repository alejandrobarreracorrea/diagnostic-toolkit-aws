# Well-Architected Framework - Evidence Pack

**Generado:** 2026-02-21T14:55:27.401269
**Account ID:** 123456789012

## Operational Excellence

**Resumen:** 0 servicios operacionales detectados

### Preguntas del Well-Architected Framework

#### OPS1: ¿Cómo determinas cuáles son tus prioridades?

**Estado de Cumplimiento:** ℹ️ Pregunta organizacional, no aplica a servicios de AWS

*Pregunta organizacional, no tiene servicios específicos de AWS*

**Mejores Prácticas:**
- Definir resultados de negocio y métricas de éxito
- Priorizar trabajo basado en valor de negocio y riesgo
- Revisar prioridades regularmente

#### OPS2: ¿Cómo estructuras tu organización para apoyar tus resultados de negocio?

**Estado de Cumplimiento:** ℹ️ Pregunta organizacional, no aplica a servicios de AWS

*Pregunta organizacional, no tiene servicios específicos de AWS*

**Mejores Prácticas:**
- Alinear la propiedad del equipo con las cargas de trabajo
- Usar equipos pequeños y autónomos
- Definir responsabilidades claras y rutas de escalación

#### OPS3: ¿Cómo tu cultura organizacional apoya tus resultados de negocio?

**Estado de Cumplimiento:** ℹ️ Pregunta organizacional, no aplica a servicios de AWS

*Pregunta organizacional, no tiene servicios específicos de AWS*

**Mejores Prácticas:**
- Promover mejora continua y aprendizaje
- Usar postmortems sin culpa
- Automatizar operaciones donde sea posible *(Servicios sugeridos: CloudFormation, Systems Manager, Lambda, EventBridge)*

#### OPS4: ¿Cómo monitoreas tu carga de trabajo para asegurar que opera como se espera?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **CloudWatch Alarms**: CloudWatch Alarms no está en uso o no tiene alarmas configuradas
  - *Gap:* Falta de alertas y monitoreo proactivo
- ❌ **CloudWatch Dashboards**: CloudWatch Dashboards no está en uso o no tiene dashboards configurados
  - *Gap:* Falta de visualización centralizada de métricas
- ❌ **CloudWatch Logs**: CloudWatch Logs no está en uso o no tiene log groups configurados
  - *Gap:* Falta de centralización y análisis de logs

**Servicios Relacionados:**
- ❌ CloudWatch (no detectado)
- ❌ CloudWatch Logs (no detectado)
- ❌ CloudWatch Alarms (no detectado)
- ❌ CloudWatch Dashboards (no detectado)

*Monitoreo de cargas de trabajo*

**Mejores Prácticas:**
- Recopilar métricas, logs y trazas *(Servicios sugeridos: CloudWatch, CloudWatch Logs, X-Ray)*
- Definir SLIs y SLOs *(Servicios sugeridos: CloudWatch, CloudWatch Alarms)*
- Usar dashboards y alarmas *(Servicios sugeridos: CloudWatch Dashboards, CloudWatch Alarms)*

#### OPS5: ¿Cómo respondes a eventos operacionales no planificados?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **CloudWatch Alarms**: CloudWatch Alarms no está en uso o no tiene alarmas configuradas
  - *Gap:* Falta de alertas y monitoreo proactivo
- ❌ **Systems Manager**: Systems Manager no está en uso o no tiene instancias gestionadas
  - *Gap:* Falta de gestión centralizada de instancias
- ❌ **SNS**: SNS no está en uso o no tiene topics/subscriptions configurados
  - *Gap:* Falta de notificaciones automatizadas para alarmas y eventos
- ❌ **EventBridge**: EventBridge no está en uso o no tiene rules/event buses configurados
  - *Gap:* Falta de automatización de respuestas a eventos

**Servicios Relacionados:**
- ❌ Systems Manager (no detectado)
- ❌ CloudWatch Alarms (no detectado)
- ❌ SNS (no detectado)
- ❌ EventBridge (no detectado)

*Respuesta a eventos operacionales*

**Mejores Prácticas:**
- Crear y mantener runbooks *(Servicios sugeridos: Systems Manager Documents)*
- Automatizar respuesta a incidentes *(Servicios sugeridos: EventBridge, Lambda, Systems Manager, CloudWatch Alarms)*
- Practicar simulaciones de incidentes *(Servicios sugeridos: Systems Manager, CloudFormation)*

#### OPS6: ¿Cómo se gestiona la escalación al responder a eventos operacionales no planificados?

**Estado de Cumplimiento:** ❌ No cumplido: 0/3 servicios detectados

**Evidencias Encontradas:**

- ❌ **CloudWatch Alarms**: CloudWatch Alarms no está en uso o no tiene alarmas configuradas
  - *Gap:* Falta de alertas y monitoreo proactivo
- ❌ **SNS**: SNS no está en uso o no tiene topics/subscriptions configurados
  - *Gap:* Falta de notificaciones automatizadas para alarmas y eventos
- ❌ **EventBridge**: EventBridge no está en uso o no tiene rules/event buses configurados
  - *Gap:* Falta de automatización de respuestas a eventos

**Servicios Relacionados:**
- ❌ CloudWatch Alarms (no detectado)
- ❌ SNS (no detectado)
- ❌ EventBridge (no detectado)

*Gestión de escalación*

**Mejores Prácticas:**
- Definir políticas de escalación *(Servicios sugeridos: CloudWatch Alarms, EventBridge)*
- Usar notificaciones automatizadas *(Servicios sugeridos: SNS, EventBridge, CloudWatch Alarms)*
- Asegurar cobertura 24/7 donde se requiera *(Servicios sugeridos: SNS, EventBridge, CloudWatch Alarms)*

### Preguntas Sugeridas Adicionales para Workshop

1. ¿Por qué no se está usando Systems Manager para gestionar instancias EC2?
2. ¿Por qué no se está usando CloudFormation para gestionar infraestructura como código?
3. ¿Por qué no se está usando SNS para notificaciones automatizadas?
4. ¿Por qué no se está usando EventBridge para automatizar respuestas a eventos?

---

## Security

**Resumen:** 1 servicios de seguridad detectados

### Preguntas del Well-Architected Framework

#### SEC1: ¿Cómo gestionas credenciales y autenticación?

**Estado de Cumplimiento:** ⚠️ Parcialmente cumplido: 1/3 servicios detectados

**Evidencias Encontradas:**

- ✅ **IAM**: IAM está accesible
- ❌ **Secrets Manager**: AWS Secrets Manager no está en uso o no tiene secrets
  - *Gap:* Falta de gestión centralizada de credenciales
- ❌ **KMS**: AWS KMS no está en uso o no tiene keys
  - *Gap:* Falta de gestión de claves de cifrado

**Servicios Relacionados:**
- ✅ IAM (detectado)
- ❌ Secrets Manager (no detectado)
- ❌ KMS (no detectado)

*Gestión de credenciales y autenticación*

**Mejores Prácticas:**
- Usar roles IAM en lugar de credenciales de largo plazo *(Servicios sugeridos: IAM Roles)*
- Habilitar MFA *(Servicios sugeridos: IAM)*
- Rotar credenciales automáticamente *(Servicios sugeridos: Secrets Manager, IAM)*

#### SEC2: ¿Cómo gestionas identidades para personas y máquinas?

**Estado de Cumplimiento:** ⚠️ Parcialmente cumplido: 1/3 servicios detectados

**Evidencias Encontradas:**

- ✅ **IAM**: IAM está accesible

**Servicios Relacionados:**
- ✅ IAM (detectado)
- ❌ Cognito (no detectado)
- ❌ SSO (no detectado)

*Gestión de identidades*

**Mejores Prácticas:**
- Centralizar gestión de identidades *(Servicios sugeridos: IAM, SSO, Cognito)*
- Usar acceso federado *(Servicios sugeridos: IAM Identity Center (SSO), Cognito)*
- Separar identidades humanas y de máquinas *(Servicios sugeridos: IAM)*

#### SEC3: ¿Cómo gestionas el acceso de menor privilegio?

**Estado de Cumplimiento:** ✅ Completamente cumplido: 1/1 servicios detectados

**Evidencias Encontradas:**

- ✅ **IAM**: IAM está accesible

**Servicios Relacionados:**
- ✅ IAM (detectado)

*Gestión de acceso de menor privilegio*

**Mejores Prácticas:**
- Otorgar permisos basados en función de trabajo *(Servicios sugeridos: IAM)*
- Revisar permisos regularmente *(Servicios sugeridos: IAM Access Analyzer, IAM)*
- Usar condiciones de políticas *(Servicios sugeridos: IAM)*

#### SEC4: ¿Cómo detectas e investigas eventos de seguridad?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **Security Hub**: AWS Security Hub no está habilitado
  - *Gap:* Falta de visibilidad centralizada del estado de seguridad
- ❌ **CloudTrail**: AWS CloudTrail no está habilitado
  - *Gap:* CRÍTICO: Falta de auditoría de actividad de API
- ❌ **GuardDuty**: Amazon GuardDuty no está habilitado
  - *Gap:* Falta de detección de amenazas
- ❌ **CloudWatch Logs**: CloudWatch Logs no está en uso o no tiene log groups
  - *Gap:* Falta de centralización de logs de seguridad

**Servicios Relacionados:**
- ❌ CloudTrail (no detectado)
- ❌ GuardDuty (no detectado)
- ❌ Security Hub (no detectado)
- ❌ CloudWatch Logs (no detectado)

*Detección e investigación de eventos de seguridad*

**Mejores Prácticas:**
- Habilitar CloudTrail *(Servicios sugeridos: CloudTrail)*
- Usar GuardDuty y Security Hub *(Servicios sugeridos: GuardDuty, Security Hub)*
- Centralizar logs de seguridad *(Servicios sugeridos: CloudWatch Logs, S3)*

#### SEC5: ¿Cómo proteges tus recursos de red?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ℹ️ **public_resources**: Revisar manualmente recursos con IPs públicas o acceso público

**Servicios Relacionados:**
- ❌ EC2 (no detectado)
- ❌ VPC (no detectado)
- ❌ Security Groups (no detectado)
- ❌ NACLs (no detectado)

*Protección de recursos de red*

**Mejores Prácticas:**
- Usar segmentación VPC *(Servicios sugeridos: VPC)*
- Aplicar security groups y NACLs *(Servicios sugeridos: EC2 Security Groups, VPC NACLs)*
- Limitar exposición pública *(Servicios sugeridos: Security Groups, NACLs, VPC)*

#### SEC6: ¿Cómo proteges tus recursos de cómputo?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **Systems Manager**: Systems Manager no está en uso o no tiene instancias gestionadas
  - *Gap:* Falta de gestión centralizada y hardening de instancias EC2

**Servicios Relacionados:**
- ❌ EC2 (no detectado)
- ❌ Systems Manager (no detectado)
- ❌ Inspector (no detectado)
- ❌ Security Hub (no detectado)

*Protección de recursos de cómputo*

**Mejores Prácticas:**
- Aplicar parches regularmente *(Servicios sugeridos: Systems Manager Patch Manager)*
- Usar AMIs endurecidas *(Servicios sugeridos: EC2, Systems Manager)*
- Monitorear comportamiento en tiempo de ejecución *(Servicios sugeridos: GuardDuty, Security Hub, Inspector)*

#### SEC7: ¿Cómo clasificas tus datos?

**Estado de Cumplimiento:** ❌ No cumplido: 0/3 servicios detectados

**Evidencias Encontradas:**

- ❌ **S3**: S3 no está en uso o no tiene buckets
  - *Gap:* Falta de almacenamiento de objetos

**Servicios Relacionados:**
- ❌ Macie (no detectado)
- ❌ S3 (no detectado)
- ❌ Data Catalog (no detectado)

*Clasificación de datos*

**Mejores Prácticas:**
- Identificar datos sensibles *(Servicios sugeridos: Macie)*
- Etiquetar y catalogar datos *(Servicios sugeridos: S3, Data Catalog)*
- Aplicar políticas de clasificación de datos *(Servicios sugeridos: Macie, S3)*

#### SEC8: ¿Cómo proteges tus datos en reposo?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **KMS**: AWS KMS no está en uso o no tiene keys
  - *Gap:* Falta de gestión de claves de cifrado
- ❌ **RDS**: RDS no está en uso o no tiene recursos activos
  - *Gap:* Falta de bases de datos gestionadas
- ❌ **EBS**: EBS no está en uso o no tiene volumes
  - *Gap:* Falta de almacenamiento persistente para instancias EC2
- ❌ **S3**: S3 no está en uso o no tiene buckets
  - *Gap:* Falta de almacenamiento de objetos

**Servicios Relacionados:**
- ❌ KMS (no detectado)
- ❌ S3 (no detectado)
- ❌ EBS (no detectado)
- ❌ RDS (no detectado)

*Protección de datos en reposo*

**Mejores Prácticas:**
- Cifrar datos usando AWS KMS *(Servicios sugeridos: KMS)*
- Restringir acceso a recursos cifrados *(Servicios sugeridos: KMS, IAM)*
- Rotar claves de cifrado *(Servicios sugeridos: KMS)*

#### SEC9: ¿Cómo proteges tus datos en tránsito?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **ACM**: ACM no está en uso o no tiene certificados
  - *Gap:* Falta de gestión de certificados SSL/TLS
- ❌ **CloudFront**: CloudFront no está en uso o no tiene distribuciones
  - *Gap:* Falta de CDN y protección de datos en tránsito
- ❌ **API Gateway**: API Gateway no está en uso o no tiene APIs
  - *Gap:* Falta de gestión de APIs y protección de datos en tránsito
- ❌ **ELB**: ELB no está en uso o no tiene load balancers
  - *Gap:* Falta de balanceo de carga y protección de datos en tránsito

**Servicios Relacionados:**
- ❌ ACM (no detectado)
- ❌ CloudFront (no detectado)
- ❌ API Gateway (no detectado)
- ❌ ELB (no detectado)

*Protección de datos en tránsito*

**Mejores Prácticas:**
- Usar TLS para todas las comunicaciones *(Servicios sugeridos: ACM, CloudFront, API Gateway, ELB)*
- Aplicar suites de cifrado seguras *(Servicios sugeridos: ACM, CloudFront)*
- Deshabilitar protocolos inseguros *(Servicios sugeridos: Security Groups, NACLs)*

#### SEC10: ¿Cómo gestionas tus claves de cifrado?

**Estado de Cumplimiento:** ❌ No cumplido: 0/1 servicios detectados

**Evidencias Encontradas:**

- ❌ **KMS**: AWS KMS no está en uso o no tiene keys
  - *Gap:* Falta de gestión de claves de cifrado

**Servicios Relacionados:**
- ❌ KMS (no detectado)

*Gestión de claves de cifrado*

**Mejores Prácticas:**
- Separar deberes de gestión de claves *(Servicios sugeridos: KMS)*
- Usar claves gestionadas por el cliente *(Servicios sugeridos: KMS)*
- Rotar claves periódicamente *(Servicios sugeridos: KMS)*

#### SEC11: ¿Cómo te preparas y respondes a incidentes de seguridad?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **Security Hub**: AWS Security Hub no está habilitado
  - *Gap:* Falta de visibilidad centralizada del estado de seguridad
- ❌ **GuardDuty**: Amazon GuardDuty no está habilitado
  - *Gap:* Falta de detección de amenazas
- ❌ **CloudWatch Logs**: CloudWatch Logs no está en uso o no tiene log groups
  - *Gap:* Falta de centralización de logs de seguridad
- ❌ **EventBridge**: EventBridge no está en uso o no tiene rules/event buses configurados
  - *Gap:* Falta de automatización de respuestas a incidentes de seguridad

**Servicios Relacionados:**
- ❌ Security Hub (no detectado)
- ❌ GuardDuty (no detectado)
- ❌ CloudWatch (no detectado)
- ❌ EventBridge (no detectado)

*Preparación y respuesta a incidentes*

**Mejores Prácticas:**
- Crear planes de respuesta a incidentes *(Servicios sugeridos: Security Hub, EventBridge)*
- Probar procedimientos de respuesta *(Servicios sugeridos: Security Hub, Lambda)*
- Automatizar acciones de contención *(Servicios sugeridos: Security Hub, EventBridge, Lambda)*

### Preguntas Sugeridas Adicionales para Workshop

1. ¿Por qué no se está usando Security Hub?
2. ¿Qué herramienta alternativa se usa para monitoreo de seguridad?
3. ¿Cómo se auditan los cambios de configuración sin Config?
4. ¿Por qué no se está usando CloudTrail? (CRÍTICO)
5. ¿Se está usando MFA para usuarios con privilegios?
6. ¿Se revisan regularmente las políticas IAM?
7. ¿Se usan roles en lugar de usuarios para aplicaciones?
8. ¿Cómo se están gestionando las credenciales sin Secrets Manager?
9. ¿Cómo se está gestionando el cifrado sin KMS?
10. ¿Cómo se están gestionando los certificados SSL/TLS sin ACM?
11. ¿Se está usando algún CDN alternativo?
12. ¿Cómo se están gestionando las APIs sin API Gateway?
13. ¿Cómo se está gestionando el balanceo de carga sin ELB?
14. ¿Cómo se están centralizando los logs de seguridad sin CloudWatch Logs?
15. ¿Qué recursos tienen acceso público y por qué?
16. ¿Se están usando Security Groups y NACLs correctamente?
17. ¿Por qué no se está usando Systems Manager para gestionar y proteger instancias EC2?
18. ¿Por qué no se está usando EventBridge para automatizar respuestas a incidentes de seguridad?

---

## Reliability

**Resumen:** 0 servicios de confiabilidad detectados

### Preguntas del Well-Architected Framework

#### REL1: ¿Cómo gestionas los límites de servicios de AWS?

**Estado de Cumplimiento:** ❌ No cumplido: 0/2 servicios detectados

**Servicios Relacionados:**
- ❌ Service Quotas (no detectado)
- ❌ CloudWatch (no detectado)

*Gestión de límites de servicios*

**Mejores Prácticas:**
- Monitorear cuotas de servicios *(Servicios sugeridos: Service Quotas, CloudWatch)*
- Solicitar aumentos de límites proactivamente *(Servicios sugeridos: Service Quotas)*
- Diseñar arquitecturas dentro de los límites

#### REL2: ¿Cómo gestionas el cambio?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **CloudFormation**: CloudFormation no está en uso o no tiene stacks activos
  - *Gap:* Falta de gestión de cambios mediante Infrastructure as Code

**Servicios Relacionados:**
- ❌ CloudFormation (no detectado)
- ❌ Terraform (no detectado)
- ❌ CodePipeline (no detectado)
- ❌ CodeDeploy (no detectado)

*Gestión de cambios*

**Mejores Prácticas:**
- Usar infraestructura como código *(Servicios sugeridos: CloudFormation, Terraform)*
- Implementar gestión de cambios *(Servicios sugeridos: CloudFormation, CodePipeline)*
- Automatizar despliegues *(Servicios sugeridos: CodePipeline, CodeDeploy, CloudFormation)*

#### REL3: ¿Cómo se adapta tu sistema a cambios en la demanda?

**Estado de Cumplimiento:** ⚠️ Parcialmente cumplido: 1/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **Auto Scaling**: EC2 detectado pero Auto Scaling no
  - *Gap:* Falta de escalado automático y recuperación

**Servicios Relacionados:**
- ❌ Auto Scaling (no detectado)
- ✅ ELB (detectado)
- ❌ ECS (no detectado)
- ❌ Lambda (no detectado)

*Adaptación a cambios en demanda*

**Mejores Prácticas:**
- Usar auto escalado *(Servicios sugeridos: Auto Scaling)*
- Diseñar cargas de trabajo sin estado *(Servicios sugeridos: S3, DynamoDB, ElastiCache)*
- Implementar balanceo de carga *(Servicios sugeridos: ELB, ALB, NLB)*

#### REL4: ¿Cómo monitoreas tus cargas de trabajo?

**Estado de Cumplimiento:** ⚠️ Parcialmente cumplido: 1/3 servicios detectados

**Evidencias Encontradas:**

- ❌ **CloudWatch Logs**: CloudWatch Logs no está en uso o no tiene log groups
  - *Gap:* Falta de monitoreo de logs de aplicaciones

**Servicios Relacionados:**
- ❌ CloudWatch (no detectado)
- ✅ CloudWatch Alarms (detectado)
- ❌ CloudWatch Logs (no detectado)

*Monitoreo de cargas de trabajo*

**Mejores Prácticas:**
- Usar métricas y alarmas de CloudWatch *(Servicios sugeridos: CloudWatch, CloudWatch Alarms)*
- Monitorear health checks *(Servicios sugeridos: Route 53 Health Checks, ELB Health Checks)*
- Rastrear KPIs de disponibilidad *(Servicios sugeridos: CloudWatch, Route 53)*

#### REL5: ¿Cómo haces respaldo de tus datos?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **RDS**: RDS no está en uso o no tiene recursos activos
  - *Gap:* Falta de bases de datos gestionadas
- ❌ **EBS**: EBS no está en uso o no tiene volumes
  - *Gap:* Falta de almacenamiento persistente para backups
- ❌ **S3**: S3 no está en uso o no tiene buckets
  - *Gap:* Falta de almacenamiento de objetos para backups

**Servicios Relacionados:**
- ❌ Backup (no detectado)
- ❌ RDS (no detectado)
- ❌ EBS (no detectado)
- ❌ S3 (no detectado)

*Respaldo de datos*

**Mejores Prácticas:**
- Automatizar backups *(Servicios sugeridos: Backup, RDS Automated Backups, EBS Snapshots)*
- Definir políticas de retención *(Servicios sugeridos: Backup, S3 Lifecycle, EBS Snapshots)*
- Probar procedimientos de restauración *(Servicios sugeridos: Backup, RDS, EBS)*

#### REL6: ¿Cómo pruebas la recuperación?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **RDS**: RDS no está en uso o no tiene recursos activos
  - *Gap:* Falta de bases de datos gestionadas
- ❌ **Route 53**: Route 53 no está en uso o no tiene hosted zones activas
  - *Gap:* Falta de gestión de DNS
- ❌ **Multi-AZ**: Multi-AZ no está configurado en ningún recurso
  - *Gap:* Falta de alta disponibilidad mediante Multi-AZ

**Servicios Relacionados:**
- ❌ Backup (no detectado)
- ❌ RDS (no detectado)
- ❌ Multi-AZ (no detectado)
- ❌ Route 53 (no detectado)

*Pruebas de recuperación*

**Mejores Prácticas:**
- Realizar simulacros de recuperación ante desastres *(Servicios sugeridos: Backup, RDS, Multi-AZ)*
- Probar mecanismos de failover *(Servicios sugeridos: Route 53, RDS Multi-AZ, ELB)*
- Documentar resultados de recuperación

### Preguntas Sugeridas Adicionales para Workshop

1. ¿Por qué no se está usando Auto Scaling para EC2?
2. ¿Cómo se están monitoreando los logs de aplicaciones sin CloudWatch Logs?
3. ¿Por qué no se está usando CloudFormation para gestionar cambios de infraestructura?
4. ¿Se debería configurar Multi-AZ para recursos críticos?

---

## Performance Efficiency

**Resumen:** 0 servicios de performance detectados

### Preguntas del Well-Architected Framework

#### PERF1: ¿Cómo seleccionas la arquitectura de mejor rendimiento?

**Estado de Cumplimiento:** ❌ No cumplido: 0/3 servicios detectados

**Evidencias Encontradas:**

- ❌ **CloudWatch**: CloudWatch no está en uso o no tiene alarmas/dashboards configurados
  - *Gap:* Falta de monitoreo y benchmarking de rendimiento
- ❌ **X-Ray**: X-Ray no está en uso o no tiene recursos configurados
  - *Gap:* Falta de rastreo distribuido y análisis de rendimiento
- ❌ **CloudFormation**: CloudFormation no está en uso o no tiene stacks activos
  - *Gap:* Falta de evaluación de patrones de arquitectura mediante Infrastructure as Code

**Servicios Relacionados:**
- ❌ CloudWatch (no detectado)
- ❌ X-Ray (no detectado)
- ❌ CloudFormation (no detectado)

*Selección de arquitectura*

**Mejores Prácticas:**
- Evaluar múltiples patrones de arquitectura *(Servicios sugeridos: CloudFormation, Well-Architected Tool)*
- Hacer benchmarking de rendimiento *(Servicios sugeridos: CloudWatch, X-Ray)*
- Usar servicios gestionados *(Servicios sugeridos: RDS, ElastiCache, DynamoDB, Lambda)*

#### PERF2: ¿Cómo seleccionas tu solución de cómputo?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **EC2**: EC2 no está en uso o no tiene instancias
  - *Gap:* Falta de cómputo virtual
- ❌ **Lambda**: Lambda no está en uso o no tiene funciones
  - *Gap:* Falta de cómputo serverless
- ❌ **ECS**: ECS no está en uso o no tiene clusters/servicios
  - *Gap:* Falta de orquestación de contenedores
- ❌ **Fargate**: ECS Fargate no está en uso
  - *Gap:* Falta de cómputo serverless para contenedores

**Servicios Relacionados:**
- ❌ EC2 (no detectado)
- ❌ Lambda (no detectado)
- ❌ ECS (no detectado)
- ❌ Fargate (no detectado)

*Selección de solución de cómputo*

**Mejores Prácticas:**
- Hacer coincidir tipos de cómputo con necesidades de carga de trabajo *(Servicios sugeridos: EC2, Lambda, ECS)*
- Usar instancias de tamaño adecuado *(Servicios sugeridos: EC2, Compute Optimizer)*
- Adoptar serverless donde sea apropiado *(Servicios sugeridos: Lambda, ECS Fargate, API Gateway)*

#### PERF3: ¿Cómo seleccionas tu solución de almacenamiento?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **EBS**: EBS no está en uso o no tiene volumes
  - *Gap:* Falta de almacenamiento persistente
- ❌ **S3**: S3 no está en uso o no tiene buckets
  - *Gap:* Falta de almacenamiento de objetos

**Servicios Relacionados:**
- ❌ S3 (no detectado)
- ❌ EBS (no detectado)
- ❌ EFS (no detectado)
- ❌ Storage Gateway (no detectado)

*Selección de solución de almacenamiento*

**Mejores Prácticas:**
- Elegir almacenamiento basado en patrones de acceso *(Servicios sugeridos: S3, EBS, EFS)*
- Usar políticas de ciclo de vida *(Servicios sugeridos: S3 Lifecycle, EBS Snapshots)*
- Monitorear IOPS y throughput *(Servicios sugeridos: CloudWatch, EBS)*

#### PERF4: ¿Cómo seleccionas tu solución de base de datos?

**Estado de Cumplimiento:** ❌ No cumplido: 0/4 servicios detectados

**Evidencias Encontradas:**

- ❌ **RDS**: RDS no está en uso o no tiene recursos activos
  - *Gap:* Falta de bases de datos gestionadas

**Servicios Relacionados:**
- ❌ RDS (no detectado)
- ❌ DynamoDB (no detectado)
- ❌ ElastiCache (no detectado)
- ❌ Redshift (no detectado)

*Selección de solución de base de datos*

**Mejores Prácticas:**
- Elegir bases de datos basadas en modelo de datos *(Servicios sugeridos: RDS, DynamoDB, ElastiCache, Redshift)*
- Optimizar indexación *(Servicios sugeridos: RDS, DynamoDB)*
- Usar bases de datos gestionadas *(Servicios sugeridos: RDS, DynamoDB, ElastiCache)*

#### PERF5: ¿Cómo monitoreas y mejoras el rendimiento?

**Estado de Cumplimiento:** ❌ No cumplido: 0/3 servicios detectados

**Evidencias Encontradas:**

- ❌ **CloudWatch**: CloudWatch no está en uso o no tiene alarmas/dashboards configurados
  - *Gap:* Falta de monitoreo y benchmarking de rendimiento
- ❌ **X-Ray**: X-Ray no está en uso o no tiene recursos configurados
  - *Gap:* Falta de rastreo distribuido y análisis de rendimiento

**Servicios Relacionados:**
- ❌ CloudWatch (no detectado)
- ❌ X-Ray (no detectado)
- ❌ CodeGuru (no detectado)

*Monitoreo y mejora de rendimiento*

**Mejores Prácticas:**
- Rastrear latencia y throughput *(Servicios sugeridos: CloudWatch, X-Ray)*
- Usar pruebas de rendimiento *(Servicios sugeridos: CloudWatch, X-Ray)*
- Ajustar cargas de trabajo continuamente *(Servicios sugeridos: CloudWatch, Compute Optimizer)*

### Preguntas Sugeridas Adicionales para Workshop

1. ¿Por qué no se está usando EC2 para cómputo?
2. ¿Por qué no se está usando Lambda para cómputo serverless?
3. ¿Por qué no se está usando ECS para orquestación de contenedores?
4. ¿Se debería considerar Fargate para cargas de trabajo serverless?
5. ¿Por qué no se está usando CloudWatch para monitorear y hacer benchmarking de rendimiento?
6. ¿Por qué no se está usando X-Ray para rastrear y analizar el rendimiento de aplicaciones?
7. ¿Por qué no se está usando CloudFormation para evaluar patrones de arquitectura?

---

## Cost Optimization

**Resumen:** 1 regiones activas, 0 servicios de costo detectados

### Preguntas del Well-Architected Framework

#### COST1: ¿Cómo consideras el costo al seleccionar servicios?

**Estado de Cumplimiento:** ❌ No cumplido: 0/3 servicios detectados

**Servicios Relacionados:**
- ❌ Cost Explorer (no detectado)
- ❌ Reserved Instances (no detectado)
- ❌ Savings Plans (no detectado)

*Consideración de costos al seleccionar servicios*

**Mejores Prácticas:**
- Comparar modelos de precios *(Servicios sugeridos: Cost Explorer, Pricing Calculator)*
- Usar servicios gestionados *(Servicios sugeridos: RDS, Lambda, ECS Fargate)*
- Evitar sobre-provisionamiento *(Servicios sugeridos: Compute Optimizer, CloudWatch)*

#### COST2: ¿Cómo monitoreas el uso y el gasto?

**Estado de Cumplimiento:** ❌ No cumplido: 0/3 servicios detectados

**Evidencias Encontradas:**

- ❌ **Cost Explorer**: Cost Explorer no accesible
  - *Gap:* Limitada visibilidad de costos
- ❌ **CloudWatch**: CloudWatch no está en uso o no tiene alarmas/dashboards configurados
  - *Gap:* Falta de monitoreo de uso y gasto

**Servicios Relacionados:**
- ❌ Cost Explorer (no detectado)
- ❌ Budgets (no detectado)
- ❌ CloudWatch (no detectado)

*Monitoreo de uso y gasto*

**Mejores Prácticas:**
- Usar Cost Explorer *(Servicios sugeridos: Cost Explorer)*
- Establecer presupuestos y alertas *(Servicios sugeridos: Budgets, CloudWatch)*
- Rastrear etiquetas de asignación de costos *(Servicios sugeridos: Cost Explorer, Cost Allocation Tags)*

#### COST3: ¿Cómo reduces costos innecesarios?

**Estado de Cumplimiento:** ❌ No cumplido: 0/3 servicios detectados

**Evidencias Encontradas:**

- ❌ **Trusted Advisor**: Trusted Advisor no está disponible o no se tienen datos recolectados
  - *Gap:* Falta de recomendaciones automatizadas de optimización (requiere plan de soporte Business o Enterprise)
  - *Nota:* Las recomendaciones de Trusted Advisor ayudan a identificar oportunidades de optimización de costos, seguridad, rendimiento y confiabilidad. Accede a través de la consola de AWS o mediante la API de Support.
- ℹ️ **trusted_advisor_info**: Trusted Advisor requiere un plan de soporte de AWS (Business o Enterprise) para acceder a recomendaciones completas
  - *Detalles:* Las recomendaciones de Trusted Advisor ayudan a identificar oportunidades de optimización de costos, seguridad, rendimiento y confiabilidad. Accede a través de la consola de AWS o mediante la API de Support.
- ❌ **CloudWatch**: CloudWatch no está en uso o no tiene alarmas/dashboards configurados
  - *Gap:* Falta de monitoreo de uso y gasto

**Servicios Relacionados:**
- ❌ CloudWatch (no detectado)
- ❌ Trusted Advisor (no detectado)
- ❌ Cost Explorer (no detectado)

*Reducción de costos innecesarios*

**Mejores Prácticas:**
- Identificar recursos inactivos *(Servicios sugeridos: Cost Explorer, Trusted Advisor, CloudWatch)*
- Desmantelar activos no utilizados *(Servicios sugeridos: CloudWatch, Trusted Advisor)*
- Usar automatización para apagar recursos *(Servicios sugeridos: Lambda, EventBridge, CloudWatch)*

#### COST4: ¿Cómo optimizas los modelos de precios?

**Estado de Cumplimiento:** ❌ No cumplido: 0/3 servicios detectados

**Servicios Relacionados:**
- ❌ Reserved Instances (no detectado)
- ❌ Savings Plans (no detectado)
- ❌ Spot Instances (no detectado)

*Optimización de modelos de precios*

**Mejores Prácticas:**
- Usar Savings Plans o Reserved Instances *(Servicios sugeridos: Reserved Instances, Savings Plans)*
- Adoptar Spot Instances *(Servicios sugeridos: EC2 Spot Instances)*
- Revisar compromisos regularmente *(Servicios sugeridos: Cost Explorer, Reserved Instances)*

### Preguntas Sugeridas Adicionales para Workshop

1. ¿Se tiene un plan de soporte que incluya Trusted Advisor?
2. ¿Se están revisando las recomendaciones de Trusted Advisor para identificar recursos inactivos?
3. ¿Por qué no se está usando CloudWatch para monitorear costos y uso?
4. ¿Se están usando Reserved Instances o Savings Plans?
5. ¿Se han evaluado instancias que podrían usar tipos más económicos?

---

## Sustainability

**Resumen:** 1 servicios relevantes para sostenibilidad

### Preguntas del Well-Architected Framework

#### SUS1: ¿Cómo mides la sostenibilidad de tu carga de trabajo?

**Estado de Cumplimiento:** ❌ No cumplido: 0/2 servicios detectados

**Evidencias Encontradas:**

- ❌ **Cost Explorer**: Cost Explorer no accesible
  - *Gap:* Limitada visibilidad de métricas de sostenibilidad
- ❌ **CloudWatch**: CloudWatch no está en uso o no tiene alarmas/dashboards configurados
  - *Gap:* Falta de medición de sostenibilidad

**Servicios Relacionados:**
- ❌ CloudWatch (no detectado)
- ❌ Cost Explorer (no detectado)

*Medición de sostenibilidad*

**Mejores Prácticas:**
- Medir utilización de recursos *(Servicios sugeridos: CloudWatch, Cost Explorer)*
- Rastrear métricas de eficiencia energética *(Servicios sugeridos: CloudWatch, Cost Explorer)*
- Usar dashboards de sostenibilidad *(Servicios sugeridos: CloudWatch Dashboards)*

#### SUS2: ¿Cómo reduces el impacto ambiental de tu carga de trabajo?

**Estado de Cumplimiento:** ⚠️ Parcialmente cumplido: 1/3 servicios detectados

**Evidencias Encontradas:**

- ✅ **Lambda**: Lambda (serverless) es más eficiente energéticamente

**Servicios Relacionados:**
- ❌ Auto Scaling (no detectado)
- ✅ Lambda (detectado)
- ❌ ECS Fargate (no detectado)

*Reducción de impacto ambiental*

**Mejores Prácticas:**
- Dimensionar recursos correctamente *(Servicios sugeridos: Compute Optimizer, CloudWatch)*
- Usar regiones eficientes *(Servicios sugeridos: Well-Architected Tool)*
- Minimizar capacidad inactiva *(Servicios sugeridos: Auto Scaling, Lambda, ECS Fargate)*

#### SUS3: ¿Cómo mejoras continuamente la sostenibilidad?

**Estado de Cumplimiento:** ❌ No cumplido: 0/3 servicios detectados

**Evidencias Encontradas:**

- ❌ **Cost Explorer**: Cost Explorer no accesible
  - *Gap:* Limitada visibilidad de métricas de sostenibilidad
- ❌ **Trusted Advisor**: Trusted Advisor no está disponible o no se tienen datos recolectados
  - *Gap:* Falta de recomendaciones automatizadas de sostenibilidad (requiere plan de soporte Business o Enterprise)
- ❌ **CloudWatch**: CloudWatch no está en uso o no tiene alarmas/dashboards configurados
  - *Gap:* Falta de medición de sostenibilidad

**Servicios Relacionados:**
- ❌ CloudWatch (no detectado)
- ❌ Cost Explorer (no detectado)
- ❌ Trusted Advisor (no detectado)

*Mejora continua de sostenibilidad*

**Mejores Prácticas:**
- Revisar métricas de sostenibilidad *(Servicios sugeridos: CloudWatch, Cost Explorer)*
- Optimizar arquitecturas regularmente *(Servicios sugeridos: Compute Optimizer, CloudWatch)*
- Adoptar servicios más nuevos y eficientes *(Servicios sugeridos: Lambda, ECS Fargate, Graviton Instances)*

### Preguntas Sugeridas Adicionales para Workshop

1. ¿Por qué no se está usando Cost Explorer para medir sostenibilidad?
2. ¿Se tiene un plan de soporte que incluya Trusted Advisor para recomendaciones de sostenibilidad?
3. ¿Por qué no se está usando CloudWatch para medir sostenibilidad?
4. ¿Se han considerado regiones con energía renovable?
5. ¿Se están usando servicios serverless cuando es posible?

---
