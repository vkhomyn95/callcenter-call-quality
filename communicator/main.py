import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from communicator.routes import CustomHTTPException
from communicator.routes import auth, transcribe, api, transcription, hook

from communicator.routes import user
from communicator.variables import variables

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

app.mount("/static", StaticFiles(directory=variables.base_dir + "/static"), name="static")
templates = Jinja2Templates(directory=variables.base_dir + "/templates")


@app.exception_handler(CustomHTTPException)
async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": exc.success, "message": exc.message}
    )

# Include the routers
app.include_router(transcribe.router, prefix="/api/v1")
app.include_router(api.router, prefix="/api/v1/user")
app.include_router(auth.router)
app.include_router(user.router, prefix="/users")
app.include_router(transcription.router, prefix="/transcriptions")

app.include_router(hook.router, prefix="/webhooks")


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=variables.app_host,
        port=variables.app_port
    )
