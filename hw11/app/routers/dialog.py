from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import psycopg
import jwt
from jwt.exceptions import InvalidSignatureError
from pydantic import BaseModel
from ..proto import dialog_pb2

router = APIRouter()
security = HTTPBearer()

def check_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, os.getenv('SECRET_KEY'), algorithms=['HS256'])
    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail='Неавторизованный доступ')
    return payload['user_id']

def get_db_conn():
    conn = psycopg.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    return conn

class DialogSendRequest(BaseModel):
    text: str

@router.post('/{friend_id}/send')
def dialog_send(
    friend_id: str,
    data: DialogSendRequest,
    request: Request,
    user_id: str = Depends(check_token)
):
    conn = get_db_conn()
    check_user = '''
        SELECT 1
        FROM prod.users
        WHERE user_id = %s
    '''
    with conn, conn.cursor() as cur:
        cur.execute(check_user, (friend_id, ))
        row = cur.fetchone()
    if row:
        md = [('request_id', request.state.request_id)]
        ack = request.app.state.grpc_stub.Send(dialog_pb2.Message(
            user_id=user_id,
            friend_id=friend_id,
            text=data.text,
        ), metadata=md)
        if ack.ok:
            raise HTTPException(status_code=200, detail='Сообщение успешно отправлено')
        else:
            raise HTTPException(status_code=500, detail='Ошибка сервера')
    else:
        raise HTTPException(status_code=400, detail='Невалидные данные')

class DialogListResponse(BaseModel):
    user_id: str
    friend_id: str
    text: str

@router.get('/{friend_id}/list', response_model=list[DialogListResponse])
def dialog_list(
    friend_id: str,
    request: Request,
    user_id: str = Depends(check_token)
):
    conn = get_db_conn()
    check_user = '''
        SELECT 1
        FROM prod.users
        WHERE user_id = %s
    '''
    with conn, conn.cursor() as cur:
        cur.execute(check_user, (friend_id, ))
        row = cur.fetchone()
    if row:
        md = [('request_id', request.state.request_id)]
        rows = request.app.state.grpc_stub.List(dialog_pb2.Dialog(
            user_id=user_id,
            friend_id=friend_id,
        ), metadata=md)
        messages = []
        for row in rows.items:
            messages.append(DialogListResponse(
                user_id=row.user_id,
                friend_id=row.friend_id,
                text=row.text
            ))
        return messages
    else:
        raise HTTPException(status_code=400, detail='Невалидные данные')
