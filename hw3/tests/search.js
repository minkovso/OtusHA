import http from "k6/http";
import { sleep } from "k6";
import { SharedArray } from 'k6/data';

const names = new SharedArray('names', () => JSON.parse(open('search.data')));

export const options = {
  vus: Number(__ENV.VUS) || 10,
  duration: __ENV.DURATION || '30s',
};

export default function () {

  const name = names[Math.floor(Math.random() * names.length)];

  const url = `http://host.docker.internal:8000/user/search?first_name=${name.first_name}&second_name=${name.second_name}`;

  http.get(url);

  sleep(1);
}