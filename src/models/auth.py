"""Pydantic models for Authentication and Billing."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class SubscriptionStatus(str, Enum):
    """Stripe subscription status."""

    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    UNPAID = "unpaid"
    PAUSED = "paused"


class APIKey(BaseModel):
    """API key record."""

    id: UUID = Field(..., description="API key UUID")
    key_prefix: str = Field(..., description="Key prefix for identification (e.g., 'hc_live_')")
    stripe_customer_id: str = Field(..., description="Associated Stripe customer ID")
    stripe_subscription_id: str | None = Field(default=None, description="Associated Stripe subscription ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    revoked_at: datetime | None = Field(default=None, description="Revocation timestamp if revoked")
    last_used_at: datetime | None = Field(default=None, description="Last usage timestamp")

    @property
    def is_revoked(self) -> bool:
        """Check if key is revoked."""
        return self.revoked_at is not None


class Customer(BaseModel):
    """Customer record with cached Stripe data."""

    stripe_customer_id: str = Field(..., description="Stripe customer ID")
    email: str = Field(..., description="Customer email")
    first_name: str = Field(..., description="Customer first name")
    last_name: str = Field(..., description="Customer last name")
    company: str | None = Field(default=None, description="Company name")
    subscription_status: SubscriptionStatus = Field(..., description="Current subscription status")
    subscription_updated_at: datetime | None = Field(default=None, description="When subscription status was last synced")
    created_at: datetime = Field(..., description="Record creation timestamp")

    @property
    def has_active_subscription(self) -> bool:
        """Check if customer has an active subscription."""
        return self.subscription_status in (
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
        )


class APIKeyCreate(BaseModel):
    """Input for creating an API key."""

    stripe_customer_id: str = Field(..., description="Stripe customer ID")
    stripe_subscription_id: str | None = Field(default=None, description="Stripe subscription ID")


class APIKeyResponse(BaseModel):
    """Response when creating an API key (includes the actual key)."""

    id: UUID = Field(..., description="API key UUID")
    key: str = Field(..., description="The actual API key (only shown once)")
    key_prefix: str = Field(..., description="Key prefix for identification")
    created_at: datetime = Field(..., description="Creation timestamp")


class AuthResult(BaseModel):
    """Result of an authentication check."""

    allowed: bool = Field(..., description="Whether access is allowed")
    customer_id: str | None = Field(default=None, description="Customer ID if authenticated")
    error: str | None = Field(default=None, description="Error message if denied")


class CustomerCreate(BaseModel):
    """Input for creating a customer record."""

    stripe_customer_id: str = Field(..., description="Stripe customer ID")
    email: str = Field(..., description="Customer email")
    first_name: str = Field(..., description="Customer first name")
    last_name: str = Field(..., description="Customer last name")
    company: str | None = Field(default=None, description="Company name")
    subscription_status: SubscriptionStatus = Field(
        default=SubscriptionStatus.INCOMPLETE,
        description="Initial subscription status"
    )
