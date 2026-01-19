"""Authentication middleware for MCP server."""

import asyncio
import logging
import os
from functools import wraps
from typing import Any, Callable

from src.core.auth import AuthManager

logger = logging.getLogger(__name__)

# Global auth manager instance
_auth_manager: AuthManager | None = None
_auth_enabled: bool = False


def init_auth(database_url: str | None = None) -> None:
    """Initialize authentication system.
    
    Args:
        database_url: PostgreSQL connection URL. If None, uses DATABASE_URL env var.
    """
    global _auth_manager, _auth_enabled
    
    # Get database URL
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    _auth_manager = AuthManager(database_url)
    _auth_enabled = True
    logger.info("Authentication initialized with PostgreSQL database")


def get_auth_manager() -> AuthManager | None:
    """Get the global auth manager instance.
    
    Returns:
        Auth manager or None if auth is disabled
    """
    return _auth_manager


def is_auth_enabled() -> bool:
    """Check if authentication is enabled.
    
    Returns:
        True if auth is enabled
    """
    return _auth_enabled


def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication for a function.
    
    Checks for API key and validates it against PostgreSQL.
    If auth is disabled, allows all requests.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        # Skip auth if explicitly disabled (for testing)
        if not _auth_enabled:
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        
        # Get API key from kwargs or environment
        api_key = kwargs.get("api_key") or kwargs.get("_api_key") or os.getenv("HOTCROSS_API_KEY")
        
        if not api_key:
            logger.warning("Authentication required but no API key provided")
            return {
                "success": False,
                "error": "Authentication required. Set HOTCROSS_API_KEY environment variable."
            }
        
        # Authenticate
        if _auth_manager is None:
            logger.error("Auth manager not initialized")
            return {
                "success": False,
                "error": "Authentication system not initialized"
            }
        
        auth_result = await _auth_manager.authenticate(api_key)
        
        if not auth_result.allowed:
            logger.warning(f"Authentication failed: {auth_result.error}")
            return {
                "success": False,
                "error": f"Authentication failed: {auth_result.error}"
            }
        
        # Add developer_id and organization_id to kwargs
        kwargs["_developer_id"] = auth_result.developer_id
        kwargs["_organization_id"] = auth_result.organization_id
        
        # Call the original function
        return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        # Skip auth if explicitly disabled (for testing)
        if not _auth_enabled:
            return func(*args, **kwargs)
        
        # Get API key from kwargs or environment
        api_key = kwargs.get("api_key") or kwargs.get("_api_key") or os.getenv("HOTCROSS_API_KEY")
        
        if not api_key:
            logger.warning("Authentication required but no API key provided")
            return {
                "success": False,
                "error": "Authentication required. Set HOTCROSS_API_KEY environment variable."
            }
        
        # Authenticate
        if _auth_manager is None:
            logger.error("Auth manager not initialized")
            return {
                "success": False,
                "error": "Authentication system not initialized"
            }
        
        # Run async authenticate in sync context
        loop = asyncio.get_event_loop()
        auth_result = loop.run_until_complete(_auth_manager.authenticate(api_key))
        
        if not auth_result.allowed:
            logger.warning(f"Authentication failed: {auth_result.error}")
            return {
                "success": False,
                "error": f"Authentication failed: {auth_result.error}"
            }
        
        # Add developer_id and organization_id to kwargs
        kwargs["_developer_id"] = auth_result.developer_id
        kwargs["_organization_id"] = auth_result.organization_id
        
        # Call the original function
        return func(*args, **kwargs)
    
    # Return appropriate wrapper based on function type
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
