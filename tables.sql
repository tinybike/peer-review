DROP TABLE IF EXISTS users;
CREATE TABLE users (
    user_id bigserial PRIMARY KEY,
    username varchar(20),
    password varchar(250),
    email varchar(50),
    joined timestamp DEFAULT statement_timestamp(),
    active timestamp DEFAULT statement_timestamp(),
    admin boolean
);

DROP TABLE IF EXISTS reviews;
CREATE TABLE reviews (
    review_id bigserial PRIMARY KEY,
    reviewer varchar(20),
    reviewee varchar(20),
    rating numeric,
    reviewtime timestamp DEFAULT statement_timestamp(),
    comments text
);

DROP TABLE IF EXISTS reports;
CREATE TABLE reports (
    report_id bigserial PRIMARY KEY,
    user_id bigint,
    username varchar(20),
    report text,
    reporttime timestamp DEFAULT statement_timestamp()
);
