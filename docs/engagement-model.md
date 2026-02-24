# Modelo de Engagement - ECAD

## Descripción del Producto

AWS Cloud Architecture Diagnostic (ECAD) es un producto de diagnóstico técnico puntual para clientes B2B en AWS. Proporciona inventario completo, análisis arquitectónico y evidencias para Well-Architected Review.

## Características del Producto

### ✅ Incluido

- **Inventario Completo**: Descubrimiento automático de todos los recursos AWS
- **Análisis Offline**: Procesamiento sin conexión a AWS
- **Evidence Pack**: Generación automática de evidencias para Well-Architected Framework
- **Reportes Ejecutivos**: Reportes y Plan de mejoras (Well-Architected Improvement Plan) listos para presentar
- **Modo Demo**: Ejecución con datos de ejemplo

### ❌ NO Incluido

- **Operación Continua**: No es un servicio operativo 24/7
- **On-Call**: No hay soporte on-call
- **Soporte 24/7**: Soporte durante horario comercial según contrato
- **Tickets / SLA**: No hay SLA garantizado ni sistema de tickets
- **Implementación**: No incluye implementación de mejoras (solo diagnóstico)

## Flujo de Engagement Típico

### Fase 1: Preparación (1-2 días)

1. **Kickoff Meeting**
   - Presentación del producto y alcance
   - Revisión de requisitos de seguridad y permisos
   - Establecimiento de expectativas

2. **Configuración de Permisos**
   - Cliente crea rol IAM según `docs/security.md`
   - Compartir ExternalId de forma segura
   - Verificar acceso con prueba pequeña

3. **Planificación**
   - Acordar ventana de tiempo para recolección
   - Establecer canales de comunicación
   - Definir formato de entrega

### Fase 2: Recolección (1-3 días)

1. **Ejecución del Collector**
   - Ejecutar `make collect` o comando equivalente
   - Monitorear progreso (puede tardar horas en entornos grandes)
   - Verificar que no haya errores críticos

2. **Validación Inicial**
   - Revisar estadísticas de recolección
   - Verificar que se hayan recolectado servicios principales
   - Identificar cualquier problema de permisos

### Fase 3: Análisis (1-2 días)

1. **Análisis Offline**
   - Ejecutar `make analyze` para generar inventarios
   - Ejecutar `make evidence` para generar evidence pack
   - Ejecutar `make reports` para generar reportes

2. **Revisión Técnica**
   - Revisar hallazgos y validar con conocimiento del entorno
   - Ajustar reportes si es necesario
   - Preparar presentación

### Fase 4: Entrega (1 día)

1. **Workshop de Presentación**
   - Presentar resumen ejecutivo
   - Revisar hallazgos principales
   - Discutir Plan de mejoras (HRI/MRI)

2. **Entrega de Artefactos**
   - Raw dumps (JSON comprimido)
   - Evidence pack (Markdown + JSON)
   - Reportes ejecutivos (Markdown)
   - Inventarios (CSV + JSON)

3. **Q&A y Próximos Pasos**
   - Responder preguntas técnicas
   - Discutir priorización según Plan de mejoras (HRI/MRI)
   - Establecer seguimiento si aplica

## Entregables

### 1. Raw Dumps

- **Formato**: JSON comprimido (`.json.gz`)
- **Ubicación**: `RUN_DIR/raw/`
- **Contenido**: Todas las respuestas de API recolectadas
- **Uso**: Análisis técnico profundo, replay offline

### 2. Evidence Pack

- **Formato**: Markdown + JSON
- **Ubicación**: `RUN_DIR/outputs/evidence/`
- **Contenido**: Evidencias por pilar Well-Architected + preguntas sugeridas
- **Uso**: Preparación y ejecución de Well-Architected Review

### 3. Reportes Ejecutivos

- **Formato**: Markdown (convertible a PDF/DOCX)
- **Ubicación**: `RUN_DIR/outputs/reports/`
- **Contenido**:
  - Executive Summary (1 página)
  - Findings Report (hallazgos detallados)
  - Plan de mejoras (improvement_plan.md)
  - Technical Annex (inventario técnico)
  - Scorecard (scores por pilar)

### 4. Inventarios

- **Formato**: CSV + JSON
- **Ubicación**: `RUN_DIR/outputs/inventory/`
- **Contenido**:
  - Top servicios por recursos
  - Top regiones por recursos
  - Matriz servicio-región
  - Inventario completo por servicio

## Expectativas y Limitaciones

### Expectativas Realistas

- **Cobertura**: ECAD intenta descubrir todos los servicios, pero algunos pueden requerir parámetros específicos
- **Tiempo**: La recolección puede tardar varias horas en entornos grandes (1000+ recursos)
- **Precisión**: Los conteos de recursos son estimaciones basadas en respuestas de API
- **Hallazgos**: Los hallazgos son señales objetivas, no reemplazan revisión manual experta

### Limitaciones Conocidas

1. **Servicios con Parámetros Requeridos**: Algunos servicios requieren parámetros específicos que no se pueden inferir automáticamente
2. **Permisos**: Si falta acceso a un servicio, no se recolectará
3. **Rate Limiting**: AWS puede aplicar throttling, lo que puede extender el tiempo de recolección
4. **Regiones**: Solo se recolectan regiones especificadas en configuración
5. **Datos Sensibles**: No se recolectan contenidos de datos, solo metadatos

## Modelo de Precio (Ejemplo)

*Nota: Este es un ejemplo, ajustar según modelo de negocio*

### Opción 1: Precio Fijo por Engagement

- **Precio**: $X,XXX USD por engagement
- **Incluye**: Recolección, análisis, reportes, workshop de 2 horas
- **Tiempo**: 5-7 días hábiles

### Opción 2: Precio por Tamaño de Entorno

- **Pequeño** (< 500 recursos): $X,XXX USD
- **Mediano** (500-2000 recursos): $X,XXX USD
- **Grande** (2000+ recursos): $X,XXX USD

### Opción 3: Precio por Componente

- **Recolección**: $XXX USD
- **Análisis + Reportes**: $XXX USD
- **Workshop**: $XXX USD
- **Evidence Pack**: $XXX USD

## Soporte Post-Entrega

### Incluido

- **Clarificaciones**: Responder preguntas sobre reportes y hallazgos (hasta 2 semanas)
- **Correcciones**: Corregir errores obvios en reportes (hasta 1 semana)

### NO Incluido (Servicios Adicionales)

- **Re-recolección**: Nueva recolección requiere nuevo engagement
- **Análisis Adicional**: Análisis más profundo de hallazgos específicos
- **Implementación**: Implementación de mejoras recomendadas
- **Seguimiento Continuo**: Monitoreo o seguimiento a largo plazo

## Mejores Prácticas

### Para el Cliente

1. **Preparación**: Tener permisos IAM listos antes del engagement
2. **Comunicación**: Proporcionar contexto sobre el entorno (servicios críticos, regiones principales)
3. **Expectativas**: Entender que es un diagnóstico, no una implementación
4. **Feedback**: Proporcionar feedback sobre hallazgos para mejorar precisión

### Para el Equipo de ECAD

1. **Transparencia**: Ser claro sobre limitaciones y expectativas
2. **Documentación**: Documentar cualquier supuesto o decisión técnica
3. **Calidad**: Revisar reportes antes de entrega
4. **Comunicación**: Mantener al cliente informado durante recolección

## Casos de Uso

### Caso 1: Pre-Migración

Cliente planea migrar a AWS o entre cuentas. Necesita inventario completo y evaluación de arquitectura actual.

### Caso 2: Well-Architected Review

Cliente necesita prepararse para un Well-Architected Review oficial. ECAD proporciona evidencias y preguntas sugeridas.

### Caso 3: Due Diligence

Cliente adquiere otra empresa o cuenta AWS. Necesita entender qué tiene antes de integrar.

### Caso 4: Optimización

Cliente quiere optimizar costos o mejorar arquitectura. ECAD identifica oportunidades.

## Contacto y Soporte

Para consultas sobre el modelo de engagement:

- **Email**: [contacto@ejemplo.com]
- **Horario**: Lunes a Viernes, 9:00 - 18:00 [timezone]
- **Tiempo de Respuesta**: 1-2 días hábiles

---

**Última actualización**: [Fecha]


