from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND

import time

# Idle time-out
IDLE_TIMEOUT_SECONDS = 180 # 3 min inactivity



# Create a router object
# This behaves like a mini FastAPI app
router = APIRouter()

# Configure Jinja2 templates directory
templates = Jinja2Templates(directory="templates")


# Hardcoded credentials for demo purposes only
# In real applications, credentials come from a database
VALID_USERNAME = "admin"
VALID_PASSWORD = "password"


@router.get("/")
def home(request: Request):
    """
    Home page route.

    - Checks if a user is logged in using the session
    - Passes user info to the template
    """
    user = request.session.get("user")

    return templates.TemplateResponse(
        # Call home for the home page html; we used index for main form page
        request,
        "home.html",
        {
            "request": request,  
            "user": user
        }
    )


@router.get("/login")
def login_page(request: Request):
    """
    Displays the login form.

    If the user is already logged in,
    the template can choose what to display.
    """
    user = request.session.get("user")
    error = request.query_params.get("error")   # Checks if there is somethig named error, otherwise would return None


    if error == "session_expired":
        e_message = "The session has expired. Please log in again."
    elif error:
        e_message = "The username or password is invalid. Please try again."
    else:
        e_message = None

    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "request": request,
            "user": user,
            "error": e_message
        }
    )


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    Handles login form submission.

    - Reads username and password from the form
    - Validates credentials
    - Stores user info in session if valid
    """
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        # Store logged-in user in session
        request.session["user"] = username
        # For the time where user is last active
        request.session["last_active"] = time.time()

        # Redirect user to dashboard
        return RedirectResponse(
            url="/dashboard",
            status_code=HTTP_302_FOUND
        )

    # If credentials are invalid:
    # Redirect back to login page
    #
    # NOTE:
    # No error message is shown intentionally.

    # Students are expected to add Bootstrap alerts.
    return RedirectResponse(
        url="/login?error=1",   # Error response
        status_code=HTTP_302_FOUND
    )


@router.get("/dashboard")
def dashboard(request: Request):
    """
    Protected route.

    - Only accessible if user is logged in
    - Redirects to login page if session is missing
    """
    user = request.session.get("user")
    last_active = request.session.get("last_active")    # For when user was last active

    # If user is not logged, block access
    if not user or not last_active:
        return RedirectResponse(
            url="/login",
            status_code=HTTP_302_FOUND
        )


    # If user is idle and it is past the active, block access
    if time.time() - last_active > IDLE_TIMEOUT_SECONDS:
        request.session.clear()
        return RedirectResponse(
            url="/login?error=session_expired",
            status_code=HTTP_302_FOUND
        ) 

    # Else if the user is active, then keep the time refreshed to most recent
    request.session["last_active"] = time.time()

    # If user is logged in, render dashboard
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "user": user
        }
    )


@router.get("/logout")
def logout(request: Request):
    """
    Logs the user out.

    - Clears all session data
    - Redirects back to home page
    """
    request.session.clear()

    return RedirectResponse(
        url="/",
        status_code=HTTP_302_FOUND
    )
