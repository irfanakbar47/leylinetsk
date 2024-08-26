CREATE TABLE IF NOT EXISTS query_log (
    id SERIAL PRIMARY KEY,
    domain VARCHAR NOT NULL,
    ip_address VARCHAR NOT NULL,
    query_time TIMESTAMPTZ NOT NULL
);
