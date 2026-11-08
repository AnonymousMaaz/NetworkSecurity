from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

web_app = FastAPI(
    title="NetworkSecurity Workspace",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

web_app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@web_app.get("/", response_class=HTMLResponse)
def workspace(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )
