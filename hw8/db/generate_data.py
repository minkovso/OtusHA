import sys
import faker
from random import randint
import psycopg
import os
import ulid
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator

fake = faker.Faker()

def generate_users(n: int) -> None:
    for _ in range(n):
        user_id = ulid.new()
        first_name = fake.first_name()
        second_name = fake.last_name()
        birthdate = fake.date()
        city = fake.city()
        biography = fake.sentence(10)
        print(f'{user_id},{first_name},{second_name},{birthdate},{city},{biography}', end='\n')

def generate_friends(n: int) -> None:
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
        post_id = ulid.new()
        user_id = user_ids[randint(0, len(user_ids) - 1)]
        text = fake.sentence(100)
        updated_at = fake.date_time().replace(microsecond=0)
        print(f'{post_id},{user_id},{text},{updated_at}', end='\n')

def generate_dialogs(n: int) -> None:
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
    cluster = Cluster(
        os.getenv('COUCH_HOST'),
        ClusterOptions(PasswordAuthenticator(os.getenv('COUCH_USER'), os.getenv('COUCH_PASSWORD')))
    )
    bucket = cluster.bucket(os.getenv('COUCH_BUCKET'))
    scope = bucket.scope('prod')
    coll = scope.collection('messages')
    for _ in range(n):
        user_id = user_ids[randint(0, len(user_ids) - 1)]
        friend_id = user_ids[randint(0, len(user_ids) - 1)]
        text = fake.sentence(nb_words=100)
        created_at = fake.date_time()
        message_id = ulid.from_timestamp(created_at.timestamp())
        dialog_id = f'{min((friend_id, user_id))}_{max((friend_id, user_id))}'
        doc_id = f'{dialog_id}:{message_id}'
        doc = {
            'from': user_id,
            'to': friend_id,
            'text': text,
            'created_at': created_at.replace(tzinfo=None, microsecond=0).isoformat()
        }
        coll.insert(doc_id, doc)


if __name__ == '__main__':
    if sys.argv[1] == 'users':
        generate_users(int(sys.argv[2]))
    elif sys.argv[1] == 'friends':
        generate_friends(int(sys.argv[2]))
    elif sys.argv[1] == 'posts':
        generate_posts(int(sys.argv[2]))
    elif sys.argv[1] == 'dialogs':
        generate_dialogs(int(sys.argv[2]))
    else:
        raise ValueError(f'Неверный генератор данных {sys.argv[1]}')
