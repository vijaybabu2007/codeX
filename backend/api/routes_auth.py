from typing import Optional
import urllib.parse
from fastapi import APIRouter, HTTPException, Header, Depends, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.config import is_google_oauth_configured, get_effective_google_client_id
from backend.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserProfile
)
from backend.services.auth_service import (
    register_user,
    authenticate_user,
    get_user_from_token,
    revoke_session,
    EMAIL_REGEX
)
from backend.services.google_oauth_service import (
    create_oauth_state,
    verify_oauth_state,
    build_google_authorization_url,
    exchange_code_for_tokens,
    fetch_google_user_profile,
    authenticate_or_create_google_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def register_endpoint(
    payload: RegisterRequest,
    db: Session = Depends(get_db)
):
    email = payload.email.strip().lower()
    if not email or not EMAIL_REGEX.match(email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please enter a valid email address."
        )

    try:
        user, token = register_user(
            db=db,
            name=payload.name,
            email=email,
            password=payload.password,
            confirm_password=payload.confirm_password,
            role=payload.role,
            student_id=payload.student_id
        )
        return LoginResponse(
            token=token,
            user_id=user.id,
            name=user.name,
            role=user.role.upper(),
            authenticated=True,
            user=UserProfile(
                id=user.id,
                user_id=user.id,
                name=user.name,
                email=user.email,
                role=user.role.lower(),
                student_id=user.student_id,
                authenticated=True,
                created_at=user.created_at.isoformat() if user.created_at else None
            ),
            message="Account registered successfully."
        )
    except KeyError as ke:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ke).strip("'\""))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=LoginResponse)
def login_endpoint(
    payload: LoginRequest,
    db: Session = Depends(get_db)
):
    ident = (payload.identifier or payload.email or "").strip()
    password = payload.password.strip()

    if not ident:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide your institutional email, Student ID, or Teacher ID."
        )

    if not password or len(password) < 4:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Password must be at least 4 characters."
        )

    try:
        user, token = authenticate_user(
            db=db,
            email=ident,
            password=password,
            expected_role=payload.role
        )
        return LoginResponse(
            token=token,
            user_id=user.id,
            name=user.name,
            role=user.role.upper(),
            authenticated=True,
            user=UserProfile(
                id=user.id,
                user_id=user.id,
                name=user.name,
                email=user.email,
                role=user.role.lower(),
                student_id=user.student_id,
                authenticated=True,
                created_at=user.created_at.isoformat() if user.created_at else None
            ),
            message="Authentication successful."
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Login failed: {str(e)}")

@router.get("/me", response_model=UserProfile)
def get_current_user_endpoint(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. Please sign in."
        )
    user = get_user_from_token(db, authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please sign in again."
        )
    return UserProfile(
        id=user.id,
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.lower(),
        student_id=user.student_id,
        authenticated=True,
        created_at=user.created_at.isoformat() if user.created_at else None
    )

@router.post("/logout")
def logout_endpoint(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    if authorization:
        revoke_session(db, authorization)
    return {"message": "Signed out successfully."}


@router.get("/providers")
def get_auth_providers_endpoint():
    """
    Returns authentication provider availability:
    - google: active if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are configured
    - microsoft: coming soon
    - github: coming soon
    """
    google_configured = is_google_oauth_configured()
    return {
        "google": {
            "enabled": google_configured,
            "client_id": get_effective_google_client_id() if google_configured else None,
            "status": "ready" if google_configured else "not_configured",
            "message": "Real Google OAuth 2.0 active" if google_configured else "Google Sign-In is not configured for this deployment. Please use email/password or configure Google OAuth credentials."
        },
        "microsoft": {
            "enabled": False,
            "status": "coming_soon",
            "message": "Microsoft authentication coming soon."
        },
        "github": {
            "enabled": False,
            "status": "coming_soon",
            "message": "GitHub authentication coming soon."
        }
    }


@router.get("/google")
def google_oauth_login_endpoint(
    intended_role: Optional[str] = Query("student", description="Intended role for new user registration: 'teacher' or 'student'"),
    redirect: bool = Query(True, description="Whether to issue an HTTP 302 redirect or return JSON with authorization_url")
):
    """
    Initiates Google OAuth 2.0 Authorization Code flow.
    Generates a cryptographically signed CSRF state parameter encoding the requested role.
    """
    if not is_google_oauth_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Sign-In is not configured for this deployment. Please use email/password or configure Google OAuth credentials."
        )

    clean_role = "teacher" if str(intended_role).lower() == "teacher" else "student"
    state_token = create_oauth_state(intended_role=clean_role)

    try:
        auth_url = build_google_authorization_url(state=state_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Google authorization URL: {str(e)}"
        )

    if redirect:
        return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    return {"authorization_url": auth_url, "state": state_token}


@router.get("/google/callback")
def google_oauth_callback_endpoint(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Google OAuth 2.0 callback endpoint:
    - Validates cryptographic state and TTL
    - Exchanges authorization code for tokens
    - Fetches Google profile and verifies email
    - Authoritatively maps or creates LessonFoundry user
    - Issues application session token
    - Redirects to frontend with session credentials
    """
    if error:
        err_msg = error_description or error or "Google Sign-In was cancelled or denied."
        return RedirectResponse(
            url=f"/login?error={urllib.parse.quote(err_msg)}",
            status_code=status.HTTP_302_FOUND
        )

    if not code or not state:
        return RedirectResponse(
            url="/login?error=" + urllib.parse.quote("Missing authorization code or state parameter from Google."),
            status_code=status.HTTP_302_FOUND
        )

    # 1. Cryptographic state verification
    try:
        state_data = verify_oauth_state(state)
    except ValueError as ve:
        return RedirectResponse(
            url=f"/login?error={urllib.parse.quote(str(ve))}",
            status_code=status.HTTP_302_FOUND
        )

    intended_role = state_data.get("role", "student")

    # 2. Exchange authorization code with Google token endpoint
    try:
        tokens = exchange_code_for_tokens(code)
    except Exception as e:
        return RedirectResponse(
            url=f"/login?error={urllib.parse.quote(str(e))}",
            status_code=status.HTTP_302_FOUND
        )

    # 3. Fetch verified user identity from Google OpenID userinfo
    try:
        profile = fetch_google_user_profile(tokens["access_token"])
    except Exception as e:
        return RedirectResponse(
            url=f"/login?error={urllib.parse.quote(str(e))}",
            status_code=status.HTTP_302_FOUND
        )

    # 4. Resolve or create user with authoritative role handling
    try:
        user, session_token = authenticate_or_create_google_user(
            db=db,
            google_profile=profile,
            intended_role=intended_role
        )
    except ValueError as ve:
        return RedirectResponse(
            url=f"/login?error={urllib.parse.quote(str(ve))}",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        return RedirectResponse(
            url="/login?error=" + urllib.parse.quote("An unexpected error occurred during Google authentication."),
            status_code=status.HTTP_302_FOUND
        )

    # 5. Success: Redirect to frontend login handler with session token
    redirect_url = f"/login?oauth_token={session_token}&role={user.role.lower()}&user_id={user.id}&name={urllib.parse.quote(user.name)}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

