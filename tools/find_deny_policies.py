#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para encontrar políticas con explicit deny que bloquean EC2.
Requiere permisos de administrador IAM o ayuda de un administrador.
"""

import json
import sys
import subprocess

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    print("="*80)
    print("🔍 BUSCAR POLÍTICAS CON EXPLICIT DENY PARA EC2")
    print("="*80)
    
    print("\n⚠️  IMPORTANTE:")
    print("   El error indica que hay un 'explicit deny' en una política basada en identidad.")
    print("   Los Deny tienen PRIORIDAD sobre los Allow, por eso EC2 falla aunque tengas permisos.")
    print()
    print("   Para encontrar la política con Deny, necesitas:")
    print("   1. Acceso de administrador IAM, O")
    print("   2. Pedirle a un administrador que revise las políticas adjuntas a tu usuario")
    print()
    
    # Obtener identidad
    try:
        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            identity = json.loads(result.stdout)
            arn = identity.get('Arn', '')
            print(f"   Usuario actual: {arn}")
            
            if ':user/' in arn:
                user_name = arn.split(':user/')[-1]
                print(f"\n   📋 INSTRUCCIONES PARA ADMINISTRADOR:")
                print(f"      1. Ve a AWS Console → IAM → Users → {user_name}")
                print(f"      2. Revisa la pestaña 'Permissions' (Permisos)")
                print(f"      3. Busca políticas que contengan 'Effect': 'Deny'")
                print(f"      4. Específicamente busca Deny para 'ec2:*' o 'ec2:Describe*'")
                print(f"      5. También verifica Permissions Boundary si existe")
                print()
                print(f"   📋 COMANDOS PARA ADMINISTRADOR:")
                print(f"      # Listar políticas adjuntas")
                print(f"      aws iam list-attached-user-policies --user-name {user_name}")
                print(f"      ")
                print(f"      # Para cada política, obtener su contenido y buscar 'Deny'")
                print(f"      aws iam get-policy --policy-arn <policy-arn>")
                print(f"      aws iam get-policy-version --policy-arn <policy-arn> --version-id <version-id>")
    except:
        pass
    
    print("\n" + "="*80)
    print("💡 SOLUCIONES POSIBLES")
    print("="*80)
    
    print("""
   1. 🔴 ELIMINAR O MODIFICAR LA POLÍTICA CON DENY
      - Identifica la política que tiene "Effect": "Deny" para EC2
      - Elimínala o modifícala para que no bloquee EC2
      - Los Deny tienen prioridad, así que aunque tengas Allow, el Deny prevalece

   2. 🔴 CREAR UNA EXCEPCIÓN EN LA POLÍTICA CON DENY
      - Si la política con Deny es necesaria para otros servicios
      - Agrega una condición o excepción para permitir EC2 específicamente
      - Ejemplo: Deny todo excepto EC2:Describe*, EC2:Get*, EC2:List*

   3. 🔴 USAR UN ROL DIFERENTE
      - Si no puedes modificar la política con Deny
      - Crea un nuevo rol sin la política restrictiva
      - Adjunta las políticas ECAD a ese nuevo rol
      - Usa AssumeRole para cambiar al nuevo rol

   4. 🔴 VERIFICAR PERMISSIONS BOUNDARY
      - Si hay un Permissions Boundary, puede estar limitando los permisos
      - Los Boundaries limitan el máximo de permisos, incluso si tienes Allow
      - Verifica si el Boundary permite EC2

   📋 ACCIÓN INMEDIATA:
      Contacta a tu administrador de IAM y pídele que:
      1. Revise las políticas adjuntas a tu usuario
      2. Busque políticas con "Effect": "Deny" para EC2
      3. Elimine o modifique esas políticas para permitir EC2:Describe*, EC2:Get*, EC2:List*
    """)
    
    print("="*80)

if __name__ == "__main__":
    main()

