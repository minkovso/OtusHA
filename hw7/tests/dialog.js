import http from "k6/http";
import { sleep } from "k6";
import { SharedArray } from 'k6/data';

const dialogs = new SharedArray('dialogs', () => JSON.parse(open('dialog.data')));

export const options = {
  vus: Number(__ENV.VUS) || 10,
  duration: __ENV.DURATION || '30s',
};

export default function () {

  const dialog = dialogs[Math.floor(Math.random() * dialogs.length)];

  const url = `http://host.docker.internal:8000/dialog/${dialog.friend_id}/list`;

  const params = {
    headers: {
      Authorization: `Bearer ${dialog.token}`,
      'Content-Type': 'application/json',
    },
  };

  http.get(url, params);

  sleep(1);
}