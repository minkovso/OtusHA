import os
import jwt
import json
import sys
import psycopg

def generate_data(n: int) -> None:
    conn = psycopg.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    select_friends = '''
       SELECT user_id, friend_id
       FROM prod.friends
       LIMIT %s
    '''
    with conn, conn.cursor() as cur:
        cur.execute(select_friends, (n, ))
        rows = cur.fetchall()
    cases = []
    for user_id, friend_id in rows:
        token = jwt.encode({'user_id': user_id}, os.getenv('SECRET_KEY'), algorithm='HS256')
        case = {'token': token, 'friend_id': friend_id}
        cases.append(case)
    print(json.dumps(cases))

if __name__ == '__main__':
    generate_data(int(sys.argv[1]))
