"""
JWT Authentication Router for Homework7
Replaces the previous cookie-session auth with stateless JWT bearer tokens.

Endpoint Information:
POST /auth/login  – accept username + password, return JWT access token
GET  /auth/me     – return the authenticated user's identity and role
POST /auth/logout – (stub) clears any leftover session cookie; JWT is stateless
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import create_access_token, verify_password
from backend import crud
from backend.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

# POST /auth/login
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticate a user and return a signed JWT access token.

    - Valid credentials   → 200 + {"access_token": "...", "token_type": "bearer"}
    - Invalid credentials → 401 Unauthorized
    """
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

# GET /auth/me
@router.get("/me")
def read_me(current_user=Depends(get_current_user)):
    """Return the authenticated user's identity and role.

    Requires a valid Bearer token in the Authorization header.
    """
    return {
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
    }
