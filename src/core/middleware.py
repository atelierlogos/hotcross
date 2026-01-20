"""License-based middleware for MCP server."""

import asyncio
import logging
import os
from functools import wraps
from typing import Any, Callable

from src.core.license import LicenseInfo, get_license_from_env

logger = logging.getLogger(__name__)

# Global license instance
_license: LicenseInfo | None = None
_license_loaded: bool = False


class FeatureTier:
    """Feature tier restrictions."""
    
    FREE = "free"
    COMMERCIAL = "commercial"
    
    @staticmethod
    def get_tier() -> str:
        """Get current feature tier based on license."""
        if _license and _license.is_commercial():
            return FeatureTier.COMMERCIAL
        return FeatureTier.FREE
    
    @staticmethod
    def is_feature_allowed(feature: str) -> bool:
        """Check if a feature is allowed in current tier."""
        if _license and _license.has_feature(feature):
            return True
        
        # Free tier restrictions
        tier = FeatureTier.get_tier()
        if tier == FeatureTier.FREE:
            restricted_features = ["todo_management", "document_management"]
            return feature not in restricted_features
        
        return True
    
    @staticmethod
    def get_project_limit() -> int | None:
        """Get project limit for current tier. None means unlimited."""
        if _license and _license.is_commercial():
            return None  # Unlimited
        return 1  # Free tier


def init_license() -> None:
    """Initialize license system."""
    global _license, _license_loaded
    
    _license = get_license_from_env()
    _license_loaded = True
    
    if _license:
        logger.info(f"✅ Commercial license active: {_license.org_name}")
        logger.info(f"   Tier: {_license.tier}")
        logger.info(f"   Features: {', '.join(_license.features)}")
    else:
        logger.info("🏠 Running in FREE tier")
        logger.info("   Limitations: 1 project, no todos, no document management")


def get_license() -> LicenseInfo | None:
    """Get the current license.
    
    Returns:
        License info or None if free tier
    """
    return _license


def is_licensed() -> bool:
    """Check if a valid commercial license is active.
    
    Returns:
        True if commercial license is active
    """
    return _license is not None and _license.is_commercial()


def require_feature(feature: str) -> Callable:
    """Decorator to require a specific feature.
    
    Args:
        feature: Feature name (e.g., "todo_management", "document_management")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not FeatureTier.is_feature_allowed(feature):
                tier = FeatureTier.get_tier()
                return {
                    "success": False,
                    "error": f"This feature requires a Commercial plan. Current tier: {tier}"
                }
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not FeatureTier.is_feature_allowed(feature):
                tier = FeatureTier.get_tier()
                return {
                    "success": False,
                    "error": f"This feature requires a Commercial plan. Current tier: {tier}"
                }
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator
