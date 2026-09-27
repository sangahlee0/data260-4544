from fastapi import APIRouter, Request, Form, Response, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from pydantic import BaseModel

import time
import secrets

from backend.database import get_db
from backend import crud, schema
from backend.session_crud import create_session, get_session, delete_session
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

# Create a router object
# This behaves like a mini FastAPI app
router = APIRouter()

# Hardcoded credentials for demo purposes only
# In real applications, credentials come from a database
#VALID_USERNAME = "admin@example.com"
#VALID_PASSWORD = "password"

password_hash = PasswordHash.recommended()

class ReactLoginReq(BaseModel):
    email: str
    password: str

@router.post("/auth/login")
def react_login(data: ReactLoginReq, response: Response, db: Session = Depends(get_db)):
    # Find the user using email
    user = crud.get_user_by_email(db, data.email)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Verify the password
    #if data.password != "password":
    if not password_hash.verify(data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create and store the session in MySQL
    session = create_session(db,user_id=user.id)

    # Store only the session token in the cookie
    response.set_cookie(
        key="session_id",
        value=session.id,
        httponly=True,
        samesite="lax",
        max_age=30 * 60
    )

    return {"user_id": user.id, "email": user.email}

@router.get("/auth/me")
def react_me(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_id")

    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Login required"
        )
    # Check
    session = get_session(db, session_token)

    if not session:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid"
        )
    
    user = crud.get_user(db, session.user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User is not found"
        )
    return {
        "user_id": user.id,
        "email": user.email
    }


@router.post("/auth/logout")
def react_logout(request: Request, response: Response, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_id")
    if session_token:
        delete_session(db, session_token)

    response.delete_cookie("session_id")

    return {"message": "Logged out"}

# @router.get("/")
# def home(request: Request):
#     """
#     Home page route.

#     - Checks if a user is logged in using the session
#     - Passes user info to the template
#     """
#     user = request.session.get("user")

#     return templates.TemplateResponse(
#         # Call home for the home page html; we used index for main form page
#         request,
#         "home.html",
#         {
#             "request": request,  
#             "user": user
#         }
#     )


# @router.get("/login")
# def login_page(request: Request):
#     """
#     Displays the login form.

#     If the user is already logged in,
#     the template can choose what to display.
#     """
#     user = request.session.get("user")
#     error = request.query_params.get("error")   # Checks if there is somethig named error, otherwise would return None


#     if error == "session_expired":
#         e_message = "The session has expired. Please log in again."
#     elif error:
#         e_message = "The username or password is invalid. Please try again."
#     else:
#         e_message = None

#     return templates.TemplateResponse(
#         request,
#         "login.html",
#         {
#             "request": request,
#             "user": user,
#             "error": e_message
#         }
#     )


# @router.post("/login")
# def login(request: Request, username: str = Form(...), password: str = Form(...)):
#     """
#     Handles login form submission.

#     - Reads username and password from the form
#     - Validates credentials
#     - Stores user info in session if valid
#     """
#     if username == VALID_USERNAME and password == VALID_PASSWORD:
#         # Store logged-in user in session
#         request.session["user"] = username
#         # For the time where user is last active
#         request.session["last_active"] = time.time()

#         # Redirect user to dashboard
#         return RedirectResponse(
#             url="/dashboard",
#             status_code=HTTP_302_FOUND
#         )

#     # If credentials are invalid:
#     # Redirect back to login page
#     #
#     # NOTE:
#     # No error message is shown intentionally.

#     # Students are expected to add Bootstrap alerts.
#     return RedirectResponse(
#         url="/login?error=1",   # Error response
#         status_code=HTTP_302_FOUND
#     )


# @router.get("/dashboard")
# def dashboard(request: Request):
#     """
#     Protected route.

#     - Only accessible if user is logged in
#     - Redirects to login page if session is missing
#     """
#     user = request.session.get("user")
#     last_active = request.session.get("last_active")    # For when user was last active

#     # If user is not logged, block access
#     if not user or not last_active:
#         return RedirectResponse(
#             url="/login",
#             status_code=HTTP_302_FOUND
#         )


#     # If user is idle and it is past the active, block access
#     if time.time() - last_active > IDLE_TIMEOUT_SECONDS:
#         request.session.clear()
#         return RedirectResponse(
#             url="/login?error=session_expired",
#             status_code=HTTP_302_FOUND
#         ) 

#     # Else if the user is active, then keep the time refreshed to most recent
#     request.session["last_active"] = time.time()

#     # If user is logged in, render dashboard
#     return templates.TemplateResponse(
#         request,
#         "dashboard.html",
#         {
#             "request": request,
#             "user": user
#         }
#     )


# @router.get("/logout")
# def logout(request: Request):
#     """
#     Logs the user out.

#     - Clears all session data
#     - Redirects back to home page
#     """
#     request.session.clear()

#     return RedirectResponse(
#         url="/",
#         status_code=HTTP_302_FOUND
#     )

# class ReactLoginReq(BaseModel):
#     email: str
#     password: str

# @router.post("/auth/login")
# def react_login(data: ReactLoginReq, response: Response):
#     if data.email != VALID_USERNAME or data.password != VALID_PASSWORD:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid email or password"
#         )

#     session_token = secrets.token_urlsafe(32)

#     response.set_cookie(
#         key="session_token",
#         value=session_token,
#         httponly=True,
#         samesite="lax"
#     )

#     return {
#         "user_id": 1
#     }
# @router.get("/auth/me")
# def react_me(request: Request):
#     session_token = request.cookies.get("session_token")
#     if not session_token:
#         raise HTTPException(
#             status_code=401,
#             detail="Login required"
#         )

#     return {
#         "user_id": 1
#     }

# @router.post("/auth/logout")
# def react_logout(request: Request, response: Response):
#     session_token = request.cookies.get("session_token")
#     response.delete_cookie("session_token")

#     return {
#         "message": "Logged out"
#     }