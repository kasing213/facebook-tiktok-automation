# app/routes/users.py
"""
User management routes for tenant owners.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.models import User, UserRole
from app.core.authorization import get_current_owner
from app.repositories import UserRepository


router = APIRouter(prefix="/users", tags=["user_management"])


# Request/Response Models
class UserSummary(BaseModel):
    """Summary user information for listing"""
    id: str
    username: Optional[str]
    email: Optional[str]
    role: UserRole
    is_active: bool
    telegram_user_id: Optional[str]
    telegram_username: Optional[str]
    telegram_linked_at: Optional[str]
    created_at: str
    last_login: Optional[str]

    class Config:
        from_attributes = True


class InviteUserRequest(BaseModel):
    """Invite new user request"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    role: UserRole = UserRole.user
    send_invitation: bool = True


class InviteUserResponse(BaseModel):
    """Invite user response"""
    success: bool
    user_id: str
    message: str
    invitation_sent: bool = False


class UpdateUserRequest(BaseModel):
    """Update user request"""
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserListResponse(BaseModel):
    """User list response"""
    users: List[UserSummary]
    total_count: int
    active_count: int
    owner_count: int


# Routes
@router.get("/", response_model=UserListResponse)
async def list_tenant_users(
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
    include_inactive: bool = False
):
    """
    List all users in the tenant (owner only).

    Args:
        owner: Current tenant owner
        db: Database session
        include_inactive: Whether to include inactive users

    Returns:
        List of users with summary information
    """
    user_repo = UserRepository(db)

    # Get all users for the tenant
    all_users = user_repo.get_tenant_users(owner.tenant_id, active_only=False)

    # Filter based on include_inactive
    if not include_inactive:
        users = [u for u in all_users if u.is_active]
    else:
        users = all_users

    # Convert to response format
    user_summaries = []
    for user in users:
        user_summaries.append(UserSummary(
            id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            telegram_user_id=user.telegram_user_id,
            telegram_username=user.telegram_username,
            telegram_linked_at=user.telegram_linked_at.isoformat() if user.telegram_linked_at else None,
            created_at=user.created_at.isoformat(),
            last_login=user.last_login.isoformat() if user.last_login else None
        ))

    # Calculate statistics
    total_count = len(all_users)
    active_count = len([u for u in all_users if u.is_active])
    owner_count = len([u for u in all_users if u.role == UserRole.admin and u.is_active])

    return UserListResponse(
        users=user_summaries,
        total_count=total_count,
        active_count=active_count,
        owner_count=owner_count
    )


@router.post("/invite", response_model=InviteUserResponse)
async def invite_user(
    invite_request: InviteUserRequest,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """
    Invite a new user to the tenant (owner only).

    Args:
        invite_request: User invitation details
        owner: Current tenant owner
        db: Database session

    Returns:
        Invitation result
    """
    user_repo = UserRepository(db)

    try:
        # Create the user (no password yet - they'll set it via invitation link)
        new_user = user_repo.create_user(
            tenant_id=owner.tenant_id,
            username=invite_request.username,
            email=invite_request.email,
            password_hash=None,  # Will be set when they accept invitation
            email_verified=False,
            role=invite_request.role
        )

        db.commit()
        db.refresh(new_user)

        # TODO: Send invitation email with setup link
        # This would typically involve:
        # 1. Generate secure invitation token
        # 2. Send email with link to set password
        # 3. Track invitation status

        return InviteUserResponse(
            success=True,
            user_id=str(new_user.id),
            message=f"User {invite_request.email} has been invited to the organization",
            invitation_sent=invite_request.send_invitation
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{user_id}", response_model=UserSummary)
async def update_user(
    user_id: str,
    update_request: UpdateUserRequest,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """
    Update user settings (owner only).

    Args:
        user_id: User ID to update
        update_request: Update data
        owner: Current tenant owner
        db: Database session

    Returns:
        Updated user information
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    user_repo = UserRepository(db)

    # Get the user and verify they belong to the same tenant
    user = user_repo.get_by_id(user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.tenant_id != owner.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage users in your own organization"
        )

    # Prevent owner from demoting themselves
    if user.id == owner.id and update_request.role and update_request.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role"
        )

    # Prevent owner from deactivating themselves
    if user.id == owner.id and update_request.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account"
        )

    # Update fields
    update_data = {}
    if update_request.role is not None:
        update_data["role"] = update_request.role
    if update_request.is_active is not None:
        update_data["is_active"] = update_request.is_active

    if update_data:
        updated_user = user_repo.update(user.id, **update_data)
        db.commit()
        db.refresh(updated_user)
        user = updated_user

    return UserSummary(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        telegram_user_id=user.telegram_user_id,
        telegram_username=user.telegram_username,
        telegram_linked_at=user.telegram_linked_at.isoformat() if user.telegram_linked_at else None,
        created_at=user.created_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.delete("/{user_id}")
async def remove_user(
    user_id: str,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """
    Remove a user from the tenant (owner only).
    This deactivates the user rather than deleting the record.

    Args:
        user_id: User ID to remove
        owner: Current tenant owner
        db: Database session

    Returns:
        Removal result
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    user_repo = UserRepository(db)

    # Get the user and verify they belong to the same tenant
    user = user_repo.get_by_id(user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.tenant_id != owner.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage users in your own organization"
        )

    # Prevent owner from removing themselves
    if user.id == owner.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove your own account"
        )

    # Deactivate the user (soft delete)
    user_repo.update(user.id, is_active=False)
    db.commit()

    return {
        "success": True,
        "message": f"User {user.email or user.username} has been removed from the organization"
    }


@router.get("/{user_id}", response_model=UserSummary)
async def get_user(
    user_id: str,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """
    Get detailed user information (owner only).

    Args:
        user_id: User ID to get
        owner: Current tenant owner
        db: Database session

    Returns:
        User information
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    user_repo = UserRepository(db)

    # Get the user and verify they belong to the same tenant
    user = user_repo.get_by_id(user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.tenant_id != owner.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view users in your own organization"
        )

    return UserSummary(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        telegram_user_id=user.telegram_user_id,
        telegram_username=user.telegram_username,
        telegram_linked_at=user.telegram_linked_at.isoformat() if user.telegram_linked_at else None,
        created_at=user.created_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None
    )