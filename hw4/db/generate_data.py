import sys
import faker
import uuid
from random import randint
import psycopg
import os

fake = faker.Faker()

def generate_users(n: int) -> None:
    for _ in range(n):
        user_id = str(uuid.uuid4())
        first_name = fake.first_name()
        second_name = fake.last_name()
        birthdate = fake.date()
        city = fake.city()
        biography = fake.sentence(10)
        print(f'{user_id},{first_name},{second_name},{birthdate},{city},{biography}', end='\n')

def generate_fiends(n: int) -> None:
    conn = psycopg.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    select_users = '''
        SELECT user_id
          FROM prod.users
    '''
    with conn, conn.cursor() as cur:
        cur.execute(select_users)
        rows = cur.fetchall()
    user_ids = [user_id for user_id, in rows]
    friends = set()
    for _ in range(n):
        while True:
            user_id = user_ids[randint(0, len(user_ids) - 1)]
            friend_id = user_ids[randint(0, len(user_ids) - 1)]
            if (user_id, friend_id) not in friends:
                break
        friends.add((user_id, friend_id))
        print(f'{user_id},{friend_id}', end='\n')

def generate_posts(n: int) -> None:
    conn = psycopg.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    select_users = '''
       SELECT user_id
       FROM prod.users
    '''
    with conn, conn.cursor() as cur:
        cur.execute(select_users)
        rows = cur.fetchall()
    user_ids = [user_id for user_id, in rows]
    for _ in range(n):
        post_id = str(uuid.uuid4())
        user_id = user_ids[randint(0, len(user_ids) - 1)]
        text = fake.sentence(100)
        updated_at = fake.date_time().replace(microsecond=0)
        print(f'{post_id},{user_id},{text},{updated_at}', end='\n')


if __name__ == '__main__':
    if sys.argv[1] == 'users':
        generate_users(int(sys.argv[2]))
    elif sys.argv[1] == 'friends':
        generate_fiends(int(sys.argv[2]))
    elif sys.argv[1] == 'posts':
        generate_posts(int(sys.argv[2]))
    else:
        raise ValueError(f'Неверный генератор данных {sys.argv[1]}')
