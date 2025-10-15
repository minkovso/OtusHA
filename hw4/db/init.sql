CREATE SCHEMA IF NOT EXISTS prod;

CREATE TABLE IF NOT EXISTS prod.users (
  user_id VARCHAR PRIMARY KEY,
  first_name VARCHAR NOT NULL,
  second_name VARCHAR NOT NULL,
  birthdate DATE NOT NULL,
  city VARCHAR NOT NULL,
  biography VARCHAR NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS users_first_second_idx
    ON prod.users (first_name text_pattern_ops, second_name text_pattern_ops);

CREATE TABLE IF NOT EXISTS prod.passwords (
  user_id VARCHAR PRIMARY KEY,
  password VARCHAR NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prod.friends (
  user_id VARCHAR REFERENCES prod.users(user_id),
  friend_id VARCHAR REFERENCES prod.users(user_id),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (friend_id, user_id)
);

CREATE TABLE IF NOT EXISTS prod.posts (
  post_id VARCHAR PRIMARY KEY,
  user_id VARCHAR REFERENCES prod.users(user_id),
  text VARCHAR NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);