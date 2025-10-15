from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import psycopg
import jwt
from jwt.exceptions import InvalidSignatureError
from pydantic import BaseModel
import uuid
import redis
from datetime import datetime
from typing import Optional, Tuple
import json

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

def get_reddis_conn():
    r = redis.Redis(host=os.getenv('REDIS_HOST'), port=int(os.getenv('REDIS_PORT')), decode_responses=True)
    return r

class PostCreateRequest(BaseModel):
    text: str

class PostCreateResponse(BaseModel):
    post_id: str

@router.post('/create', response_model=PostCreateResponse)
def post_create(data: PostCreateRequest, user_id: str = Depends(check_token)):
    conn = get_db_conn()
    r = get_reddis_conn()
    insert_post = '''
        INSERT INTO prod.posts (post_id, user_id, text)
        VALUES (%s, %s, %s)
    '''
    select_friends = '''
        SELECT user_id
          FROM prod.friends
         WHERE friend_id = %s
    '''
    post_id = str(uuid.uuid4())
    with conn, conn.cursor() as cur:
        cur.execute(insert_post, (post_id, user_id, data.text))
        conn.commit()
        cur.execute(select_friends, (user_id, ))
        rows = cur.fetchall()
    for friend_id, in rows:
        key = f'feeds:{friend_id}'
        r.zadd(key, {post_id: int(datetime.now().replace(microsecond=0).timestamp())})
        r.zremrangebyrank(key, 0, -1001)
    key = f'users:{user_id}'
    r.zadd(key, {post_id: int(datetime.now().replace(microsecond=0).timestamp())})
    r.zremrangebyrank(key, 0, -1001)
    return PostCreateResponse(post_id=post_id)

class PostUpdateRequest(BaseModel):
    post_id: str
    text: str

@router.put('/update')
def post_update(data: PostUpdateRequest, user_id: str = Depends(check_token)):
    conn = get_db_conn()
    r = get_reddis_conn()
    update_post = '''
        UPDATE prod.posts
           SET text = %s, updated_at = NOW()
         WHERE post_id = %s
               AND user_id = %s
    '''
    select_friends = '''
        SELECT user_id
          FROM prod.friends
         WHERE friend_id = %s
    '''
    with conn, conn.cursor() as cur:
        cur.execute(update_post, (data.text, data.post_id, user_id))
        updated = cur.rowcount
        if updated:
            conn.commit()
            cur.execute(select_friends, (user_id, ))
            rows = cur.fetchall()
    if updated:
        for friend_id, in rows:
            key = f'feeds:{friend_id}'
            r.zadd(key, {data.post_id: int(datetime.now().replace(microsecond=0).timestamp())})
            r.zremrangebyrank(key, 0, -1001)
        key = f'users:{user_id}'
        r.zadd(key, {data.post_id: int(datetime.now().replace(microsecond=0).timestamp())})
        r.zremrangebyrank(key, 0, -1001)
        key = f'posts:{data.post_id}'
        r.set(key, json.dumps([user_id, data.text]))
        r.expire(key, 3600)
        raise HTTPException(status_code=200, detail='Пост успешно изменен')
    else:
        raise HTTPException(status_code=400, detail='Невалидные данные')

@router.put('/delete/{post_id}')
def post_delete(post_id: str, user_id: str = Depends(check_token)):
    conn = get_db_conn()
    r = get_reddis_conn()
    delete_post = '''
        DELETE FROM prod.posts
         WHERE post_id = %s
               AND user_id = %s
    '''
    select_friends = '''
        SELECT user_id
          FROM prod.friends
         WHERE friend_id = %s
    '''
    with conn, conn.cursor() as cur:
        cur.execute(delete_post, (post_id, user_id))
        deleted = cur.rowcount
        if deleted:
            conn.commit()
            cur.execute(select_friends, (user_id, ))
            rows = cur.fetchall()
    if deleted:
        for friend_id, in rows:
            r.zrem(f'feeds:{friend_id}', post_id)
        r.zrem(f'users:{user_id}', post_id)
        raise HTTPException(status_code=200, detail='Пост успешно удален')
    else:
        raise HTTPException(status_code=400, detail='Невалидные данные')

def _post_get(post_id: str) -> Optional[Tuple[str, str]]:
    r = get_reddis_conn()
    key = f'posts:{post_id}'
    row = r.get(key)
    if not row:
        conn = get_db_conn()
        select_post = '''
            SELECT user_id, text
              FROM prod.posts 
             WHERE post_id = %s
        '''
        with conn, conn.cursor() as cur:
            cur.execute(select_post, (post_id, ))
            row = cur.fetchone()
    if row:
        if isinstance(row, str):
            user_id, text = json.loads(row)
        else:
            user_id, text = row
            r.set(key, json.dumps([user_id, text]))
        r.expire(key, 3600)
        return user_id, text

class PostGetResponse(BaseModel):
    post_id: str
    user_id: str
    text: str

@router.get('/get/{post_id}', response_model=PostGetResponse)
def post_get(post_id: str, _: str = Depends(check_token)):
    post = _post_get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail='Пост не найден')
    else:
        user_id, text = post
        return PostGetResponse(
            post_id=post_id,
            user_id=user_id,
            text=text
        )

class PostFeedResponse(BaseModel):
    post_id: str
    user_id: str
    text: str

@router.get('/feed', response_model=list[PostFeedResponse])
def post_get(offset: int = 0, limit: int = 10, user_id: str = Depends(check_token)):
    r = get_reddis_conn()
    post_ids = r.zrevrange(f'feeds:{user_id}', offset, offset + limit - 1)
    posts = []
    for post_id in post_ids:
        post = _post_get(post_id)
        friend_id, text = post
        posts.append(PostFeedResponse(
            post_id=post_id,
            user_id=friend_id,
            text=text
        ))
    return posts
