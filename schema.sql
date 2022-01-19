CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT,
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
