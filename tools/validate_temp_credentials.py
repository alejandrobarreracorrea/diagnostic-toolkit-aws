#!/usr/bin/env python3
"""
Script para validar credenciales temporales de AWS (SSO/AssumeRole).
NO guarda ninguna información en archivos.
"""

import os
import sys
import json

def validate_credentials():
    """Validar credenciales temporales de AWS usando variables de entorno."""
    print("="*60)
    print("🔍 VALIDACIÓN DE CREDENCIALES TEMPORALES AWS")
    print("="*60)
    print()
    
    # Verificar que las variables de entorno estén configuradas
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    session_token = os.getenv("AWS_SESSION_TOKEN")
    
    if not access_key:
        print("❌ AWS_ACCESS_KEY_ID no está configurada")
        return False
    
    if not secret_key:
        print("❌ AWS_SECRET_ACCESS_KEY no está configurada")
        return False
    
    if not session_token:
        print("❌ AWS_SESSION_TOKEN no está configurada")
        return False
    
    print("✅ Variables de entorno detectadas:")
    print(f"   AWS_ACCESS_KEY_ID: {access_key[:10]}...{access_key[-4:]}")
    print(f"   AWS_SECRET_ACCESS_KEY: {'*' * len(secret_key)}")
    print(f"   AWS_SESSION_TOKEN: {session_token[:20]}...{session_token[-20:]}")
    print()
    
    # Intentar usar las credenciales con boto3
    try:
        import boto3
        print("🔍 Probando conexión con AWS...")
        
        # Crear sesión con las credenciales de las variables de entorno
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        
        # Intentar obtener la identidad del caller
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        print("✅ Credenciales válidas y funcionando correctamente")
        print()
        print("📋 Información de la cuenta:")
        print(f"   Account ID: {identity.get('Account', 'N/A')}")
        print(f"   User/Role ARN: {identity.get('Arn', 'N/A')}")
        print(f"   User ID: {identity.get('UserId', 'N/A')}")
        print()
        
        # Verificar expiración (si está disponible en el token)
        # Nota: No podemos decodificar el token JWT fácilmente, pero podemos verificar
        # que la sesión funciona haciendo una llamada adicional
        try:
            # Intentar listar regiones para verificar que las credenciales funcionan
            ec2 = session.client('ec2', region_name='us-east-1')
            regions = ec2.describe_regions()
            print("✅ Verificación adicional: Acceso a servicios AWS confirmado")
            print(f"   Regiones disponibles: {len(regions.get('Regions', []))}")
        except Exception as e:
            print(f"⚠️  Advertencia: No se pudo verificar acceso a servicios: {e}")
            print("   Pero las credenciales básicas funcionan")
        
        print()
        print("="*60)
        print("✅ VALIDACIÓN EXITOSA")
        print("="*60)
        print()
        print("💡 Las credenciales están funcionando correctamente.")
        print("   Puedes usar estas variables de entorno para ejecutar ECAD.")
        print()
        print("⚠️  IMPORTANTE: Estas credenciales son temporales.")
        print("   Si expiran, necesitarás renovarlas (ej: aws sso login)")
        print()
        
        return True
        
    except ImportError:
        print("❌ boto3 no está instalado")
        print("   Instala con: pip install boto3")
        return False
    except Exception as e:
        error_msg = str(e)
        print("❌ Error validando credenciales:")
        print(f"   {error_msg}")
        print()
        
        if "ExpiredToken" in error_msg or "expired" in error_msg.lower():
            print("💡 Las credenciales han expirado.")
            print("   Renueva las credenciales (ej: aws sso login)")
        elif "InvalidClientTokenId" in error_msg or "SignatureDoesNotMatch" in error_msg:
            print("💡 Las credenciales son inválidas.")
            print("   Verifica que las variables de entorno estén correctas")
        elif "AccessDenied" in error_msg:
            print("💡 Las credenciales son válidas pero tienen permisos limitados.")
            print("   Esto puede ser normal dependiendo de los permisos del rol/usuario")
        else:
            print("💡 Verifica:")
            print("   1. Que las variables de entorno estén correctamente configuradas")
            print("   2. Que tengas conexión a internet")
            print("   3. Que las credenciales no hayan expirado")
        
        return False

if __name__ == "__main__":
    try:
        success = validate_credentials()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Validación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)

