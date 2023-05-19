import edgedb
import random
import threading

from . import queries

ASYNC = True
INSERT_PREFIX = 'insert_test__'
thread_data = threading.local()


async def connect(ctx):
    client = getattr(thread_data, 'client', None)
    if client is None:
        client = (
            edgedb.create_async_client(max_concurrency=ctx.concurrency)
            .with_retry_options(
                edgedb.RetryOptions(attempts=10)
            )
        )

    return client


async def close(ctx, conn):
    # Don't bother closing individual pool connections, they'll be
    # closed automatically.
    pass


async def load_ids(ctx, conn):
    d = await conn.query_single(
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


async def get_answer(conn, id):
    return await conn.query_single_json(queries.GET_ANSWER, id=id)


async def get_comments_on_question(conn, id):
    return await conn.query_json(queries.GET_COMMENTS_ON_QUESTION, id=id)


async def insert_user(conn, val):
    num = random.randrange(10, 100)
    return await conn.query_single_json(
        queries.INSERT_USER,
        age=num,
        email=f"{val}{num}@test.com",
        fname=f"{val}{num+1}",
        lname=f"{val}{num+2}",
        username=f"{val}{num+3}",
        hashed_password=f"{val}{num+4}",
    )


async def update_comments_on_answer(conn, val):
    num = random.randrange(10_000)
    return await conn.query_single_json(
        queries.UPDATE_COMMENTS_ON_ANSWER,
        answer_id=random.choice(val["answer_id"]),
        author_id=random.choice(val["author_id"]),
        upvote=num,
        downvote=num // 10,
        content=f"{val['prefix']}{num}",
    )


async def cleanup(ctx, conn, queryname):
    if queryname == "insert_user":
        # Delete the inserted user data
        await conn.query("""
            DELETE User
            FILTER .username LIKE <str>$prefix
        """, prefix=f"{INSERT_PREFIX}%")
    elif queryname == "update_comments_on_answer":
        # Delete the inserted comment
        await conn.query("""
            UPDATE Answer FILTER .comments.content LIKE <str>$prefix
            SET {
                comments -= (SELECT Comment FILTER .content LIKE <str>$prefix)
            }
        """, prefix=f"{INSERT_PREFIX}%")

        await conn.query("""
            DELETE Comment FILTER .content LIKE <str>$prefix
        """, prefix=f"{INSERT_PREFIX}%")
