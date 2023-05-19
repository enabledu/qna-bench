import argparse
import asyncio
import json
import random

import edgedb
import progress.bar
import uvloop


async def import_data(data: dict):
    client = edgedb.create_async_client(max_concurrency=32)
    batch_size = 1000

    users = data["users"]
    questions = data["questions"]
    answers = data["answers"]
    comments = data["comments"]

    id2username_map = {user["id"]: user["username"] for user in users}
    id2comment_map = {comment["id"]: comment["content"] for comment in comments}
    id2answer_map = {answer["id"]: answer["content"] for answer in answers}

    # region Load users
    users_data = [
        dict(
            _id=u["id"],
            age=u["age"],
            email=u["email"],
            first_name=u["first_name"],
            last_name=u["last_name"],
            username=u["username"],
            is_active=u["is_active"],
            is_superuser=u["is_superuser"],
            is_verified=u["is_verified"],
            hashed_password=u["hashed_password"],
        )
        for u in users
    ]

    users_insert_query = r"""
        WITH users := <json>$users
        FOR user in json_array_unpack(users) UNION (
            INSERT User {
                age := <Age>user["age"],
                email := <str>user["email"],
                first_name := <str>user["first_name"],
                last_name := <str>user["last_name"],
                username := <str>user["username"],
                is_active := <bool>user["is_active"],
                is_superuser := <bool>user["is_superuser"],
                is_verified := <bool>user["is_verified"],
                hashed_password := <str>user["hashed_password"],
            }
        );
    """

    start = 0
    users_bar = progress.bar.Bar("Users", max=len(users))
    users_slice = users_data[start : start + batch_size]
    while len(users_slice):
        users_bar.goto(start)
        await client.query(users_insert_query, users=json.dumps(users_slice))
        start += batch_size
        users_slice = users_data[start : start + batch_size]
    users_bar.goto(users_bar.max)
    users_bar.finish()

    # Get all users id's
    user_ids = await client.query_json("SELECT User")
    user_ids = json.loads(user_ids)

    # endregion

    # region Load comments
    comments_data = [
        dict(
            _id=c["id"],
            upvote=c["upvote"],
            downvote=c["downvote"],
            content=c["content"],
            author=user_ids[c["author"]]["id"],
        )
        for c in comments
    ]

    comments_insert_query = r"""
    WITH comments := <json>$comments
    FOR comment in json_array_unpack(comments) UNION (
        INSERT Comment {
            upvote := <int16>comment["upvote"],
            downvote := <int16>comment["downvote"],
            content := <str>comment["content"],
            author := (SELECT User FILTER .id = <uuid>comment["author"])
        }
    );
    """

    start = 0
    comments_bar = progress.bar.Bar("Comments", max=len(comments))
    comments_slice = comments_data[start : start + batch_size]
    while len(comments_slice):
        comments_bar.goto(start)
        await client.query(comments_insert_query, comments=json.dumps(comments_slice))
        start += batch_size
        comments_slice = comments_data[start : start + batch_size]
    comments_bar.goto(comments_bar.max)
    comments_bar.finish()

    # Get all comments id's
    comment_ids = await client.query_json("SELECT Comment")
    comment_ids = json.loads(comment_ids)
    # endregion

    # region Load answer
    random.shuffle(user_ids)

    answers_data = [
        dict(
            _id=a["id"],
            upvote=a["upvote"],
            downvote=a["downvote"],
            content=a["content"],
            is_accepted=a["is_accepted"],
            author=user_ids[a["author"]]["id"],
            comments=[comment_ids[comment]["id"] for comment in a["comments"]],
        )
        for a in answers
    ]

    answers_insert_query = r"""
    WITH answers := <json>$answers
    FOR answer IN json_array_unpack(answers) UNION (
        INSERT Answer {
            upvote := <int16>answer["upvote"],
            downvote := <int16>answer["downvote"],
            content := <str>answer["content"],
            author := (SELECT User FILTER .id = <uuid>answer["author"]),
            comments := (
                FOR x IN {
                    enumerate(array_unpack(<array<uuid>>answer["comments"]))
                } UNION (
                    SELECT Comment FILTER .id = x.1
                )
            )
        }
    );
    """

    start = 0
    answers_bar = progress.bar.Bar("Answers", max=len(answers))
    answers_slice = answers_data[start : start + batch_size]
    while len(answers_slice):
        answers_bar.goto(start)
        await client.query(answers_insert_query, answers=json.dumps(answers_slice))
        start += batch_size
        answers_slice = answers_data[start : start + batch_size]
    answers_bar.goto(answers_bar.max)
    answers_bar.finish()

    # Get all answers id's
    answer_ids = await client.query_json("SELECT Answer")
    answer_ids = json.loads(answer_ids)
    # endregion

    # region Load questions
    random.shuffle(user_ids)
    random.shuffle(comment_ids)

    questions_data = [
        dict(
            _id=q["id"],
            upvote=q["upvote"],
            downvote=q["downvote"],
            content=q["content"],
            tags=q["tags"],
            title=q["title"],
            author=user_ids[q["author"]]["id"],
            comments=[comment_ids[comment]["id"] for comment in q["comments"]],
            answers=[answer_ids[answer]["id"] for answer in q["answers"]],
        )
        for q in questions
    ]

    questions_insert_query = r"""
    WITH questions := <json>$questions
    FOR question in json_array_unpack(questions) UNION (
        INSERT Question {
            upvote := <int16>question["upvote"],
            downvote := <int16>question["downvote"],
            content := <str>question["content"],
            tags := <array<str>>question["tags"],
            title := <str>question["title"],
            author := (SELECT User FILTER .id = <uuid>question["author"]),
            comments := (
                FOR x IN {
                    enumerate(array_unpack(<array<uuid>>question["comments"]))
                } UNION (
                    SELECT Comment FILTER .id = x.1
                )
            ),
            answers := (
                FOR x IN {
                    enumerate(array_unpack(<array<uuid>>question["answers"]))
                } UNION (
                    SELECT Answer FILTER .id = x.1
                )
            )
        }
    );
    """

    start = 0
    questions_bar = progress.bar.Bar("Questions", max=len(questions))
    questions_slice = questions_data[start : start + batch_size]
    while len(questions_slice):
        questions_bar.goto(start)
        await client.query(
            questions_insert_query, questions=json.dumps(questions_slice)
        )
        start += batch_size
        questions_slice = questions_data[start : start + batch_size]
    questions_bar.goto(questions_bar.max)
    questions_bar.finish()
    # endregion


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str, help="The EdgeDB JSON dataset file")
    args = parser.parse_args()

    with open(args.filename) as f:
        data = json.load(f)

    uvloop.install()
    asyncio.run(import_data(data))
