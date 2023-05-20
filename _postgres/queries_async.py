import asyncpg
import json
import random


ASYNC = True
INSERT_PREFIX = "insert_test__"


async def connect(ctx):
    return await asyncpg.connect(
        user="postgres_bench",
        database="postgres_bench",
        password="edgedbbenchmark",
        host=ctx.db_host,
        port=ctx.pg_port,
    )


async def close(ctx, conn):
    await conn.close()


async def load_ids(ctx, conn):
    users = await conn.fetch(
        f'SELECT id FROM "User" ORDER BY random() LIMIT {ctx.number_of_ids}'
    )

    questions = await conn.fetch(
        f'SELECT id FROM "Question" ORDER BY random() LIMIT {ctx.number_of_ids}'
    )

    answers = await conn.fetch(
        f'SELECT id FROM "Answer" ORDER BY random() LIMIT {ctx.number_of_ids}'
    )

    comments = await conn.fetch(
        f'SELECT id FROM "Comment" ORDER BY random() LIMIT {ctx.number_of_ids}'
    )

    return dict(
        get_answer=[a[0] for a in answers],
        get_comments_on_question=[q[0] for q in questions],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[INSERT_PREFIX] * ctx.concurrency,
        update_comments_on_answer=[
            {
                "prefix": INSERT_PREFIX,
                "answer_id": [a[0] for a in answers],
                "author_id": [u[0] for u in users],
            }
        ]
        * ctx.concurrency,
    )


async def get_answer(conn, id):
    rows = await conn.fetch(
        f"""
        SELECT
            a.content,
            a.upvote,
            a.downvote,
            a.is_accepted,
            u.email AS author_email,
            u.username AS author_username,
            c.content AS comment_content,
            c.upvote AS comment_upvote,
            c.downvote AS comment_downvote,
            c.author_id AS comment_author_id
        FROM
            "Answer" AS a
            INNER JOIN "User" AS u ON a.author_id = u.id
            LEFT JOIN "Comment" AS c ON a.id = c.answer_id
        WHERE
            a.id = {id}
    """
    )

    return json.dumps(
        {
            "content": rows[0]["content"],
            "upvote": rows[0]["upvote"],
            "downvote": rows[0]["downvote"],
            "is_accepted": rows[0]["is_accepted"],
            "author_email": rows[0]["author_email"],
            "author_username": rows[0]["author_username"],
            "comments": [row["comment_content"] for row in rows],
            "comments_upvotes": [row["comment_upvote"] for row in rows],
            "comments_downvotes": [row["comment_downvote"] for row in rows],
            "comment_author_id": [row["comment_author_id"] for row in rows],
        }
    )


async def get_comments_on_question(conn, id):
    rows = await conn.fetch(
        f"""
            WITH comments_ids AS (
                SELECT c.id
                FROM "Comment" AS c
                INNER JOIN "Question" AS q ON q.id = c.question_id
                WHERE q.id = {id}
            )
            SELECT
                c.content,
                c.upvote,
                c.downvote,
                u.id AS author_id,
                u.email AS author_email,
                u.username AS author_username
            FROM
                "Comment" AS c
                INNER JOIN "User" AS u ON c.author_id = u.id
            WHERE
                c.id IN (SELECT id FROM comments_ids)
        """
    )

    return json.dumps(
        {
            "comments": [row["content"] for row in rows],
            "upvotes": [row["upvote"] for row in rows],
            "downvotes": [row["downvote"] for row in rows],
            "author_ids": [row["author_id"] for row in rows],
            "author_emails": [row["author_email"] for row in rows],
            "author_usernames": [row["author_username"] for row in rows],
        }
    )


async def insert_user(conn, val):
    num = random.randrange(10, 100)
    rows = await conn.fetch(
        f"""
            INSERT INTO "User" (age, email, first_name, last_name, username, hashed_password)
            VALUES ({num}, '{val}{num}@test.com', '{val}{num+1}', '{val}{num+2}', '{val}{num+3}', '{val}{num+4}')
            RETURNING id, username, email, age, first_name, last_name
        """
    )

    return json.dumps(
        {
            "id": rows[0]["id"],
            "username": rows[0]["username"],
            "email": rows[0]["email"],
            "first_name": rows[0]["first_name"],
            "last_name": rows[0]["last_name"],
        }
    )


async def update_comments_on_answer(conn, val):
    num = random.randrange(10_000)
    rows = await conn.fetch(
        f"""
            INSERT INTO "Comment" (upvote, downvote, content, author_id, answer_id)
            VALUES ({num}, {num // 10}, '{val['prefix']}{num}', {random.choice(val["author_id"])}, {random.choice(val["answer_id"])})
            RETURNING id, upvote, downvote, content, author_id, answer_id
        """
    )

    return json.dumps(
        {
            "id": rows[0]["id"],
            "upvote": rows[0]["upvote"],
            "downvote": rows[0]["downvote"],
            "content": rows[0]["content"],
            "author_id": rows[0]["author_id"],
            "answer_id": rows[0]["answer_id"],
        }
    )


async def cleanup(ctx, conn, queryname):
    if queryname == "insert_user":
        await conn.fetch(
            f"""
            DELETE FROM "User"
            WHERE username LIKE '{INSERT_PREFIX}%'
        """
        )
    elif queryname == "update_comments_in_answer":
        await conn.fetch(
            f"""
            DELETE FROM "Comment"
            WHERE content LIKE '{INSERT_PREFIX}%'
        """
        )
