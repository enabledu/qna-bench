#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import argparse
import sys
import types
import typing


from _edgedb import queries_sync as edgedb_queries_sync
from _edgedb import queries_async as edgedb_queries_async
from _postgres import queries_sync as postgres_queries_sync


class impl(typing.NamedTuple):
    language: str
    title: str
    module: typing.Optional[types.ModuleType]


IMPLEMENTATIONS = {
    "edgedb_py_sync": impl("python", "EdgeDB (Python, Sync)", edgedb_queries_sync),
    "edgedb_py_async": impl("python", "EdgeDB (Python, Async)", edgedb_queries_async),
    "postgres_py_sync": impl("python", "PostgreSQL (Python)", postgres_queries_sync)
}


class bench(typing.NamedTuple):
    title: str
    description: str


BENCHMARKS = {
    "get_answer": bench(
        title="GET /answer/:id",
        description=(
            "Get all information about a given answer: content, upvote, downvote, "
            "author, is_accepted and comments."
        ),
    ),
    "get_comments_on_question": bench(
        title="GET /comment/:question_id",
        description="Get all comments on a given question.",
    ),
    "insert_user": bench(title="POST /user", description="Insert a new user."),
    "update_comments_on_answer": bench(
        title="PATCH /answer/:id",
        description="Update the comments on a given answer (add a new comment to exisiting comments).",
    ),
}


def parse_args(*, prog_desc: str, out_to_json: bool = False, out_to_html: bool = False):
    parser = argparse.ArgumentParser(
        description=prog_desc, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-C",
        "--concurrency",
        type=int,
        default=1,
        help="number of concurrent connections",
    )

    parser.add_argument(
        "--async-split",
        type=int,
        default=1,
        help="number of processes to split Python async connections",
    )

    parser.add_argument(
        "--db-host", type=str, default="127.0.0.1", help="host with databases"
    )

    parser.add_argument(
        "-D", "--duration", type=int, default=30, help="duration of test in seconds"
    )
    parser.add_argument(
        "--timeout", default=2, type=int, help="server timeout in seconds"
    )
    parser.add_argument(
        "--warmup-time",
        type=int,
        default=5,
        help="duration of warmup period for each benchmark in seconds",
    )
    parser.add_argument(
        "--net-latency",
        default=0,
        type=int,
        help="assumed p0 roundtrip latency between a database and a client",
    )
    parser.add_argument(
        "--pg-port", type=int, default=3500, help="PostgreSQL server port"
    )

    parser.add_argument(
        "--edgedb-port", type=int, default=None, help="EdgeDB server port"
    )

    parser.add_argument(
        "--mongodb-port", type=int, default=27017, help="MongoDB server port"
    )

    parser.add_argument(
        "--number-of-ids",
        type=int,
        default=250,
        help="number of random IDs to fetch data with in benchmarks",
    )

    parser.add_argument(
        "--query",
        dest="queries",
        action="append",
        help="queries to benchmark",
        choices=list(BENCHMARKS.keys()) + ["all"],
    )

    parser.add_argument(
        "benchmarks",
        nargs="+",
        help="benchmarks names",
        choices=list(IMPLEMENTATIONS.keys()) + ["all"],
    )

    if out_to_json:
        parser.add_argument(
            "--json",
            type=str,
            default="",
            help="filename to dump serialized results in JSON",
        )

    if out_to_html:
        parser.add_argument(
            "--html", type=str, default="", help="filename to dump HTML report"
        )

    args = parser.parse_args()
    argv = sys.argv[1:]

    if not args.queries:
        args.queries = list(BENCHMARKS.keys())

    if args.concurrency % args.async_split != 0:
        raise Exception(
            "'--concurrency' must be an integer multiple of '--async-split'"
        )

    if "all" in args.benchmarks:
        args.benchmarks = list(IMPLEMENTATIONS.keys())

    if out_to_json and args.json:
        i = argv.index("--json")
        del argv[i : i + 2]

    if out_to_html and args.html:
        i = argv.index("--html")
        del argv[i : i + 2]

    return args, argv
