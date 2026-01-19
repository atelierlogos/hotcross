"""Authentication and authorization for Memory Portals."""

import hashlib
import logging
import os
from datetime import datetime, timezone

from src.models.auth import AuthResult, SubscriptionStatus

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication via external PostgreSQL database."""

    def __init__(self, database_url: str | None = None):
        """Initialize auth manager.
        
        Args:
            database_url: PostgreSQL connection URL. If None, reads from env.
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable required for authentication")
        
        self._conn = None
        self._connect()

    def _connect(self) -> None:
        """Connect to PostgreSQL database."""
        try:
            import asyncpg
            # Note: asyncpg is async, but we'll use it synchronously for now
            # In production, you'd want to use a connection pool
            logger.info("Auth manager initialized with PostgreSQL")
        except ImportError:
            raise ImportError(
                "asyncpg is required for authentication. "
                "Install with: pip install asyncpg"
            )
    
    async def _get_connection(self):
        """Get database connection."""
        import asyncpg
        if self._conn is None or self._conn.is_closed():
            self._conn = await asyncpg.connect(self.database_url)
        return self._conn
    
    def close(self) -> None:
        """Close database connection."""
        if self._conn and not self._conn.is_closed():
            import asyncio
            asyncio.get_event_loop().run_until_complete(self._conn.close())

    def _hash_key(self, key: str) -> str:
        """Hash an API key for validation.
        
        Args:
            key: The API key to hash
            
        Returns:
            SHA-256 hash of the key
        """
        return hashlib.sha256(key.encode()).hexdigest()

    async def authenticate(self, api_key: str) -> AuthResult:
        """Authenticate an API key against PostgreSQL database.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Authentication result
        """
        if not api_key:
            return AuthResult(
                allowed=False,
                error="API key required"
            )

        key_hash = self._hash_key(api_key)

        try:
            conn = await self._get_connection()
            
            # Look up the key in customers table
            row = await conn.fetchrow("""
                SELECT 
                    stripe_customer_id,
                    subscription_status,
                    api_key_revoked_at
                FROM customers
                WHERE api_key_hash = $1
                LIMIT 1
            """, key_hash)

            if not row:
                return AuthResult(
                    allowed=False,
                    error="Invalid API key"
                )
            
            # Check if revoked
            if row['api_key_revoked_at']:
                return AuthResult(
                    allowed=False,
                    error="API key has been revoked"
                )

            # Check if subscription is active
            status = row['subscription_status']
            if status not in ('active', 'trialing'):
                return AuthResult(
                    allowed=False,
                    error=f"Subscription is {status}"
                )

            # Update last used timestamp
            await conn.execute("""
                UPDATE customers
                SET api_key_last_used_at = NOW()
                WHERE api_key_hash = $1
            """, key_hash)

            customer_id = row['stripe_customer_id']
            logger.info(f"Authenticated customer {customer_id}")

            return AuthResult(
                allowed=True,
                customer_id=customer_id
            )

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return AuthResult(
                allowed=False,
                error="Authentication system error"
            )
