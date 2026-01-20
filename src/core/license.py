"""JWT-based license validation for Hotcross."""

import logging
import os
from datetime import datetime, timezone
from typing import Any

import jwt

logger = logging.getLogger(__name__)

# Public key for verifying licenses (private key kept secret)
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsSSr9o
EhX+jSEMFppJ2M
VsIX02RrXW7n0Za0B3k2G4F7Fs6FFpR/AUIjKVCg5WNG3A8MGy
bmKUeg+C+cbUzk
sOEb+CB/6sT6daHBFiae3dUQwIYv1ko2D2QiTEeSiilEx8n4qL
w2Edr2JBasSU6n
nlC/OJveKf/WCds9nebBwT6Z4srzAiUoYY6evuDX78cG/4oi8u
hmAz35jJTGVyKk
LsLMwJyeTuR4ii4YSohe2+rq1lJo2cLxVxM6h3zqycHbrDgGrj
0rzTxtnABL/by/
Tr8AVnp/briZzVfYQXwhXiQNl85WmYVMlgpAmLGWOIzPBwg1zW
zUkAWaVLGJzcil
/wIDAQAB
-----END PUBLIC KEY-----"""


class LicenseInfo:
    """Parsed license information."""
    
    def __init__(self, claims: dict[str, Any]):
        self.org_id: str = claims.get("org_id", "")
        self.org_name: str = claims.get("org_name", "")
        self.tier: str = claims.get("tier", "free")
        self.features: list[str] = claims.get("features", [])
        self.max_seats: int = claims.get("max_seats", 1)
        self.issued_at: int = claims.get("iat", 0)
        self.expires_at: int = claims.get("exp", 0)
        self.claims = claims
    
    def is_expired(self) -> bool:
        """Check if license is expired."""
        if self.expires_at == 0:
            return False
        return datetime.now(timezone.utc).timestamp() > self.expires_at
    
    def has_feature(self, feature: str) -> bool:
        """Check if license includes a feature."""
        return feature in self.features
    
    def is_commercial(self) -> bool:
        """Check if this is a commercial license."""
        return self.tier == "commercial"
    
    def __repr__(self) -> str:
        return f"License(org={self.org_name}, tier={self.tier}, expires={datetime.fromtimestamp(self.expires_at) if self.expires_at else 'never'})"


def validate_license(license_key: str) -> LicenseInfo | None:
    """Validate a JWT license key.
    
    Args:
        license_key: JWT license string
        
    Returns:
        LicenseInfo if valid, None if invalid
    """
    try:
        # Decode and verify JWT
        claims = jwt.decode(
            license_key,
            PUBLIC_KEY,
            algorithms=["RS256"],
            options={"verify_exp": True}
        )
        
        license_info = LicenseInfo(claims)
        
        # Check expiration
        if license_info.is_expired():
            logger.error("License expired")
            return None
        
        logger.info(f"✅ Valid license: {license_info}")
        return license_info
        
    except jwt.ExpiredSignatureError:
        logger.error("License expired")
        return None
    except jwt.InvalidSignatureError:
        logger.error("Invalid license signature")
        return None
    except jwt.DecodeError as e:
        logger.error(f"Failed to decode license: {e}")
        return None
    except Exception as e:
        logger.error(f"License validation error: {e}")
        return None


def get_license_from_env() -> LicenseInfo | None:
    """Get and validate license from environment variable.
    
    Returns:
        LicenseInfo if valid license found, None for free tier
    """
    license_key = os.getenv("HOTCROSS_LICENSE")
    
    if not license_key:
        logger.info("🏠 No license key found - running in FREE tier")
        logger.info("   Free tier: 1 project limit, no todos, no document management")
        logger.info("   For commercial license, visit: https://cal.com/team/atelierlogos/get-a-hotcross-api-key")
        return None
    
    logger.info("🔐 License key detected - validating...")
    return validate_license(license_key)
