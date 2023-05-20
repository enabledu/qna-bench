#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import argparse
import psycopg2
import json


def import_data(data):
    # Establish a connection to the PostgreSQL database
    users = data["users"]
    questions = data["questions"]
    answers = data["answers"]
    comments = data["comments"]

    conn = psycopg2.connect(
        host="localhost",
        port="3500",
        database="postgres_bench",
        user="postgres_bench",
        password="edgedbbenchmark",
    )

    cursor = conn.cursor()

    for user in users:
        id = user["id"]
        email = user["email"].replace("'", "''")
        hashed_password = user["hashed_password"].replace("'", "''")
        is_active = user["is_active"]
        is_superuser = user["is_superuser"]
        is_verified = user["is_verified"]
        first_name = user["first_name"].replace("'", "''")
        last_name = user["last_name"].replace("'", "''")
        username = user["username"].replace("'", "''")
        age = user["age"]

        insert_query = f"""
            INSERT INTO "User" (id, email, hashed_password, is_active, is_superuser, is_verified, first_name, last_name, username, age)
            VALUES ({id}, '{email}', '{hashed_password}', {is_active}, {is_superuser}, {is_verified}, '{first_name}', '{last_name}', '{username}', {age});
            """

        cursor.execute(insert_query)

    for question in questions:
        id = question["id"]
        content = question["content"].replace("'", "''")
        title = question["title"].replace("'", "''")
        upvote = question["upvote"]
        downvote = question["downvote"]
        author_id = question["author"]
        tags = "'{" + ",".join(question["tags"]) + "}'"

        insert_query = f"""
            INSERT INTO "Question" (id, content, title, upvote, downvote, author_id, tags)
            VALUES ({id}, '{content}', '{title}', {upvote}, {downvote}, {author_id}, {tags});
            """

        cursor.execute(insert_query)

    for answer in answers:
        id = answer["id"]
        content = answer["content"].replace("'", "''")
        upvote = answer["upvote"]
        downvote = answer["downvote"]
        author_id = answer["author"]
        question_id = answer["question"]
        is_accepted = answer["is_accepted"]

        insert_query = f"""
            INSERT INTO "Answer" (id, content, upvote, downvote, author_id, question_id, is_accepted)
            VALUES ({id}, '{content}', {upvote}, {downvote}, {author_id}, {question_id}, {is_accepted});
            """

        cursor.execute(insert_query)

    for comment in comments:
        id = comment["id"]
        content = comment["content"].replace("'", "''")
        upvote = comment["upvote"]
        downvote = comment["downvote"]
        author_id = comment["author"]
        question_id = comment["question"]
        answer_id = comment["answer"]

        insert_query = f"""
            INSERT INTO "Comment" (id, content, upvote, downvote, author_id, question_id, answer_id)
            VALUES ({id}, '{content}', {upvote}, {downvote}, {author_id}, {question_id}, {answer_id});
            """

        cursor.execute(insert_query)

    # Commit the changes to the database
    conn.commit()
    # Close the cursor and the database connection
    cursor.close()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load a specific fixture, old data will be purged."
    )
    parser.add_argument("filename", type=str, help="The JSON dataset file")

    args = parser.parse_args()

    with open(args.filename, "rt") as f:
        data = json.load(f)

    import_data(data)
