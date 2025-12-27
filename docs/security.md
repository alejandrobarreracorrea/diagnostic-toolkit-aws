# Seguridad y Permisos - ECAD

## Modelo de Acceso

ECAD utiliza el modelo de **AssumeRole con ExternalId** para acceso seguro a cuentas AWS de clientes. Este modelo proporciona:

- **Aislamiento de credenciales**: No se requieren credenciales permanentes del cliente
- **Control de acceso temporal**: Las sesiones tienen duración limitada
- **Auditoría**: Todas las acciones se registran en CloudTrail
- **Seguridad adicional**: ExternalId previene confusión de roles (confused deputy)

## Política IAM Recomendada

### Trust Policy (Para el Rol en la Cuenta del Cliente)

El cliente debe crear un rol IAM con la siguiente trust policy que permita asumir el rol:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "UNIQUE_EXTERNAL_ID"
        }
      }
    }
  ]
}
```

**Notas:**
- Reemplazar `ACCOUNT_ID` con el Account ID de la cuenta que asumirá el rol
- Reemplazar `UNIQUE_EXTERNAL_ID` con un ExternalId único compartido de forma segura
- El ExternalId debe ser compartido de forma segura (no en código o repos públicos)

### Permisos del Rol (ReadOnly + Cost Explorer)

El rol debe tener los siguientes permisos:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECADReadOnlyAccess",
      "Effect": "Allow",
      "Action": [
        "acm:Describe*",
        "acm:List*",
        "apigateway:GET",
        "application-autoscaling:Describe*",
        "autoscaling:Describe*",
        "cloudformation:Describe*",
        "cloudformation:List*",
        "cloudfront:Get*",
        "cloudfront:List*",
        "cloudtrail:Describe*",
        "cloudtrail:Get*",
        "cloudtrail:LookupEvents",
        "cloudwatch:Describe*",
        "cloudwatch:Get*",
        "cloudwatch:List*",
        "config:Describe*",
        "config:Get*",
        "config:List*",
        "dynamodb:Describe*",
        "dynamodb:List*",
        "ec2:Describe*",
        "ec2:Get*",
        "ecr:Describe*",
        "ecr:Get*",
        "ecr:List*",
        "ecs:Describe*",
        "ecs:List*",
        "eks:Describe*",
        "eks:List*",
        "elasticache:Describe*",
        "elasticache:List*",
        "elasticloadbalancing:Describe*",
        "es:Describe*",
        "es:List*",
        "events:Describe*",
        "events:List*",
        "firehose:Describe*",
        "firehose:List*",
        "iam:Get*",
        "iam:List*",
        "kinesis:Describe*",
        "kinesis:List*",
        "lambda:Get*",
        "lambda:List*",
        "logs:Describe*",
        "logs:Get*",
        "logs:FilterLogEvents",
        "rds:Describe*",
        "rds:List*",
        "redshift:Describe*",
        "redshift:List*",
        "route53:Get*",
        "route53:List*",
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning",
        "s3:ListAllMyBuckets",
        "s3:ListBucket",
        "s3:GetBucketAcl",
        "s3:GetBucketPolicy",
        "s3:GetBucketPublicAccessBlock",
        "s3:GetEncryptionConfiguration",
        "s3:GetLifecycleConfiguration",
        "s3:GetReplicationConfiguration",
        "s3:GetBucketTagging",
        "s3:GetBucketWebsite",
        "s3:GetObjectVersion",
        "s3:GetObject",
        "s3:GetObjectAcl",
        "s3:GetObjectTagging",
        "sagemaker:Describe*",
        "sagemaker:List*",
        "secretsmanager:Describe*",
        "secretsmanager:Get*",
        "secretsmanager:List*",
        "sns:Get*",
        "sns:List*",
        "sqs:Get*",
        "sqs:List*",
        "ssm:Describe*",
        "ssm:Get*",
        "ssm:List*",
        "sts:GetCallerIdentity",
        "support:Describe*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECADCostExplorerReadOnly",
      "Effect": "Allow",
      "Action": [
        "ce:Describe*",
        "ce:Get*",
        "ce:List*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECADOrganizationsReadOnly",
      "Effect": "Allow",
      "Action": [
        "organizations:Describe*",
        "organizations:List*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECADSecurityHubReadOnly",
      "Effect": "Allow",
      "Action": [
        "securityhub:Describe*",
        "securityhub:Get*",
        "securityhub:List*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECADGuardDutyReadOnly",
      "Effect": "Allow",
      "Action": [
        "guardduty:Describe*",
        "guardduty:Get*",
        "guardduty:List*"
      ],
      "Resource": "*"
    }
  ]
}
```

**Nota:** Esta política es extensa pero solo incluye operaciones ReadOnly. Si algún servicio no está listado, puede agregarse siguiendo el patrón `servicio:Describe*`, `servicio:List*`, `servicio:Get*`.

### Política Mínima Simplificada (Alternativa)

Si se prefiere una política más simple, se puede usar una política administrada de AWS con restricciones:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ReadOnlyAccess"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ce:Describe*",
        "ce:Get*",
        "ce:List*"
      ],
      "Resource": "*"
    }
  ]
}
```

**Nota:** `ReadOnlyAccess` es una política administrada de AWS que puede ser demasiado permisiva. Se recomienda la política detallada arriba para seguir el principio de menor privilegio.

## Configuración de Variables de Entorno

Para usar AssumeRole, configurar las siguientes variables de entorno:

```bash
export AWS_ROLE_ARN=arn:aws:iam::CLIENT_ACCOUNT_ID:role/ECADRole
export AWS_EXTERNAL_ID=unique-external-id
export AWS_ROLE_SESSION_NAME=ECAD-Session
```

O pasar como argumentos al collector:

```bash
python -m collector.main \
  --role-arn arn:aws:iam::CLIENT_ACCOUNT_ID:role/ECADRole \
  --external-id unique-external-id \
  --output-dir ./runs/run-$(date +%Y%m%d-%H%M%S)
```

## Protección de Datos Recolectados

### Almacenamiento Local

- Todos los datos se almacenan **localmente** en el directorio especificado
- Los datos están comprimidos en formato `.json.gz` para eficiencia
- **No se envían datos a servicios externos** - todo permanece local

### Recomendaciones de Seguridad

1. **Cifrado en Reposo**: Se recomienda cifrar el directorio donde se almacenan los datos:
   ```bash
   # Linux/Mac
   encfs ~/ecad-data ~/ecad-data-encrypted
   
   # O usar herramientas de cifrado de disco completo
   ```

2. **Control de Acceso**: Asegurar que solo usuarios autorizados tengan acceso a los datos:
   ```bash
   chmod -R 700 ./runs/
   ```

3. **Eliminación Segura**: Después de completar el engagement, eliminar datos de forma segura:
   ```bash
   # Linux
   shred -u -z -n 3 ./runs/run-*/
   
   # Mac
   srm -rf ./runs/run-*/
   ```

4. **Backup**: Si se hace backup, asegurar que esté cifrado y con control de acceso adecuado

### Datos Recolectados

ECAD recolecta:

- **Metadatos de cuenta**: Account ID, alias, organización
- **Inventario de recursos**: Listas de recursos por servicio y región
- **Configuraciones**: Configuraciones de recursos (sin datos sensibles)
- **Metadatos de servicios**: Información sobre servicios habilitados

**NO se recolectan:**

- Contenido de datos (contenido de S3 objects, mensajes SQS, etc.)
- Secrets o credenciales (aunque se detecta si existen)
- Datos de aplicaciones
- Información personal identificable (PII) más allá de metadatos de cuenta

## Auditoría y Cumplimiento

### CloudTrail

Todas las acciones de ECAD se registran en CloudTrail del cliente:

- **Usuario/Rol**: El rol asumido aparece en CloudTrail
- **Acciones**: Todas las llamadas de API se registran
- **Timestamp**: Timestamps precisos de todas las operaciones

### Cumplimiento

ECAD está diseñado para cumplir con:

- **Principio de menor privilegio**: Solo permisos ReadOnly
- **Separación de responsabilidades**: AssumeRole con ExternalId
- **Auditoría**: Todas las acciones son auditables
- **Transparencia**: Cliente tiene control total sobre permisos

## Troubleshooting de Permisos

### Error: AccessDenied

**Causa común:** El rol no tiene permisos suficientes o la trust policy es incorrecta.

**Solución:**
1. Verificar que el rol tenga la política de permisos correcta
2. Verificar que la trust policy permita asumir el rol correctamente
3. Verificar que el ExternalId coincida exactamente

### Error: InvalidUserID.NotFound

**Causa común:** El ExternalId no coincide o la trust policy tiene un error.

**Solución:**
1. Verificar que el ExternalId en la trust policy coincida exactamente con el proporcionado
2. Verificar que no haya espacios adicionales o caracteres especiales

### Error: Throttling

**Causa común:** Demasiadas llamadas simultáneas o límites de rate de AWS.

**Solución:**
1. Reducir `--max-threads` en la configuración
2. El collector aplica backoff automático, pero puede tardar más tiempo

## Contacto

Para preguntas sobre seguridad o permisos, consultar la documentación del proyecto.


