# Avisos de Terceros (Third-Party Notices)

Este archivo contiene información sobre las dependencias de terceros utilizadas en este proyecto y sus respectivas licencias.

## Dependencias Principales

### boto3 y botocore
- **Versión**: >=1.28.0 (boto3), >=1.31.0 (botocore)
- **Licencia**: Apache License 2.0
- **Repositorio**: https://github.com/boto/boto3
- **Compatibilidad**: ✅ Compatible con MIT License
- **Nota**: boto3 es la librería oficial de AWS SDK para Python

### PyYAML
- **Versión**: >=6.0
- **Licencia**: MIT License
- **Repositorio**: https://github.com/yaml/pyyaml
- **Compatibilidad**: ✅ Compatible con MIT License

### Jinja2
- **Versión**: >=3.1.0
- **Licencia**: BSD License (3-clause)
- **Repositorio**: https://github.com/pallets/jinja
- **Compatibilidad**: ✅ Compatible con MIT License

### python-dateutil
- **Versión**: >=2.8.2
- **Licencia**: Apache License 2.0 / BSD License (dual-licensed)
- **Repositorio**: https://github.com/dateutil/dateutil
- **Compatibilidad**: ✅ Compatible con MIT License

### tqdm
- **Versión**: >=4.66.0
- **Licencia**: MPL 2.0 (Mozilla Public License 2.0) / MIT License (dual-licensed)
- **Repositorio**: https://github.com/tqdm/tqdm
- **Compatibilidad**: ✅ Compatible con MIT License

## Compatibilidad de Licencias

Todas las dependencias utilizadas son compatibles con la licencia MIT del proyecto:

- ✅ **Apache License 2.0**: Compatible con MIT
- ✅ **BSD License**: Compatible con MIT
- ✅ **MIT License**: Compatible con MIT
- ✅ **MPL 2.0**: Compatible con MIT

## Verificación de Licencias

Para verificar las licencias actuales de las dependencias instaladas:

```bash
# Instalar pip-licenses si no está instalado
pip install pip-licenses

# Ver todas las licencias
pip-licenses

# O verificar manualmente
pip show boto3 | grep License
pip show pyyaml | grep License
```

## Notas Importantes

1. **Dependencias Transitivas**: Las dependencias listadas aquí pueden tener sus propias dependencias. Todas deben ser compatibles con MIT.

2. **Actualización de Dependencias**: Al actualizar dependencias, verificar que las nuevas versiones mantengan licencias compatibles.

3. **Uso Comercial**: Todas las dependencias permiten uso comercial, lo cual es consistente con la licencia MIT del proyecto.

## Información de Copyright

Este proyecto incluye código y dependencias de terceros. Cada dependencia mantiene su propio copyright y licencia, que se respetan según sus términos.

Para más información sobre las licencias específicas, consulta:
- Los archivos LICENSE en los repositorios de cada dependencia
- Los metadatos de los paquetes en PyPI
- La documentación oficial de cada proyecto

---

**Última actualización**: 2024
