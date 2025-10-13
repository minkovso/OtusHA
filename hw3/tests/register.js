import http from 'k6/http';
import { SharedArray } from 'k6/data';
import { sleep } from 'k6';

const users = new SharedArray('users', () => JSON.parse(open('register.data')));

export const options = {
  vus: Number(__ENV.VUS) || 10,
  duration: __ENV.DURATION || '30s',
};

export default function () {

  const user = users[Math.floor(Math.random() * users.length)];

  http.post('http://host.docker.internal:8000/user/register', JSON.stringify(user), {
    headers: { 'Content-Type': 'application/json' },
  });

  sleep(1);
}