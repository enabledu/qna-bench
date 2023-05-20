CREATE TABLE "User"
(
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255)          NOT NULL,
    hashed_password VARCHAR(255)          NOT NULL,
    is_active       BOOLEAN DEFAULT true  NOT NULL,
    is_superuser    BOOLEAN DEFAULT false NOT NULL,
    is_verified     BOOLEAN DEFAULT false NOT NULL,
    first_name      VARCHAR(255)          NOT NULL,
    last_name       VARCHAR(255)          NOT NULL,
    username        VARCHAR(255)          NOT NULL,
    age             SMALLINT              NOT NULL CHECK (age >= 0 AND age <= 110)
);


CREATE TABLE "Question"
(
    id          SERIAL PRIMARY KEY,
    content     TEXT                   NOT NULL,
    upvote      SMALLINT DEFAULT 0     NOT NULL,
    downvote    SMALLINT DEFAULT 0     NOT NULL,
    author_id   INTEGER                NOT NULL REFERENCES "User" (id),
    title       VARCHAR(255)           NOT NULL,
    tags        VARCHAR(255)[],
    is_accepted BOOLEAN  DEFAULT false NOT NULL
);

CREATE TABLE "Answer"
(
    id          SERIAL PRIMARY KEY,
    content     TEXT                   NOT NULL,
    upvote      SMALLINT DEFAULT 0     NOT NULL,
    downvote    SMALLINT DEFAULT 0     NOT NULL,
    author_id   INTEGER                NOT NULL REFERENCES "User" (id),
    question_id INTEGER                NOT NULL REFERENCES "Question" (id),
    is_accepted BOOLEAN  DEFAULT false NOT NULL
);

CREATE TABLE "Comment"
(
    id          SERIAL PRIMARY KEY,
    content     TEXT               NOT NULL,
    upvote      SMALLINT DEFAULT 0 NOT NULL,
    downvote    SMALLINT DEFAULT 0 NOT NULL,
    author_id   INTEGER            NOT NULL REFERENCES "User" (id),
    question_id INTEGER REFERENCES "Question" (id),
    answer_id   INTEGER REFERENCES "Answer" (id)
);