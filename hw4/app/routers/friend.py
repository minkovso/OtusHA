from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import psycopg
import jwt
from jwt.exceptions import InvalidSignatureError
from psycopg.errors import ForeignKeyViolation, UniqueViolation
import redis

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

@router.put('/add/{friend_id}')
def friend_add(friend_id: str, user_id: str = Depends(check_token)):
    conn = get_db_conn()
    r = get_reddis_conn()
    insert_friend = '''
        INSERT INTO prod.friends (user_id, friend_id)
        VALUES (%s, %s)
    '''
    with conn, conn.cursor() as cur:
        try:
            cur.execute(insert_friend, (user_id, friend_id))
        except (ForeignKeyViolation, UniqueViolation):
            raise HTTPException(status_code=400, detail='Невалидные данные')
        conn.commit()
    friend_posts = r.zrange(f'users:{friend_id}', 0, -1, withscores=True)
    key = f'feeds:{user_id}'
    for post_id, updated_at in friend_posts:
        r.zadd(key, {post_id: updated_at})
    r.zremrangebyrank(key, 0, -1001)
    raise HTTPException(status_code=200, detail='Друг успешно добавлен')

@router.put('/delete/{friend_id}')
def friend_delete(friend_id: str, user_id: str = Depends(check_token)):
    conn = get_db_conn()
    r = get_reddis_conn()
    delete_friend = '''
        DELETE FROM prod.friends
         WHERE user_id = %s
               AND friend_id = %s
    '''
    with conn, conn.cursor() as cur:
        cur.execute(delete_friend, (user_id, friend_id))
        deleted = cur.rowcount
        conn.commit()
    if deleted:
        friend_posts = r.zrange(f'users:{friend_id}', 0, -1, withscores=True)
        for post_id, updated_at in friend_posts:
            r.zrem(f'feeds:{user_id}', post_id)
        raise HTTPException(status_code=200, detail='Друг успешно удален')
    else:
        raise HTTPException(status_code=400, detail='Невалидные данные')
