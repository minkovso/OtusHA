from fastapi import FastAPI
from .routers import login, user, friend, post, dialog
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse
from app.hub import LocalHub
from contextlib import asynccontextmanager

hub = LocalHub()
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.hub = hub
    await app.state.hub.start()
    try:
        yield
    finally:
        await app.state.hub.stop()
app = FastAPI(
    title='OtusHA',
    description='Домашнее задание 5',
    version='1.0.0',
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan
)

app.include_router(login.router)
app.include_router(user.router, prefix='/user')
app.include_router(friend.router, prefix='/friend')
app.include_router(post.router, prefix='/post')
app.include_router(dialog.router, prefix='/dialog')

@app.get('/docs', include_in_schema=False)
def get_swagger_ui():
    return get_swagger_ui_html(
        openapi_url='/openapi.yaml',
        title='Custom Swagger UI'
    )

@app.get('/openapi.yaml', include_in_schema=False)
def get_openapi_yaml():
    return FileResponse('app/openapi.yaml', media_type='application/yaml')
