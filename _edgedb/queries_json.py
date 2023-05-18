#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import edgedb
import random

from . import queries


INSERT_PREFIX = 'insert_test__'


def connect(ctx):
    return edgedb.create_client().with_retry_options(
        edgedb.RetryOptions(attempts=10),
    )


def close(ctx, conn):
    conn.close()


def load_ids(ctx, conn):
    d = conn.query_single('''
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
    ''', limit=ctx.number_of_ids)

    return dict(
        get_user=list(d.users),
        get_comment=list(d.comments),
        get_answer=list(d.answers),
        get_question=list(d.questions)
    )

def get_answer(conn, id):
    return conn.query_single_json(queries.GET_ANSWER, id=id)


def setup(ctx, conn, queryname):
    ...


def cleanup(ctx, conn, queryname):
    ...
