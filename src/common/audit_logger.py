"""
Structured audit logging for security-sensitive operations.

This module provides a centralized audit logging system that tracks:
- Authentication events (login, logout, failed attempts)
- Authorization events (permission denied)
- Data access (sensitive resource access)
- Data modification (create, update, delete)
- Role changes
- Organization membership changes

Logs are structured in JSON format for easy parsing by external tools.
"""

import json
import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional

from fastapi import Request

# Configure audit logger - separate from application logger
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

# Create file handler for audit logs (separate from main logs)
audit_handler = logging.FileHandler('logs/audit.log')
audit_handler.setLevel(logging.INFO)

# JSON formatter for structured logging
formatter = logging.Formatter('%(message)s')
audit_handler.setFormatter(formatter)
audit_logger.addHandler(audit_handler)

# Prevent propagation to root logger
audit_logger.propagate = False


class EventType(str, Enum):
    """Types of audit events."""

    AUTHENTICATION = 'authentication'
    AUTHORIZATION = 'authorization'
    DATA_ACCESS = 'data_access'
    DATA_MODIFICATION = 'data_modification'
    SYSTEM = 'system'


class EventStatus(str, Enum):
    """Status of audit events."""

    SUCCESS = 'success'
    FAILURE = 'failure'
    ERROR = 'error'


class AuditLogger:
    """Centralized audit logging for security events."""

    @staticmethod
    def _log_event(
        event_type: EventType,
        action: str,
        status: EventStatus,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Internal method to log audit events.

        Args:
            event_type: Type of event (authentication, authorization, etc.)
            action: Specific action being performed
            status: Success, failure, or error
            user_id: ID of user performing action (if authenticated)
            organization_id: ID of organization context (if applicable)
            resource: Type of resource being accessed/modified
            resource_id: ID of specific resource
            ip_address: Client IP address
            user_agent: Client user agent string
            metadata: Additional context-specific data
        """
        audit_data = {
            'timestamp': datetime.now(UTC).isoformat(),
            'event_type': event_type.value,
            'action': action,
            'status': status.value,
            'user_id': user_id,
            'organization_id': organization_id,
            'resource': resource,
            'resource_id': resource_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'metadata': metadata or {},
        }

        # Log as JSON for structured logging
        audit_logger.info(json.dumps(audit_data))

    @staticmethod
    def log_auth_event(
        action: str,
        email: str,
        status: EventStatus,
        request: Request,
        user_id: Optional[int] = None,
        reason: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Log authentication-related events.

        Examples:
            - User login (successful/failed)
            - User logout
            - Password reset request
            - Email verification
            - Token refresh

        Args:
            action: Specific auth action (e.g., 'login', 'logout', 'password_reset')
            email: User's email address
            status: Success or failure
            request: FastAPI request object
            user_id: User ID (if available)
            reason: Reason for failure (if applicable)
            metadata: Additional context
        """
        meta = metadata or {}
        meta['email'] = email
        if reason:
            meta['reason'] = reason

        AuditLogger._log_event(
            event_type=EventType.AUTHENTICATION,
            action=action,
            status=status,
            user_id=user_id,
            resource='user',
            resource_id=email,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            metadata=meta,
        )

    @staticmethod
    def log_authz_event(
        action: str,
        user_id: int,
        organization_id: Optional[int],
        resource: str,
        resource_id: str,
        request: Request,
        required_permission: Optional[str] = None,
    ):
        """
        Log authorization/permission events.

        Examples:
            - Permission denied
            - Role check failed
            - Insufficient privileges

        Args:
            action: Authorization action (e.g., 'permission_denied')
            user_id: ID of user attempting action
            organization_id: Organization context (if applicable)
            resource: Type of resource
            resource_id: ID of resource
            request: FastAPI request object
            required_permission: Permission that was required
        """
        metadata = {}
        if required_permission:
            metadata['required_permission'] = required_permission

        AuditLogger._log_event(
            event_type=EventType.AUTHORIZATION,
            action=action,
            status=EventStatus.FAILURE,  # Authorization logs are typically failures
            user_id=user_id,
            organization_id=organization_id,
            resource=resource,
            resource_id=resource_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            metadata=metadata,
        )

    @staticmethod
    def log_data_access(
        action: str,
        user_id: int,
        organization_id: int,
        resource: str,
        resource_id: str,
        request: Request,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Log access to sensitive data.

        Examples:
            - Viewing organization details
            - Accessing payment information
            - Viewing user list
            - Exporting data

        Args:
            action: Data access action (e.g., 'view', 'export', 'download')
            user_id: ID of user accessing data
            organization_id: Organization context
            resource: Type of resource being accessed
            resource_id: ID of specific resource
            request: FastAPI request object
            metadata: Additional context
        """
        AuditLogger._log_event(
            event_type=EventType.DATA_ACCESS,
            action=action,
            status=EventStatus.SUCCESS,
            user_id=user_id,
            organization_id=organization_id,
            resource=resource,
            resource_id=resource_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            metadata=metadata,
        )

    @staticmethod
    def log_data_modification(
        action: str,
        user_id: int,
        organization_id: Optional[int],
        resource: str,
        resource_id: str,
        request: Request,
        status: EventStatus = EventStatus.SUCCESS,
        changes: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Log data modification events.

        Examples:
            - Creating a resource
            - Updating a resource
            - Deleting a resource
            - Role changes
            - Membership changes

        Args:
            action: Modification action (e.g., 'create', 'update', 'delete')
            user_id: ID of user making changes
            organization_id: Organization context (if applicable)
            resource: Type of resource being modified
            resource_id: ID of specific resource
            request: FastAPI request object
            status: Success or failure
            changes: Dictionary of what changed (before/after)
            metadata: Additional context
        """
        meta = metadata or {}
        if changes:
            meta['changes'] = changes

        AuditLogger._log_event(
            event_type=EventType.DATA_MODIFICATION,
            action=action,
            status=status,
            user_id=user_id,
            organization_id=organization_id,
            resource=resource,
            resource_id=resource_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            metadata=meta,
        )

    @staticmethod
    def log_system_event(
        action: str,
        status: EventStatus,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Log system-level events.

        Examples:
            - Application startup
            - Application shutdown
            - Configuration changes
            - Health check failures

        Args:
            action: System action
            status: Success or error
            metadata: Additional context
        """
        AuditLogger._log_event(
            event_type=EventType.SYSTEM,
            action=action,
            status=status,
            metadata=metadata,
        )


# Convenience functions for common audit events


def log_login_success(user_id: int, email: str, request: Request):
    """Log successful login."""
    AuditLogger.log_auth_event(
        action='login',
        email=email,
        status=EventStatus.SUCCESS,
        request=request,
        user_id=user_id,
    )


def log_login_failure(
    email: str, request: Request, reason: str = 'invalid_credentials'
):
    """Log failed login attempt."""
    AuditLogger.log_auth_event(
        action='login',
        email=email,
        status=EventStatus.FAILURE,
        request=request,
        reason=reason,
    )


def log_logout(user_id: int, email: str, request: Request):
    """Log user logout."""
    AuditLogger.log_auth_event(
        action='logout',
        email=email,
        status=EventStatus.SUCCESS,
        request=request,
        user_id=user_id,
    )


def log_password_reset_request(email: str, request: Request):
    """Log password reset request."""
    AuditLogger.log_auth_event(
        action='password_reset_request',
        email=email,
        status=EventStatus.SUCCESS,
        request=request,
    )


def log_password_reset_complete(user_id: int, email: str, request: Request):
    """Log password reset completion."""
    AuditLogger.log_auth_event(
        action='password_reset_complete',
        email=email,
        status=EventStatus.SUCCESS,
        request=request,
        user_id=user_id,
    )


def log_email_verification(user_id: int, email: str, request: Request):
    """Log email verification."""
    AuditLogger.log_auth_event(
        action='email_verification',
        email=email,
        status=EventStatus.SUCCESS,
        request=request,
        user_id=user_id,
    )


def log_permission_denied(
    user_id: int,
    organization_id: Optional[int],
    resource: str,
    resource_id: str,
    request: Request,
    required_permission: str,
):
    """Log permission denied event."""
    AuditLogger.log_authz_event(
        action='permission_denied',
        user_id=user_id,
        organization_id=organization_id,
        resource=resource,
        resource_id=resource_id,
        request=request,
        required_permission=required_permission,
    )


def log_role_change(
    user_id: int,
    organization_id: int,
    target_user_id: int,
    old_role: str,
    new_role: str,
    request: Request,
):
    """Log role change."""
    AuditLogger.log_data_modification(
        action='role_change',
        user_id=user_id,
        organization_id=organization_id,
        resource='user_role',
        resource_id=str(target_user_id),
        request=request,
        changes={'old_role': old_role, 'new_role': new_role},
    )


def log_organization_member_added(
    user_id: int,
    organization_id: int,
    new_member_id: int,
    role: str,
    request: Request,
):
    """Log new organization member added."""
    AuditLogger.log_data_modification(
        action='member_added',
        user_id=user_id,
        organization_id=organization_id,
        resource='organization_member',
        resource_id=str(new_member_id),
        request=request,
        metadata={'role': role},
    )


def log_organization_member_removed(
    user_id: int,
    organization_id: int,
    removed_member_id: int,
    request: Request,
):
    """Log organization member removed."""
    AuditLogger.log_data_modification(
        action='member_removed',
        user_id=user_id,
        organization_id=organization_id,
        resource='organization_member',
        resource_id=str(removed_member_id),
        request=request,
    )
