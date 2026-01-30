# Guía de Contribución

¡Gracias por tu interés en contribuir a AWS Cloud Architecture Diagnostic (ECAD)!

## Cómo Contribuir

### Reportar Problemas

Si encuentras un bug o tienes una sugerencia:

1. Verifica que el problema no haya sido reportado ya en [Issues](../../issues)
2. Crea un nuevo issue con:
   - Descripción clara del problema o sugerencia
   - Pasos para reproducir (si aplica)
   - Versión de Python y sistema operativo
   - Logs o mensajes de error relevantes

### Contribuir Código

1. **Fork el repositorio** y clónalo localmente
2. **Crea una rama** para tu feature o fix:
   ```bash
   git checkout -b feature/nombre-de-tu-feature
   # o
   git checkout -b fix/descripcion-del-fix
   ```
3. **Haz tus cambios** siguiendo las convenciones del proyecto:
   - Código en Python 3.9+
   - Usa type hints cuando sea posible
   - Sigue PEP 8 para estilo de código
   - Agrega docstrings a funciones y clases
   - Incluye comentarios cuando el código no sea obvio
4. **Prueba tus cambios**:
   ```bash
   # Ejecutar tests si existen
   python -m pytest tests/
   
   # Verificar que el código funciona
   python ecad.py
   ```
5. **Commit tus cambios** con mensajes descriptivos:
   ```bash
   git commit -m "feat: agrega nueva funcionalidad X"
   # o
   git commit -m "fix: corrige problema Y"
   ```
6. **Push a tu fork**:
   ```bash
   git push origin feature/nombre-de-tu-feature
   ```
7. **Abre un Pull Request** en el repositorio original

### Convenciones de Commits

Usa mensajes de commit descriptivos siguiendo el formato:

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Cambios de formato (sin afectar funcionalidad)
- `refactor:` Refactorización de código
- `test:` Agregar o modificar tests
- `chore:` Tareas de mantenimiento

Ejemplos:
- `feat: agrega soporte para Route53 ResourceRecordSets`
- `fix: corrige conteo de recursos en CloudFormation`
- `docs: actualiza guía de instalación para Windows`

### Estándares de Código

- **Python 3.9+**: Asegúrate de que el código sea compatible
- **Type Hints**: Usa type hints cuando sea posible
- **Docstrings**: Documenta funciones y clases importantes
- **PEP 8**: Sigue las convenciones de estilo de Python
- **Manejo de Errores**: Incluye manejo apropiado de excepciones
- **Logging**: Usa el módulo `logging` en lugar de `print()`

### Estructura del Proyecto

- `collector/`: Lógica de recolección de datos AWS
- `analyzer/`: Análisis offline de datos
- `evidence/`: Generación de evidence packs
- `tools/`: Scripts de utilidad
- `docs/`: Documentación
- `policies/`: Políticas IAM

### Testing

Si agregas nueva funcionalidad, considera agregar tests:

- Tests unitarios para funciones individuales
- Tests de integración para flujos completos
- Verifica que los cambios no rompan funcionalidad existente

### Documentación

- Actualiza el README si agregas nuevas funcionalidades
- Documenta cambios importantes en `docs/`
- Agrega ejemplos de uso cuando sea relevante

## Preguntas

Si tienes preguntas sobre cómo contribuir, puedes:

- Abrir un issue con la etiqueta `question`
- Revisar la documentación en `docs/`

## Código de Conducta

- Sé respetuoso y profesional
- Acepta críticas constructivas
- Enfócate en lo que es mejor para el proyecto
- Muestra empatía hacia otros miembros de la comunidad

## Licencia

Al contribuir, aceptas que tus contribuciones serán licenciadas bajo la misma [MIT License](../LICENSE) del proyecto.

¡Gracias por contribuir! 🎉
