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


class Organization(BaseModel):
    """Organization record."""

    id: UUID = Field(..., description="Organization UUID")
    name: str = Field(..., description="Organization name")
    stripe_customer_id: str | None = Field(default=None, description="Stripe customer ID")
    subscription_status: SubscriptionStatus = Field(..., description="Current subscription status")
    subscription_id: str | None = Field(default=None, description="Stripe subscription ID")
    max_seats: int = Field(..., description="Maximum number of developers allowed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @property
    def has_active_subscription(self) -> bool:
        """Check if organization has an active subscription."""
        return self.subscription_status in (
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
        )


class Developer(BaseModel):
    """Developer record."""

    id: UUID = Field(..., description="Developer UUID")
    organization_id: UUID = Field(..., description="Organization UUID")
    email: str = Field(..., description="Developer email")
    first_name: str = Field(..., description="Developer first name")
    last_name: str = Field(..., description="Developer last name")
    api_key_prefix: str = Field(..., description="API key prefix")
    api_key_created_at: datetime = Field(..., description="API key creation timestamp")
    api_key_revoked_at: datetime | None = Field(default=None, description="API key revocation timestamp")
    api_key_last_used_at: datetime | None = Field(default=None, description="Last API key usage timestamp")
    is_active: bool = Field(..., description="Whether developer is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @property
    def is_revoked(self) -> bool:
        """Check if API key is revoked."""
        return self.api_key_revoked_at is not None


class OrganizationCreate(BaseModel):
    """Input for creating an organization."""

    name: str = Field(..., description="Organization name")
    stripe_customer_id: str | None = Field(default=None, description="Stripe customer ID")
    subscription_status: SubscriptionStatus = Field(
        default=SubscriptionStatus.INCOMPLETE,
        description="Initial subscription status"
    )
    max_seats: int = Field(default=1, description="Maximum number of developers")


class DeveloperCreate(BaseModel):
    """Input for creating a developer."""

    organization_id: UUID = Field(..., description="Organization UUID")
    email: str = Field(..., description="Developer email")
    first_name: str = Field(..., description="Developer first name")
    last_name: str = Field(..., description="Developer last name")


class DeveloperResponse(BaseModel):
    """Response when creating a developer (includes the actual API key)."""

    id: UUID = Field(..., description="Developer UUID")
    organization_id: UUID = Field(..., description="Organization UUID")
    email: str = Field(..., description="Developer email")
    api_key: str = Field(..., description="The actual API key (only shown once)")
    api_key_prefix: str = Field(..., description="API key prefix")
    created_at: datetime = Field(..., description="Creation timestamp")


class AuthResult(BaseModel):
    """Result of an authentication check."""

    allowed: bool = Field(..., description="Whether access is allowed")
    developer_id: UUID | None = Field(default=None, description="Developer UUID if authenticated")
    organization_id: UUID | None = Field(default=None, description="Organization UUID if authenticated")
    error: str | None = Field(default=None, description="Error message if denied")
