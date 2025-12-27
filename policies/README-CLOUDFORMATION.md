# CloudFormation Stack para ECAD - Guía de Implementación

Este template de CloudFormation crea automáticamente el rol IAM y las políticas necesarias para ECAD en tu cuenta de AWS.

## 📋 Resumen

El template `ecad-iam-role-cloudformation.yaml` crea:
- ✅ **Rol IAM** con permisos ReadOnly para ECAD
- ✅ **Política IAM Part 1** (servicios principales)
- ✅ **Política IAM Part 2** (servicios adicionales)
- ✅ Configuración para acceso desde la misma cuenta o cross-account
- ✅ Soporte para External ID (recomendado para cross-account)

## 🚀 Despliegue Rápido

### Opción 1: AWS Console (Recomendado para principiantes)

1. **Abrir CloudFormation Console:**
   - Ve a AWS Console → CloudFormation → Stacks
   - Click en "Create stack" → "With new resources (standard)"

2. **Cargar Template:**
   - Selecciona "Upload a template file"
   - Sube el archivo `ecad-iam-role-cloudformation.yaml`
   - Click "Next"

3. **Configurar Parámetros:**
   - **RoleName**: Nombre del rol (default: `ECAD-ReadOnly-Role`)
   - **EnableSameAccountAccess**: `true` para permitir acceso desde la misma cuenta
   - **PrincipalAccountId**: (Opcional) ID de cuenta para cross-account
   - **PrincipalArn**: (Opcional) ARN específico de usuario/rol
   - **ExternalId**: (Opcional) External ID para seguridad adicional

4. **Revisar y Crear:**
   - Revisa la configuración
   - Marca "I acknowledge that AWS CloudFormation might create IAM resources"
   - Click "Create stack"

5. **Esperar Creación:**
   - El stack se creará en ~1-2 minutos
   - Verás los Outputs con el ARN del rol y comandos de uso

### Opción 2: AWS CLI

```bash
# Desplegar stack básico (misma cuenta)
aws cloudformation create-stack \
  --stack-name ECAD-IAM-Role \
  --template-body file://policies/ecad-iam-role-cloudformation.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=RoleName,ParameterValue=ECAD-ReadOnly-Role \
    ParameterKey=EnableSameAccountAccess,ParameterValue=true

# Verificar estado
aws cloudformation describe-stacks --stack-name ECAD-IAM-Role

# Ver outputs
aws cloudformation describe-stacks \
  --stack-name ECAD-IAM-Role \
  --query 'Stacks[0].Outputs'
```

### Opción 3: Cross-Account con External ID

```bash
# Desplegar con External ID para cross-account seguro
aws cloudformation create-stack \
  --stack-name ECAD-IAM-Role \
  --template-body file://policies/ecad-iam-role-cloudformation.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=RoleName,ParameterValue=ECAD-ReadOnly-Role \
    ParameterKey=PrincipalAccountId,ParameterValue=123456789012 \
    ParameterKey=ExternalId,ParameterValue=mi-external-id-secreto \
    ParameterKey=EnableSameAccountAccess,ParameterValue=false
```

## 📝 Parámetros del Template

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `RoleName` | String | `ECAD-ReadOnly-Role` | Nombre del rol IAM a crear |
| `EnableSameAccountAccess` | String | `true` | Permitir acceso desde la misma cuenta |
| `PrincipalAccountId` | String | `''` | ID de cuenta AWS para cross-account |
| `PrincipalArn` | String | `''` | ARN específico de usuario/rol |
| `ExternalId` | String | `''` | External ID para seguridad (recomendado) |

## 🔧 Escenarios de Uso

### Escenario 1: Misma Cuenta (Más Simple)

**Configuración:**
- `EnableSameAccountAccess`: `true`
- `PrincipalAccountId`: (vacío)
- `ExternalId`: (vacío)

**Uso:**
```bash
# Asumir el rol
aws sts assume-role \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/ECAD-ReadOnly-Role \
  --role-session-name ECAD-Session

# Configurar credenciales temporales
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
```

### Escenario 2: Cross-Account con External ID (Recomendado)

**Configuración:**
- `EnableSameAccountAccess`: `false`
- `PrincipalAccountId`: `123456789012` (cuenta origen)
- `ExternalId`: `mi-external-id-secreto`

**Uso desde cuenta origen:**
```bash
# Asumir el rol con External ID
aws sts assume-role \
  --role-arn arn:aws:iam::TARGET_ACCOUNT:role/ECAD-ReadOnly-Role \
  --role-session-name ECAD-Session \
  --external-id mi-external-id-secreto
```

### Escenario 3: Usuario/Rol Específico

**Configuración:**
- `PrincipalArn`: `arn:aws:iam::ACCOUNT_ID:user/mi-usuario`
- `ExternalId`: (opcional)

**Uso:**
Solo el usuario/rol especificado puede asumir el rol.

## ✅ Verificación

Después de crear el stack, verifica que todo funciona:

```bash
# Ver el rol creado
aws iam get-role --role-name ECAD-ReadOnly-Role

# Ver políticas adjuntas
aws iam list-attached-role-policies --role-name ECAD-ReadOnly-Role

# Probar acceso (después de asumir el rol)
aws ec2 describe-instances --region us-east-1
aws s3 list-buckets
aws iam list-users
```

## 🔒 Seguridad

### Mejores Prácticas:

1. **External ID para Cross-Account:**
   - Siempre usa External ID cuando configures cross-account
   - El External ID debe ser secreto y único
   - No lo compartas públicamente

2. **Principio de Menor Privilegio:**
   - El template solo crea permisos ReadOnly
   - No permite crear, modificar o eliminar recursos
   - Resource: "*" es necesario para operaciones de listado

3. **Monitoreo:**
   - Habilita CloudTrail para auditar el uso del rol
   - Revisa regularmente quién asume el rol

4. **Rotación:**
   - Si usas External ID, rótalo periódicamente
   - Actualiza el stack con el nuevo External ID

## 📊 Outputs del Stack

El stack genera los siguientes outputs:

- **RoleName**: Nombre del rol creado
- **RoleArn**: ARN completo del rol (útil para asumir el rol)
- **PolicyPart1Arn**: ARN de la política Part 1
- **PolicyPart2Arn**: ARN de la política Part 2
- **AssumeRoleCommand**: Comando listo para usar para asumir el rol
- **UsageInstructions**: Instrucciones de uso

## 🔄 Actualización del Stack

Para actualizar el stack (por ejemplo, cambiar External ID):

```bash
aws cloudformation update-stack \
  --stack-name ECAD-IAM-Role \
  --template-body file://policies/ecad-iam-role-cloudformation.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=RoleName,ParameterValue=ECAD-ReadOnly-Role \
    ParameterKey=ExternalId,ParameterValue=nuevo-external-id
```

## 🗑️ Eliminación del Stack

Para eliminar el stack y todos los recursos:

```bash
aws cloudformation delete-stack --stack-name ECAD-IAM-Role
```

**Nota:** Esto eliminará el rol y las políticas. Asegúrate de no tener dependencias antes de eliminar.

## 🐛 Solución de Problemas

### Error: "Cannot assume role"

**Causa:** El principal no tiene permisos para asumir el rol.

**Solución:**
- Verifica que `EnableSameAccountAccess` esté en `true` si usas la misma cuenta
- Verifica que `PrincipalAccountId` o `PrincipalArn` sean correctos
- Verifica que el External ID sea correcto si está configurado

### Error: "Policy too large"

**Causa:** Las políticas IAM tienen límites de tamaño.

**Solución:**
- El template divide las políticas en Part 1 y Part 2
- Si aún es muy grande, considera usar políticas más específicas

### Error: "Role already exists"

**Causa:** Ya existe un rol con ese nombre.

**Solución:**
- Usa un nombre diferente en el parámetro `RoleName`
- O elimina el rol existente primero

## 📖 Referencias

- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)
- [AWS IAM Roles Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)
- [AWS AssumeRole Documentation](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)
- [ECAD README](../README.md)

## 💡 Ejemplo Completo

```bash
# 1. Crear el stack
aws cloudformation create-stack \
  --stack-name ECAD-IAM-Role \
  --template-body file://policies/ecad-iam-role-cloudformation.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# 2. Esperar a que se cree (verificar estado)
aws cloudformation wait stack-create-complete --stack-name ECAD-IAM-Role

# 3. Obtener el ARN del rol
ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name ECAD-IAM-Role \
  --query 'Stacks[0].Outputs[?OutputKey==`RoleArn`].OutputValue' \
  --output text)

# 4. Asumir el rol
aws sts assume-role \
  --role-arn $ROLE_ARN \
  --role-session-name ECAD-Session

# 5. Configurar credenciales y usar ECAD
python ecad.py
```

