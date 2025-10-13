from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import psycopg
from datetime import date
import uuid
from hashlib import sha256

router = APIRouter()

class RegisterRequest(BaseModel):
    first_name: str
    second_name: str
    birthdate: date
    city: str
    biography: str
    password: str

class RegisterResponse(BaseModel):
    id: str

@router.post('/register', response_model=RegisterResponse)
def register(data: RegisterRequest):
    conn = psycopg.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    insert_user = '''
        INSERT INTO prod.users (id, first_name, second_name, birthdate, city, biography)
        VALUES (%s, %s, %s, %s, %s, %s)
    '''
    insert_password = '''
        INSERT INTO prod.passwords (id, password)
        VALUES (%s, %s)
    '''
    id = str(uuid.uuid4())
    password = sha256(data.password.encode()).hexdigest()
    with conn, conn.cursor() as cur:
        cur.execute(insert_user, (id, data.first_name, data.second_name, data.birthdate, data.city, data.biography))
        cur.execute(insert_password, (id, password))
        conn.commit()
    return RegisterResponse(id=id)

class GetIdResponse(BaseModel):
    id: str
    first_name: str
    second_name: str
    birthdate: date
    city: str
    biography: str

@router.get('/get/{id}', response_model=GetIdResponse)
def get_id(id: str):
    conn = psycopg.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    select_user = '''
        SELECT first_name, second_name, birthdate, city, biography 
          FROM prod.users 
         WHERE id = %s
    '''
    with conn, conn.cursor() as cur:
        cur.execute(select_user, (id, ))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Анкета не найдена')
    else:
        first_name, second_name, birthdate, city, biography = row
        return GetIdResponse(
            id=id,
            first_name=first_name,
            second_name=second_name,
            birthdate=birthdate,
            city=city,
            biography=biography
        )
