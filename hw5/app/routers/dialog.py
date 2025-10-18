from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import psycopg
import jwt
from jwt.exceptions import InvalidSignatureError
from pydantic import BaseModel
from couchbase.kv_range_scan import PrefixScan
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator
import ulid

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

def get_couch_conn():
    cluster = Cluster(
        os.getenv('COUCH_HOST'),
        ClusterOptions(PasswordAuthenticator(os.getenv('COUCH_USER'), os.getenv('COUCH_PASSWORD')))
    )
    bucket = cluster.bucket(os.getenv('COUCH_BUCKET'))
    return bucket

class DialogSendRequest(BaseModel):
    text: str

@router.post('/{friend_id}/send')
def dialog_send(friend_id: str, data: DialogSendRequest, user_id: str = Depends(check_token)):
    conn = get_db_conn()
    select_friend = '''
        SELECT 1
          FROM prod.friends
         WHERE user_id = %s
               AND friend_id = %s
    '''
    with conn, conn.cursor() as cur:
        cur.execute(select_friend, (user_id, friend_id))
        row = cur.fetchone()
    if row:
        bucket = get_couch_conn()
        scope = bucket.scope('prod')
        coll = scope.collection('messages')
        dialog_id = f'{min((friend_id, user_id))}_{max((friend_id, user_id))}'
        message_id = ulid.new()
        doc_id = f'{dialog_id}:{message_id}'
        doc = {
            'from': user_id,
            'to': friend_id,
            'text': data.text,
            'created_at': message_id.timestamp().datetime.replace(tzinfo=None, microsecond=0).isoformat()
        }
        coll.insert(doc_id, doc)
        raise HTTPException(status_code=200, detail='Сообщение успешно отправлено')
    else:
        raise HTTPException(status_code=400, detail='Невалидные данные')

class DialogListResponse(BaseModel):
    user_id: str
    friend_id: str
    text: str

@router.get('/{friend_id}/list', response_model=list[DialogListResponse])
def dialog_list(friend_id: str, user_id: str = Depends(check_token)):
    conn = get_db_conn()
    select_friend = '''
        SELECT 1
          FROM prod.friends
         WHERE user_id = %s
               AND friend_id = %s
    '''
    with conn, conn.cursor() as cur:
        cur.execute(select_friend, (user_id, friend_id))
        row = cur.fetchone()
    if row:
        bucket = get_couch_conn()
        scope = bucket.scope('prod')
        coll = scope.collection('messages')
        dialog_id = f'{min((friend_id, user_id))}_{max((friend_id, user_id))}'
        prefix = f'{dialog_id}:'
        scan = PrefixScan(prefix)
        messages = []
        for item in coll.scan(scan):
            text = item.content_as[dict]['text']
            messages.append(DialogListResponse(
                user_id=user_id,
                friend_id=friend_id,
                text=text
            ))
        return messages
    else:
        raise HTTPException(status_code=400, detail='Невалидные данные')
