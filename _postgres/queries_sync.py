import json
import psycopg2
import random


INSERT_PREFIX = "insert_test__"


def connect(ctx):
    conn = psycopg2.connect(
        user="postgres_bench",
        dbname="postgres_bench",
        password="edgedbbenchmark",
        host=ctx.db_host,
        port=ctx.pg_port,
    )
    conn.autocommit = True
    return conn


def close(ctx, conn):
    conn.close()


def load_ids(ctx, conn):
    cur = conn.cursor()

    cur.execute(f'SELECT id FROM "User" ORDER BY random() LIMIT {ctx.number_of_ids}')
    users = cur.fetchall()

    cur.execute(
        f'SELECT id FROM "Question" ORDER BY random() LIMIT {ctx.number_of_ids}'
    )
    questions = cur.fetchall()

    cur.execute(f'SELECT id FROM "Answer" ORDER BY random() LIMIT {ctx.number_of_ids}')
    answers = cur.fetchall()

    cur.execute(f'SELECT id FROM "Comment" ORDER BY random() LIMIT {ctx.number_of_ids}')
    comments = cur.fetchall()

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


def get_answer(conn, id):
    with conn.cursor() as cur:
        cur.execute(
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

        rows = cur.fetchall()

    return json.dumps(
        {
            "content": rows[0][0],
            "upvote": rows[0][1],
            "downvote": rows[0][2],
            "is_accepted": rows[0][3],
            "author_email": rows[0][4],
            "author_username": rows[0][5],
            "comments": [row[6] for row in rows],
            "comments_upvotes": [row[7] for row in rows],
            "comments_downvotes": [row[8] for row in rows],
            "comment_author_id": [row[9] for row in rows],
        }
    )


def get_comments_on_question(conn, id):
    with conn.cursor() as cur:
        cur.execute(
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

        rows = cur.fetchall()

    return json.dumps(
        {
            "comments": [row[0] for row in rows],
            "upvotes": [row[1] for row in rows],
            "downvotes": [row[2] for row in rows],
            "author_ids": [row[3] for row in rows],
            "author_emails": [row[4] for row in rows],
            "author_usernames": [row[5] for row in rows],
        }
    )


def insert_user(conn, val):
    num = random.randrange(10, 100)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO "User" (age, email, first_name, last_name, username, hashed_password)
            VALUES ({num}, '{val}{num}@test.com', '{val}{num+1}', '{val}{num+2}', '{val}{num+3}', '{val}{num+4}')
            RETURNING id, username, email, age, first_name, last_name
        """
        )

        rows = cur.fetchall()

    return json.dumps(
        {
            "id": rows[0][0],
            "username": rows[0][1],
            "email": rows[0][2],
            "first_name": rows[0][3],
            "last_name": rows[0][4],
        }
    )


def update_comments_on_answer(conn, val):
    num = random.randrange(10_000)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO "Comment" (upvote, downvote, content, author_id, answer_id)
            VALUES ({num}, {num // 10}, '{val['prefix']}{num}', {random.choice(val["author_id"])}, {random.choice(val["answer_id"])})
            RETURNING id, upvote, downvote, content, author_id, answer_id
        """
        )

        rows = cur.fetchall()

    return json.dumps(
        {
            "id": rows[0][0],
            "upvote": rows[0][1],
            "downvote": rows[0][2],
            "content": rows[0][3],
            "author_id": rows[0][4],
            "answer_id": rows[0][5],
        }
    )


def cleanup(ctx, conn, queryname):
    if queryname == "insert_user":
        cur = conn.cursor()
        cur.execute(
            f"""
            DELETE FROM "User"
            WHERE username LIKE '{INSERT_PREFIX}%'
        """
        )
        conn.commit()
    elif queryname == "update_comments_on_answer":
        cur = conn.cursor()
        cur.execute(
            f"""
            DELETE FROM "Comment"
            WHERE content LIKE '{INSERT_PREFIX}%'
        """
        )
        conn.commit()
