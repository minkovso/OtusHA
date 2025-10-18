from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import psycopg
from datetime import date
from hashlib import sha256
import ulid

router = APIRouter()

def get_db_conn():
    conn = psycopg.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    return conn

class UserRegisterRequest(BaseModel):
    first_name: str
    second_name: str
    birthdate: date
    city: str
    biography: str
    password: str

class UserRegisterResponse(BaseModel):
    user_id: str

@router.post('/register', response_model=UserRegisterResponse)
def user_register(data: UserRegisterRequest):
    conn = get_db_conn()
    insert_user = '''
        INSERT INTO prod.users (user_id, first_name, second_name, birthdate, city, biography)
        VALUES (%s, %s, %s, %s, %s, %s)
    '''
    insert_password = '''
        INSERT INTO prod.passwords (user_id, password)
        VALUES (%s, %s)
    '''
    user_id = ulid.new()
    password = sha256(data.password.encode()).hexdigest()
    with conn, conn.cursor() as cur:
        cur.execute(insert_user, (user_id, data.first_name, data.second_name, data.birthdate, data.city, data.biography))
        cur.execute(insert_password, (user_id, password))
        conn.commit()
    return UserRegisterResponse(user_id=user_id)

class UserGetResponse(BaseModel):
    user_id: str
    first_name: str
    second_name: str
    birthdate: date
    city: str
    biography: str

@router.get('/get/{user_id}', response_model=UserGetResponse)
def user_get(user_id: str):
    conn = get_db_conn()
    select_user = '''
        SELECT user_id, first_name, second_name, birthdate, city, biography 
          FROM prod.users 
         WHERE user_id = %s
    '''
    with conn, conn.cursor() as cur:
        cur.execute(select_user, (user_id, ))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Анкета не найдена')
    else:
        user_id, first_name, second_name, birthdate, city, biography = row
        return UserGetResponse(
            user_id=user_id,
            first_name=first_name,
            second_name=second_name,
            birthdate=birthdate,
            city=city,
            biography=biography
        )

class UserSearchResponse(BaseModel):
    user_id: str
    first_name: str
    second_name: str
    birthdate: date
    city: str
    biography: str

@router.get('/search', response_model=list[UserSearchResponse])
def user_search(first_name: str, second_name: str):
    conn = get_db_conn()
    first_name += '%'
    second_name += '%'
    select_users = '''
        SELECT user_id, first_name, second_name, birthdate, city, biography 
          FROM prod.users 
         WHERE first_name like %s AND second_name like %s
    '''
    with conn, conn.cursor() as cur:
        cur.execute(select_users, (first_name, second_name))
        rows = cur.fetchall()
    return [UserSearchResponse(
        user_id=user_id,
        first_name=first_name,
        second_name=second_name,
        birthdate=birthdate,
        city=city,
        biography=biography
    ) for user_id, first_name, second_name, birthdate, city, biography in rows]
