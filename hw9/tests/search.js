import http from "k6/http";
import { sleep } from "k6";
import { SharedArray } from 'k6/data';

const tests = new SharedArray('tests', () => JSON.parse(open('search.data')));

export const options = {
  vus: Number(__ENV.VUS) || 10,
  duration: __ENV.DURATION || '120s',
};

export default function () {

  const test = tests[Math.floor(Math.random() * tests.length)];

  const url = `http://host.docker.internal:80/user/search?first_name=${test.first_name}&second_name=${test.second_name}`;

  http.get(url);

  sleep(1);
}