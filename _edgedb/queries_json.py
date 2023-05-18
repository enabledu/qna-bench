#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import edgedb
import random

from . import queries


INSERT_PREFIX = "insert_test__"


def connect(ctx):
    return edgedb.create_client().with_retry_options(
        edgedb.RetryOptions(attempts=10),
    )


def close(ctx, conn):
    conn.close()


def load_ids(ctx, conn):
    d = conn.query_single(
        """
        WITH
            U := User {id, r := random()},
            C := Comment {id, r := random()},
            A := Answer {id, r := random()},
            Q := Question {id, r := random()}
        SELECT (
            users := array_agg((SELECT U ORDER BY U.r LIMIT <int64>$limit).id),
            comments := array_agg((SELECT C ORDER BY C.r LIMIT <int64>$limit).id),
            answers := array_agg((SELECT A ORDER BY A.r LIMIT <int64>$limit).id),
            questions := array_agg((SELECT Q ORDER BY Q.r LIMIT <int64>$limit).id),
        );
    """,
        limit=ctx.number_of_ids,
    )

    return dict(
        get_answer=list(d.answers),
        get_comments_on_question=list(d.questions),
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[INSERT_PREFIX] * ctx.concurrency,
        update_comments_on_answer=[
            {
                "prefix": INSERT_PREFIX,
                "answer_id": list(d.answers),
                "author_id": list(d.users),
            }
        ] * ctx.concurrency,
    )


def get_answer(conn, id):
    return conn.query_single_json(queries.GET_ANSWER, id=id)


def get_comments_on_question(conn, id):
    return conn.query_json(queries.GET_COMMENTS_ON_QUESTION, id=id)


def insert_user(conn, val):
    num = random.randrange(10, 100)
    return conn.query_single_json(
        queries.INSERT_USER,
        age=num,
        email=f"{val}{num}@test.com",
        fname=f"{val}{num+1}",
        lname=f"{val}{num+2}",
        username=f"{val}{num+3}",
        hashed_password=f"{val}{num+4}",
    )


def update_comments_on_answer(conn, val):
    num = random.randrange(10_000)
    return conn.query_single_json(
        queries.UPDATE_COMMENTS_ON_ANSWER,
        answer_id=random.choice(val["answer_id"]),
        author_id=random.choice(val["author_id"]),
        upvote=num,
        downvote=num // 10,
        content=f"{val['prefix']}_{num}",
    )


def setup(ctx, conn, queryname):
    ...


def cleanup(ctx, conn, queryname):
    ...
