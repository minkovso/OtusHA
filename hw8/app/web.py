from fastapi import FastAPI, Request
from .routers import login, user, friend, post, dialog
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse
from .hub import LocalHub
from contextlib import asynccontextmanager
import logging
import ulid
import grpc
from .proto import dialog_pb2_grpc
import os

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [request_id=%(request_id)s] %(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.hub = LocalHub()
    await app.state.hub.start()
    target = os.getenv('DIALOG_HOST') + ':' + os.getenv('DIALOG_PORT')
    app.state.grpc_channel = grpc.insecure_channel(target)
    app.state.grpc_stub = dialog_pb2_grpc.DialogServiceStub(app.state.grpc_channel)
    try:
        yield
    finally:
        await app.state.hub.stop()
        app.state.grpc_channel.close()

app = FastAPI(
    title='OtusHA',
    description='Домашнее задание 8',
    version='1.0.0',
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan
)

@app.middleware("http")
async def request_id_mw(request: Request, call_next):
    request_id = request.headers.get('request_id') or str(ulid.new())
    request.state.request_id = request_id
    logger.info('HTTP request in', extra={'request_id': request_id})
    resp = await call_next(request)
    resp.headers['request_id'] = request_id
    logger.info('HTTP response out', extra={'request_id': request_id})
    return resp

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
