from fastapi import FastAPI
from .routers import login, user
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse

app = FastAPI(
    title='OtusHA',
    description='Домашнее задание 1',
    version='1.0.0',
    docs_url=None,
    redoc_url=None
)

app.include_router(login.router)
app.include_router(user.router, prefix='/user')

@app.get('/docs', include_in_schema=False)
def get_swagger_ui():
    return get_swagger_ui_html(
        openapi_url='/openapi.yaml',
        title='OtusHA'
    )

@app.get('/openapi.yaml', include_in_schema=False)
def get_openapi_yaml():
    return FileResponse('app/openapi.yaml', media_type='application/yaml')
