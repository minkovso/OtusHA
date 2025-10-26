from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import psycopg
from hashlib import sha256
import jwt

router = APIRouter()

class LoginRequest(BaseModel):
    user_id: str
    password: str

class LoginResponse(BaseModel):
    token: str

@router.post('/login', response_model=LoginResponse)
def login(data: LoginRequest):
    conn = psycopg.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    select_password = '''
        SELECT password 
          FROM prod.passwords 
         WHERE user_id = %s
    '''
    with conn, conn.cursor() as cur:
        cur.execute(select_password, (data.user_id, ))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    else:
        password, = row
        if sha256(data.password.encode()).hexdigest() == password:
            return LoginResponse(token=jwt.encode({'user_id': data.user_id}, os.getenv('SECRET_KEY'), algorithm='HS256'))
        else:
            raise HTTPException(status_code=400, detail='Невалидные данные')
