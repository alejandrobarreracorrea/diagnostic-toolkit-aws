"""
Metadata Collector - Recolección de metadatos de cuenta AWS.
"""

import logging
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class MetadataCollector:
    """Recolector de metadatos de cuenta AWS."""
    
    def __init__(self, session: boto3.Session):
        self.session = session
    
    def collect(self) -> Dict[str, Any]:
        """Recolectar metadatos de la cuenta AWS."""
        metadata = {
            "account_id": None,
            "account_alias": None,
            "regions": [],
            "organization": None,
            "timestamp": None
        }
        
        try:
            # Account ID
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            metadata["account_id"] = identity.get("Account")
            metadata["arn"] = identity.get("Arn")
            metadata["user_id"] = identity.get("UserId")
            
            # Account Alias
            try:
                iam = self.session.client('iam')
                aliases = iam.list_account_aliases()
                if aliases.get('AccountAliases'):
                    metadata["account_alias"] = aliases['AccountAliases'][0]
            except Exception as e:
                logger.debug(f"No se pudo obtener alias de cuenta: {e}")
            
            # Regions disponibles
            try:
                ec2 = self.session.client('ec2', region_name='us-east-1')
                regions_response = ec2.describe_regions()
                metadata["regions"] = [
                    r['RegionName'] for r in regions_response.get('Regions', [])
                ]
            except Exception as e:
                logger.debug(f"No se pudieron listar regiones: {e}")
            
            # Organization info (si aplica)
            try:
                orgs = self.session.client('organizations')
                org_info = orgs.describe_organization()
                metadata["organization"] = {
                    "id": org_info['Organization'].get('Id'),
                    "arn": org_info['Organization'].get('Arn'),
                    "master_account_id": org_info['Organization'].get('MasterAccountId')
                }
            except ClientError as e:
                if e.response['Error']['Code'] != 'AWSOrganizationsNotInUseException':
                    logger.debug(f"No se pudo obtener info de organización: {e}")
            except Exception as e:
                logger.debug(f"Error obteniendo organización: {e}")
            
        except Exception as e:
            logger.warning(f"Error recolectando metadatos: {e}")
        
        from datetime import datetime
        metadata["timestamp"] = datetime.utcnow().isoformat()
        
        return metadata


