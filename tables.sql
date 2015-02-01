CREATE TABLE users (
    user_id bigserial PRIMARY KEY,
    username varchar(20),
    password varchar(250),
    email varchar(50),
    joined timestamp DEFAULT statement_timestamp(),
    active timestamp DEFAULT statement_timestamp(),
    admin boolean
);

CREATE TABLE reviews (
    review_id bigserial PRIMARY KEY,
    reviewer bigint,
    reviewee bigint,
    stars numeric,
    reviewtime timestamp DEFAULT statement_timestamp(),
    comments text
);

CREATE TABLE reports (
    report_id bigserial PRIMARY KEY,
    user_id bigint,
    report text,
    reporttime timestamp DEFAULT statement_timestamp()
);
