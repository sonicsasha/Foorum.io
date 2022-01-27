CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    auth_level INTEGER
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    poster_id INTEGER REFERENCES users,
    message TEXT,
    sent_at TIMESTAMP,
    edited_at TIMESTAMP
);

CREATE TABLE threads (
    id SERIAL PRIMARY KEY,
    poster_id INTEGER REFERENCES users,
    topic_id INTEGER REFERENCES topics,
    thread_header TEXT,
    thread_desc TEXT,
    sent_at TIMESTAMP,
    edited_at TIMESTAMP
);

CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    topic_name TEXT UNIQUE,
    topic_desc TEXT,
    is_hidden BOOLEAN

);

CREATE TABLE topicsAccess (
    user_id INTEGER REFERENCES users,
    topic_id INTEGER REFERENCES topics
);
