"""
Administrative CLI script for managing tenants, users, and system operations.

This script provides command-line utilities for common administrative tasks
such as creating tenants, managing users, and performing system maintenance.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.db import async_session_maker
from app.core.models import Tenant, User, AdToken, Destination, Automation
from app.core.security import get_password_hash


async def create_tenant(
    name: str,
    slug: str,
    is_active: bool = True
) -> Tenant:
    """
    Create a new tenant.

    Args:
        name: Tenant name
        slug: URL-friendly identifier
        is_active: Whether tenant is active

    Returns:
        Created tenant
    """
    async with async_session_maker() as session:
        tenant = Tenant(
            id=uuid4(),
            name=name,
            slug=slug,
            is_active=is_active,
            settings={}
        )
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)

        logger.success(f"Created tenant: {tenant.name} (ID: {tenant.id})")
        return tenant


async def list_tenants():
    """List all tenants in the system."""
    async with async_session_maker() as session:
        result = await session.execute(select(Tenant))
        tenants = result.scalars().all()

        if not tenants:
            logger.info("No tenants found.")
            return

        logger.info(f"Found {len(tenants)} tenant(s):")
        for tenant in tenants:
            status = "active" if tenant.is_active else "inactive"
            logger.info(f"  - {tenant.name} ({tenant.slug}) - {status} - ID: {tenant.id}")


async def create_user(
    tenant_id: str,
    username: str,
    email: str,
    password: str,
    role: str = "user"
) -> User:
    """
    Create a new user.

    Args:
        tenant_id: Parent tenant ID
        username: Username
        email: Email address
        password: Plain text password (will be hashed)
        role: User role (admin, user, viewer)

    Returns:
        Created user
    """
    async with async_session_maker() as session:
        # Verify tenant exists
        tenant = await session.get(Tenant, tenant_id)
        if not tenant:
            raise ValueError(f"Tenant not found: {tenant_id}")

        user = User(
            id=uuid4(),
            tenant_id=tenant.id,
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            role=role,
            is_active=True,
            email_verified=False,
            profile_data={}
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        logger.success(f"Created user: {user.username} ({user.role}) - ID: {user.id}")
        return user


async def list_users(tenant_id: Optional[str] = None):
    """
    List users in the system.

    Args:
        tenant_id: Optional tenant ID to filter by
    """
    async with async_session_maker() as session:
        query = select(User)
        if tenant_id:
            query = query.where(User.tenant_id == tenant_id)

        result = await session.execute(query)
        users = result.scalars().all()

        if not users:
            logger.info("No users found.")
            return

        logger.info(f"Found {len(users)} user(s):")
        for user in users:
            status = "active" if user.is_active else "inactive"
            logger.info(
                f"  - {user.username} ({user.email}) - {user.role} - {status} - ID: {user.id}"
            )


async def reset_password(user_id: str, new_password: str):
    """
    Reset a user's password.

    Args:
        user_id: User ID
        new_password: New plain text password
    """
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        user.password_hash = get_password_hash(new_password)
        await session.commit()

        logger.success(f"Password reset for user: {user.username}")


async def deactivate_user(user_id: str):
    """
    Deactivate a user.

    Args:
        user_id: User ID
    """
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        user.is_active = False
        await session.commit()

        logger.success(f"Deactivated user: {user.username}")


async def activate_user(user_id: str):
    """
    Activate a user.

    Args:
        user_id: User ID
    """
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        user.is_active = True
        await session.commit()

        logger.success(f"Activated user: {user.username}")


async def delete_expired_tokens():
    """Delete all expired OAuth tokens from the database."""
    from datetime import datetime

    async with async_session_maker() as session:
        result = await session.execute(
            select(AdToken).where(
                AdToken.expires_at < datetime.utcnow(),
                AdToken.is_valid == False
            )
        )
        tokens = result.scalars().all()

        count = len(tokens)
        for token in tokens:
            await session.delete(token)

        await session.commit()
        logger.success(f"Deleted {count} expired token(s)")


async def system_stats():
    """Display system statistics."""
    async with async_session_maker() as session:
        tenant_count = (await session.execute(select(Tenant))).scalars().all()
        user_count = (await session.execute(select(User))).scalars().all()
        token_count = (await session.execute(select(AdToken))).scalars().all()
        dest_count = (await session.execute(select(Destination))).scalars().all()
        auto_count = (await session.execute(select(Automation))).scalars().all()

        active_tenants = sum(1 for t in tenant_count if t.is_active)
        active_users = sum(1 for u in user_count if u.is_active)
        valid_tokens = sum(1 for t in token_count if t.is_valid)
        active_automations = sum(1 for a in auto_count if a.status == "active")

        logger.info("System Statistics:")
        logger.info(f"  Tenants: {len(tenant_count)} total, {active_tenants} active")
        logger.info(f"  Users: {len(user_count)} total, {active_users} active")
        logger.info(f"  OAuth Tokens: {len(token_count)} total, {valid_tokens} valid")
        logger.info(f"  Destinations: {len(dest_count)} total")
        logger.info(f"  Automations: {len(auto_count)} total, {active_automations} active")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Administrative CLI tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Tenant commands
    tenant_parser = subparsers.add_parser("create-tenant", help="Create a new tenant")
    tenant_parser.add_argument("--name", required=True, help="Tenant name")
    tenant_parser.add_argument("--slug", required=True, help="URL-friendly slug")
    tenant_parser.add_argument("--inactive", action="store_true", help="Create as inactive")

    subparsers.add_parser("list-tenants", help="List all tenants")

    # User commands
    user_parser = subparsers.add_parser("create-user", help="Create a new user")
    user_parser.add_argument("--tenant-id", required=True, help="Tenant ID")
    user_parser.add_argument("--username", required=True, help="Username")
    user_parser.add_argument("--email", required=True, help="Email address")
    user_parser.add_argument("--password", required=True, help="Password")
    user_parser.add_argument("--role", default="user", choices=["admin", "user", "viewer"])

    list_users_parser = subparsers.add_parser("list-users", help="List users")
    list_users_parser.add_argument("--tenant-id", help="Filter by tenant ID")

    reset_pw_parser = subparsers.add_parser("reset-password", help="Reset user password")
    reset_pw_parser.add_argument("--user-id", required=True, help="User ID")
    reset_pw_parser.add_argument("--password", required=True, help="New password")

    deactivate_parser = subparsers.add_parser("deactivate-user", help="Deactivate user")
    deactivate_parser.add_argument("--user-id", required=True, help="User ID")

    activate_parser = subparsers.add_parser("activate-user", help="Activate user")
    activate_parser.add_argument("--user-id", required=True, help="User ID")

    # System commands
    subparsers.add_parser("delete-expired-tokens", help="Delete expired OAuth tokens")
    subparsers.add_parser("stats", help="Display system statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute commands
    try:
        if args.command == "create-tenant":
            asyncio.run(create_tenant(
                name=args.name,
                slug=args.slug,
                is_active=not args.inactive
            ))
        elif args.command == "list-tenants":
            asyncio.run(list_tenants())
        elif args.command == "create-user":
            asyncio.run(create_user(
                tenant_id=args.tenant_id,
                username=args.username,
                email=args.email,
                password=args.password,
                role=args.role
            ))
        elif args.command == "list-users":
            asyncio.run(list_users(tenant_id=args.tenant_id))
        elif args.command == "reset-password":
            asyncio.run(reset_password(args.user_id, args.password))
        elif args.command == "deactivate-user":
            asyncio.run(deactivate_user(args.user_id))
        elif args.command == "activate-user":
            asyncio.run(activate_user(args.user_id))
        elif args.command == "delete-expired-tokens":
            asyncio.run(delete_expired_tokens())
        elif args.command == "stats":
            asyncio.run(system_stats())
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
