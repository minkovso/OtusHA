import psycopg
import os
import redis
import sys
import json

def get_db_conn():
    conn = psycopg.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    return conn

def generate_posts() -> None:
    conn = get_db_conn()
    select_posts = '''
        SELECT post_id, user_id, text
          FROM prod.posts
         ORDER BY updated_at DESC LIMIT 1000
    '''
    with conn, conn.cursor() as cur:
        cur.execute(select_posts)
        rows = cur.fetchall()
    for post_id, user_id, text in rows:
        element = json.dumps([user_id, text]).replace('"', '\\"')
        print(f'SET posts:{post_id} "{element}"', end='\n')
        print(f'EXPIRE posts:{post_id} 3600', end='\n')

def generate_users() -> None:
    conn = get_db_conn()
    select_posts = '''
        SELECT post_id, user_id, CAST(EXTRACT(EPOCH FROM updated_at) AS BIGINT)
          FROM prod.posts
    '''
    with conn, conn.cursor() as cur:
        cur.execute(select_posts)
        rows = cur.fetchall()
    users = {}
    for post_id, user_id, updated_at in rows:
        users.setdefault(user_id, []).append(f'{updated_at} "{post_id}"')
    for k, v in users.items():
        elements = ' '.join(v[:1000])
        print(f'ZADD users:{k} {elements}', end='\n')

def generate_feeds() -> None:
    conn = get_db_conn()
    r = redis.Redis(host=os.getenv('REDIS_HOST'), port=int(os.getenv('REDIS_PORT')), decode_responses=True)
    select_friends = '''
        SELECT user_id, array_agg(friend_id)
          FROM prod.friends
         GROUP BY user_id
    '''
    with conn, conn.cursor() as cur:
        cur.execute(select_friends)
        rows = cur.fetchall()
    for user_id, friend_ids in rows:
        feed = []
        for friend_id in friend_ids:
            posts = r.zrange(f'users:{friend_id}', 0, -1, withscores=True)
            for post in posts:
                feed.append(post)
        if feed:
            feed.sort(key=lambda post: post[1], reverse=True)
            elements = ' '.join([f'{updated_at} "{post_id}"' for post_id, updated_at in feed[:1000]])
            print(f'ZADD feeds:{user_id} {elements}', end='\n')

if __name__ == '__main__':
    if sys.argv[1] == 'users':
        generate_users()
    elif sys.argv[1] == 'feeds':
        generate_feeds()
    elif sys.argv[1] == 'posts':
        generate_posts()
    else:
        raise ValueError(f'Неверный генератор данных {sys.argv[1]}')
