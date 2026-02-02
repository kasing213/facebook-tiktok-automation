# app/services/validation_schemas.py
"""
Request/response validation schemas for all services.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import Field, validator
from enum import Enum

from app.core.validation import BaseRequestModel, BaseResponseModel, TenantRequest
from app.core.models import Platform, TokenType


# Auth Service Schemas
class StoreOAuthTokenRequest(TenantRequest):
    """Request to store OAuth token"""
    user_id: UUID = Field(..., description="User ID who owns the token")
    access_token: str = Field(..., min_length=1, description="OAuth access token")
    refresh_token: Optional[str] = Field(default=None, description="OAuth refresh token")
    platform: Platform = Field(..., description="OAuth platform")
    account_ref: str = Field(..., description="Platform account reference")
    scope: Optional[str] = Field(default=None, description="Token scopes")
    expires_at: Optional[datetime] = Field(default=None, description="Token expiration")
    raw_data: Optional[Dict[str, Any]] = Field(default=None, description="Raw OAuth response")


class StoreOAuthTokenResponse(BaseResponseModel):
    """Response for storing OAuth token"""
    token_id: UUID = Field(..., description="Created token ID")
    platform: Platform = Field(..., description="OAuth platform")
    account_name: Optional[str] = Field(default=None, description="Account display name")
    expires_at: Optional[datetime] = Field(default=None, description="Token expiration")


class GetTokenRequest(TenantRequest):
    """Request to get decrypted token"""
    user_id: UUID = Field(..., description="User ID who owns the token")
    platform: Platform = Field(..., description="Token platform")
    account_ref: Optional[str] = Field(default=None, description="Platform account reference")
    social_identity_id: Optional[UUID] = Field(default=None, description="Social identity ID")
    facebook_page_id: Optional[UUID] = Field(default=None, description="Facebook page ID")


class GetTokenResponse(BaseResponseModel):
    """Response for getting token"""
    token: Optional[str] = Field(default=None, description="Decrypted access token")
    expires_at: Optional[datetime] = Field(default=None, description="Token expiration")
    is_valid: bool = Field(default=False, description="Whether token is valid")


class ValidateTokenRequest(BaseRequestModel):
    """Request to validate token"""
    token_id: UUID = Field(..., description="Token ID to validate")
    user_id: UUID = Field(..., description="User ID who owns the token")
    is_valid: bool = Field(default=True, description="Validation status")


class ValidateTokenResponse(BaseResponseModel):
    """Response for token validation"""
    token_id: UUID = Field(..., description="Validated token ID")
    is_valid: bool = Field(..., description="Current validation status")
    updated_at: datetime = Field(..., description="Validation timestamp")


class AuthenticateUserRequest(TenantRequest):
    """Request to authenticate user"""
    telegram_user_id: str = Field(..., min_length=1, description="Telegram user ID")


class AuthenticateUserResponse(BaseResponseModel):
    """Response for user authentication"""
    user_id: Optional[UUID] = Field(default=None, description="User ID if authenticated")
    username: Optional[str] = Field(default=None, description="Username")
    is_authenticated: bool = Field(default=False, description="Authentication status")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")


class CreateUserRequest(TenantRequest):
    """Request to create user"""
    telegram_user_id: str = Field(..., min_length=1, description="Telegram user ID")
    username: Optional[str] = Field(default=None, description="Username")


class CreateUserResponse(BaseResponseModel):
    """Response for user creation"""
    user_id: UUID = Field(..., description="Created user ID")
    telegram_user_id: str = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(default=None, description="Username")
    created_at: datetime = Field(..., description="Creation timestamp")


class GetFacebookPagesRequest(TenantRequest):
    """Request to get Facebook pages"""
    user_id: UUID = Field(..., description="User ID who owns the pages")


class FacebookPageInfo(BaseRequestModel):
    """Facebook page information"""
    id: str = Field(..., description="Token ID")
    page_id: str = Field(..., description="Facebook page ID")
    page_name: str = Field(..., description="Page name")
    category: Optional[str] = Field(default=None, description="Page category")
    tasks: List[str] = Field(default=[], description="Page tasks/permissions")
    access_token: str = Field(..., description="Page access token")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Additional page data")


class GetFacebookPagesResponse(BaseResponseModel):
    """Response for Facebook pages"""
    pages: List[FacebookPageInfo] = Field(default=[], description="Facebook pages")
    total_pages: int = Field(default=0, description="Total number of pages")


class RefreshTokenRequest(BaseRequestModel):
    """Request to refresh token"""
    token_id: UUID = Field(..., description="Token ID to refresh")
    user_id: UUID = Field(..., description="User ID who owns the token")


class RefreshTokenResponse(BaseResponseModel):
    """Response for token refresh"""
    token_id: UUID = Field(..., description="Refreshed token ID")
    is_valid: bool = Field(..., description="Whether refresh was successful")
    refreshed_at: datetime = Field(..., description="Refresh timestamp")


class DeleteUserDataRequest(BaseRequestModel):
    """Request to delete user data"""
    facebook_user_id: str = Field(..., min_length=1, description="Facebook user ID")


class DeleteUserDataResponse(BaseResponseModel):
    """Response for user data deletion"""
    status: str = Field(..., description="Deletion status")
    user_id: str = Field(..., description="Facebook user ID")
    deleted_count: int = Field(default=0, description="Number of items deleted")
    timestamp: datetime = Field(..., description="Deletion timestamp")


# Inventory Service Schemas
class CreateProductRequest(TenantRequest):
    """Request to create product"""
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    sku: str = Field(..., min_length=1, max_length=50, description="Product SKU")
    price: float = Field(..., ge=0, description="Product price")
    stock_quantity: int = Field(default=0, ge=0, description="Initial stock quantity")
    description: Optional[str] = Field(default=None, max_length=1000, description="Product description")
    category: Optional[str] = Field(default=None, max_length=100, description="Product category")
    unit: Optional[str] = Field(default="piece", max_length=20, description="Stock unit")
    low_stock_threshold: int = Field(default=5, ge=0, description="Low stock alert threshold")
    is_active: bool = Field(default=True, description="Product active status")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional product data")

    @validator('price')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price must be non-negative')
        return round(v, 2)


class ProductInfo(BaseResponseModel):
    """Product information"""
    id: UUID = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    sku: str = Field(..., description="Product SKU")
    price: float = Field(..., description="Product price")
    stock_quantity: int = Field(..., description="Current stock quantity")
    description: Optional[str] = Field(default=None, description="Product description")
    category: Optional[str] = Field(default=None, description="Product category")
    unit: str = Field(..., description="Stock unit")
    low_stock_threshold: int = Field(..., description="Low stock threshold")
    is_active: bool = Field(..., description="Product active status")
    is_low_stock: bool = Field(..., description="Whether product is low on stock")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CreateProductResponse(BaseResponseModel):
    """Response for product creation"""
    product: ProductInfo = Field(..., description="Created product information")


class UpdateStockRequest(TenantRequest):
    """Request to update stock"""
    product_id: UUID = Field(..., description="Product ID")
    quantity_change: int = Field(..., description="Stock quantity change (positive or negative)")
    reason: str = Field(..., min_length=1, max_length=200, description="Reason for stock change")
    reference_type: Optional[str] = Field(default=None, description="Reference type (e.g., 'invoice')")
    reference_id: Optional[UUID] = Field(default=None, description="Reference ID")

    @validator('quantity_change')
    def validate_quantity_change(cls, v):
        if v == 0:
            raise ValueError('Quantity change cannot be zero')
        return v


class StockMovement(BaseResponseModel):
    """Stock movement information"""
    id: UUID = Field(..., description="Movement ID")
    product_id: UUID = Field(..., description="Product ID")
    quantity_change: int = Field(..., description="Quantity change")
    quantity_before: int = Field(..., description="Stock before change")
    quantity_after: int = Field(..., description="Stock after change")
    reason: str = Field(..., description="Movement reason")
    reference_type: Optional[str] = Field(default=None, description="Reference type")
    reference_id: Optional[UUID] = Field(default=None, description="Reference ID")
    created_at: datetime = Field(..., description="Movement timestamp")


class UpdateStockResponse(BaseResponseModel):
    """Response for stock update"""
    movement: StockMovement = Field(..., description="Stock movement record")
    current_stock: int = Field(..., description="Current stock quantity")
    is_low_stock: bool = Field(..., description="Whether product is now low on stock")


# Invoice Service Schemas
class CreateInvoiceRequest(TenantRequest):
    """Request to create invoice"""
    recipient_name: str = Field(..., min_length=1, max_length=200, description="Invoice recipient name")
    amount: float = Field(..., gt=0, description="Invoice amount")
    currency: str = Field(default="USD", regex="^[A-Z]{3}$", description="Currency code")
    description: Optional[str] = Field(default=None, max_length=1000, description="Invoice description")
    due_date: Optional[datetime] = Field(default=None, description="Payment due date")
    line_items: Optional[List[Dict[str, Any]]] = Field(default=None, description="Invoice line items")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional invoice data")

    @validator('amount')
    def validate_amount(cls, v):
        return round(v, 2)

    @validator('due_date')
    def validate_due_date(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError('Due date cannot be in the past')
        return v


class InvoiceInfo(BaseResponseModel):
    """Invoice information"""
    id: UUID = Field(..., description="Invoice ID")
    invoice_number: str = Field(..., description="Invoice number")
    recipient_name: str = Field(..., description="Recipient name")
    amount: float = Field(..., description="Invoice amount")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Invoice status")
    description: Optional[str] = Field(default=None, description="Invoice description")
    due_date: Optional[datetime] = Field(default=None, description="Due date")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CreateInvoiceResponse(BaseResponseModel):
    """Response for invoice creation"""
    invoice: InvoiceInfo = Field(..., description="Created invoice information")
    pdf_url: Optional[str] = Field(default=None, description="PDF download URL")