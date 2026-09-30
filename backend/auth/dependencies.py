from typing import Optional
from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.services.auth_service import get_user_from_token

def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Retrieve current user from authorization header if present, otherwise None."""
    if not authorization:
        return None
    return get_user_from_token(db, authorization)

def require_authenticated_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Ensure valid session token is provided; raises 401 Unauthorized if absent or invalid."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. Please sign in."
        )
    user = get_user_from_token(db, authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please sign in again."
        )
    return user

def require_teacher(
    user: User = Depends(require_authenticated_user)
) -> User:
    """Enforce that the authenticated user possesses the TEACHER role. Raises 403 Forbidden for students."""
    if user.role.lower() != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Teacher role required to perform this action."
        )
    return user

def require_student(
    user: User = Depends(require_authenticated_user)
) -> User:
    """Enforce that the authenticated user possesses the STUDENT role. Raises 403 Forbidden for teachers where appropriate."""
    if user.role.lower() != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Student role required to perform this action."
        )
    return user
