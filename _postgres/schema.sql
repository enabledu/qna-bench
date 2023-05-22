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
CREATE INDEX idx_question_author_id ON "Question" (author_id);


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
CREATE INDEX idx_answer_author_id ON "Answer" (author_id);
CREATE INDEX idx_answer_question_id ON "Answer" (question_id);

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
CREATE INDEX idx_comment_author_id ON "Comment" (author_id);
CREATE INDEX idx_comment_question_id ON "Comment" (question_id);
CREATE INDEX idx_comment_answer_id ON "Comment" (answer_id);
