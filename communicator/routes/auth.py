import typing

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from werkzeug.security import check_password_hash

from communicator.database import mariadb
from communicator.variables import variables

router = APIRouter()

templates = Jinja2Templates(directory=variables.base_dir + "/templates")


@router.get("/", response_class=HTMLResponse)
@router.get("/login/", response_class=HTMLResponse)
def login(request: Request):
    """
    Handle the login page.

    GET:
        Renders the 'login.html' template to display the login form.

    POST:
        Processes the login form submission.
        - If the username or password is missing, flashes an error message and redirects to the login page.
        - Strips leading/trailing whitespace from the username and password.
        - Loads the user by username.
        - Checks the password hash against the provided password.
        - If the credentials are valid, sets the user session and redirects to the dashboard.
        - Otherwise, flashes an error message and re displays the login page.

    Templates:
        - login.html: The template for the login page.
    """
    if "user" in request.session:
        return RedirectResponse(url="/users", status_code=303)
    return templates.TemplateResponse('login.html', {'request': request})


@router.post("/", response_class=HTMLResponse)
@router.post("/login/", response_class=HTMLResponse)
async def auth(request: Request):
    """
    Handle the login page.

    GET:
       Renders the 'login.html' template to display the login form.

    POST:
       Processes the login form submission.
       - If the username or password is missing, flashes an error message and redirects to the login page.
       - Strips leading/trailing whitespace from the username and password.
       - Loads the user by username.
       - Checks the password hash against the provided password.
       - If the credentials are valid, sets the user session and redirects to the dashboard.
       - Otherwise, flashes an error message and re displays the login page.

    Templates:
       - login.html: The template for the login page.
    """
    form = await request.form()

    if not form.get("username") or not form.get("password"):
        flash(request, "Invalid username or password")
        return RedirectResponse(url="/login/", status_code=303)
    else:
        username = form.get("username").strip()
        password = form.get("password").strip()

    user = mariadb.load_user_by_username(username, None)
    if user and check_password_hash(user.password, password):
        request.session["user"] = user.json()
        return RedirectResponse(url="/users", status_code=303)
    else:
        flash(request, "Invalid username or password")
        return RedirectResponse(url="/login/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    """
    Handle user logout.

    GET:
        Logs out the current user by removing the 'user' key from the session.
        Redirects the user to the login page after logging out.

    Templates:
        - None: This endpoint does not render a template; it only performs a redirect.
    """
    request.session.pop("user")
    return RedirectResponse(url="/login/", status_code=303)


def flash(request: Request, message: typing.Any, category: str = "primary") -> None:
    if "_messages" not in request.session:
        request.session["_messages"] = []
        request.session["_messages"].append({"message": message, "category": category})


def get_flashed_messages(request: Request):
    return request.session.pop("_messages") if "_messages" in request.session else []


templates.env.globals["get_flashed_messages"] = get_flashed_messages
