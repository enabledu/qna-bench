import argparse
import json
import progress.bar

import sqlalchemy as sa
import sqlalchemy.orm as orm

import models as m


def bar(label, total):
    return progress.bar.Bar(label[:32].ljust(32), max=total)


def bulk_insert(db, label, data, into):
    label = f"Creating {len(data)} {label}"
    pbar = bar(label, len(data))

    while data:
        chunk = data[:1000]
        data = data[1000:]
        db.execute(sa.insert(into), chunk)
        db.commit()
        pbar.next(len(chunk))
    pbar.finish()


def reset_sequence(db, tablename):
    tab = sa.table(tablename, sa.column("id"))

    db.execute(
        sa.select(
            sa.func.setval(
                f"{tablename}_id_seq",
                sa.select(tab.c.id)
                .order_by(tab.c.id.desc())
                .limit(1)
                .scalar_subquery(),
            )
        )
    )


def load_data(filename, engine):
    session_factory = orm.sessionmaker(bind=engine)
    Session = orm.scoped_session(session_factory)

    with Session() as db:
        # first clear all the existing data
        print(f"purging existing data...")

        db.execute(sa.delete(m.Comment))
        db.execute(sa.delete(m.Answer))
        db.execute(sa.delete(m.Question))
        db.execute(sa.delete(m.User))
        db.commit()

    # read the JSON data
    with open(filename, "rt") as f:
        data = json.load(f)

    users_data = [
        dict(
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
        for u in data["users"]
    ]

    questions_data = [
        dict(
            upvote=q["upvote"],
            downvote=q["downvote"],
            content=q["content"],
            tags=q["tags"],
            title=q["title"],
            author_id=q["author"],
        )
        for q in data["questions"]
    ]

    answers_data = [
        dict(
            upvote=a["upvote"],
            downvote=a["downvote"],
            content=a["content"],
            is_accepted=a["is_accepted"],
            author_id=a["author"],
            question_id=a["question"],
        )
        for a in data["answers"]
    ]

    comments_data = [
        dict(
            upvote=c["upvote"],
            downvote=c["downvote"],
            content=c["content"],
            author_id=c["author"],
            question_id=c["question"],
            answer_id=c["answer"],
        )
        for c in data["comments"]
    ]

    with Session() as db:
        # bulk create all the users
        bulk_insert(db, "users", users_data, m.User)

        # bulk create all the questions
        bulk_insert(db, "questions", questions_data, m.Question)

        # bulk create all the answers
        bulk_insert(db, "answers", answers_data, m.Answer)

        # bulk create all the comments
        bulk_insert(db, "comments", comments_data, m.Comment)

        # reconcile the autoincrementing indexes with the actual indexes
        reset_sequence(db, "Comment")
        reset_sequence(db, "Answer")
        reset_sequence(db, "Question")
        reset_sequence(db, "User")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load a specific fixture, old data will be purged."
    )
    parser.add_argument("filename", type=str, help="The JSON dataset file")

    args = parser.parse_args()

    engine = sa.create_engine(
        "postgresql+asyncpg://sqlalch_bench:edgedbbenchmark@localhost:3500/sqlalch_bench?async_fallback=True"
    )

    load_data(args.filename, engine)
