# Políticas IAM para ECAD - Guía de Implementación

## 📋 Resumen

Para cubrir todos los servicios AWS con permisos ReadOnly, ECAD utiliza **dos políticas complementarias** que deben adjuntarse al mismo rol/usuario.

## 🔧 Políticas Disponibles

### Política 1: `iam-policy-ecad-part1.json`
**Servicios principales y más comunes:**
- Compute: EC2, ECS, EKS, Lambda, Batch
- Storage: S3, EFS, Glacier
- Database: RDS, DynamoDB, ElastiCache, Redshift, DAX
- Networking: VPC, ELB, CloudFront, Route53, DirectConnect
- Security: IAM, GuardDuty, Security Hub, Config, CloudTrail, Shield, WAF
- Monitoring: CloudWatch, X-Ray, CloudTrail
- Development: CodeBuild, CodeCommit, CodePipeline, CodeArtifact
- Y muchos más servicios esenciales

### Política 2: `iam-policy-ecad-part2.json`
**Servicios adicionales y especializados:**
- Device Farm
- GameLift
- Ground Station
- Outposts
- Personalize
- Redshift Serverless
- Resource Explorer 2
- RoboMaker
- Verified Permissions

## 🚀 Cómo Implementar

### Opción 1: Adjuntar Ambas Políticas al Rol/Usuario

1. **Crear Política 1:**
   ```bash
   # En AWS Console: IAM → Policies → Create Policy
   # Copia el contenido de policies/iam-policy-ecad-part1.json
   # Nombre: ECAD-ReadOnly-Part1
   ```

2. **Crear Política 2:**
   ```bash
   # En AWS Console: IAM → Policies → Create Policy
   # Copia el contenido de policies/iam-policy-ecad-part2.json
   # Nombre: ECAD-ReadOnly-Part2
   ```

3. **Adjuntar Ambas Políticas:**
   ```bash
   # En AWS Console: IAM → Roles (o Users) → Selecciona tu rol/usuario
   # → Add permissions → Attach policies
   # Selecciona ambas: ECAD-ReadOnly-Part1 y ECAD-ReadOnly-Part2
   ```

### Opción 2: Usar AWS CLI

```bash
# Crear política 1
aws iam create-policy \
  --policy-name ECAD-ReadOnly-Part1 \
  --policy-document file://policies/iam-policy-ecad-part1.json

# Crear política 2
aws iam create-policy \
  --policy-name ECAD-ReadOnly-Part2 \
  --policy-document file://policies/iam-policy-ecad-part2.json

# Adjuntar ambas al rol
aws iam attach-role-policy \
  --role-name ECAD-Role \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/ECAD-ReadOnly-Part1

aws iam attach-role-policy \
  --role-name ECAD-Role \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/ECAD-ReadOnly-Part2
```

### Opción 3: Usar Terraform

```hcl
resource "aws_iam_policy" "ecad_part1" {
  name        = "ECAD-ReadOnly-Part1"
  description = "ECAD ReadOnly Access - Part 1 (Main Services)"
  policy      = file("${path.module}/policies/iam-policy-ecad-part1.json")
}

resource "aws_iam_policy" "ecad_part2" {
  name        = "ECAD-ReadOnly-Part2"
  description = "ECAD ReadOnly Access - Part 2 (Additional Services)"
  policy      = file("${path.module}/policies/iam-policy-ecad-part2.json")
}

resource "aws_iam_role_policy_attachment" "ecad_part1" {
  role       = aws_iam_role.ecad_role.name
  policy_arn = aws_iam_policy.ecad_part1.arn
}

resource "aws_iam_role_policy_attachment" "ecad_part2" {
  role       = aws_iam_role.ecad_role.name
  policy_arn = aws_iam_policy.ecad_part2.arn
}
```

## ✅ Verificación

Después de adjuntar ambas políticas, verifica que funcionan:

```bash
# Verificar políticas adjuntas
aws iam list-attached-role-policies --role-name ECAD-Role

# Probar acceso
aws ec2 describe-instances --region us-east-1
aws s3 list-buckets
aws iam list-users
```

## 📊 Cobertura

- **Política 1:** ~200 servicios principales
- **Política 2:** ~9 servicios adicionales
- **Total:** Cobertura completa de servicios AWS válidos

## 🔒 Seguridad

Ambas políticas:
- ✅ Solo acciones ReadOnly (List*, Describe*, Get*)
- ✅ No permiten crear, modificar o eliminar recursos
- ✅ Resource: "*" (necesario para operaciones de listado)
- ✅ Siguen el principio de privilegio mínimo

## 📝 Notas

- **Ambas políticas deben adjuntarse** para cobertura completa
- Si solo necesitas servicios principales, puedes usar solo la Parte 1
- Las políticas están validadas contra la documentación oficial de AWS IAM
- Todos los servicios incluidos son válidos y funcionan correctamente

## 🔄 Actualización

Si AWS agrega nuevos servicios, puedes:
1. Agregar acciones a la Parte 2 (si hay espacio)
2. O crear una Parte 3 si es necesario

## 📖 Referencias

- [AWS IAM Policy Reference](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies.html)
- [AWS Service Authorization Reference](https://docs.aws.amazon.com/service-authorization/latest/reference/)


