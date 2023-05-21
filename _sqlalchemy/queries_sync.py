import json
import random
import sqlalchemy as sa
import sqlalchemy.orm as orm
import _sqlalchemy.models as m


engine = None
session_factory = None
INSERT_PREFIX = "insert_test__"


def connect(ctx):
    global engine
    global session_factory

    if session_factory is None:
        engine = sa.create_engine(
            f"postgresql://sqlalch_bench:edgedbbenchmark@"
            f"{ctx.db_host}:{ctx.pg_port}/sqlalch_bench"
        )
        session_factory = orm.sessionmaker(bind=engine, expire_on_commit=False)

    return session_factory()


def close(ctx, sess):
    sess.close()
    sess.bind.dispose()


def load_ids(ctx, sess):
    users = sess.scalars(
        sa.select(m.User).order_by(sa.func.random()).limit(ctx.number_of_ids)
    ).all()

    questions = sess.scalars(
        sa.select(m.Question).order_by(sa.func.random()).limit(ctx.number_of_ids)
    ).all()

    answers = sess.scalars(
        sa.select(m.Answer).order_by(sa.func.random()).limit(ctx.number_of_ids)
    ).all()

    comments = sess.scalars(
        sa.select(m.Comment).order_by(sa.func.random()).limit(ctx.number_of_ids)
    ).all()

    return dict(
        get_answer=[a.id for a in answers],
        get_comments_on_question=[q.id for q in questions],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[INSERT_PREFIX] * ctx.concurrency,
        update_comments_on_answer=[
            {
                "prefix": INSERT_PREFIX,
                "answer_id": [a.id for a in answers],
                "author_id": [u.id for u in users],
            }
        ]
        * ctx.concurrency,
    )


def get_answer(sess, id):
    Answer = m.Answer
    User = m.User
    Comment = m.Comment

    stmt = (
        sess.query(
            Answer.content,
            Answer.upvote,
            Answer.downvote,
            Answer.is_accepted,
            User.email.label("author_email"),
            User.username.label("author_username"),
            Comment.content.label("comment_content"),
            Comment.upvote.label("comment_upvote"),
            Comment.downvote.label("comment_downvote"),
            Comment.author_id.label("comment_author_id"),
        )
        .join(User, Answer.author_id == User.id)
        .outerjoin(Comment, Answer.id == Comment.answer_id)
        .filter_by(id=id)
    )
    result = stmt.first()

    answer_details = json.dumps(
        {
            "content": result.content,
            "upvote": result.upvote,
            "downvote": result.downvote,
            "is_accepted": result.is_accepted,
            "author_email": result.author_email,
            "author_username": result.author_username,
            "comment_content": result.comment_content,
            "comment_upvote": result.comment_upvote,
            "comment_downvote": result.comment_downvote,
            "comment_author_id": result.comment_author_id,
        }
    )
    return answer_details


def get_comments_on_question(sess, id):
    Comment = m.Comment
    Question = m.Question
    User = m.User

    comments_ids = (
        sess.query(Comment.id)
        .join(Question, Question.id == Comment.question_id)
        .filter(Question.id == id)
        .subquery()
    )

    stmt = (
        sess.query(
            Comment.content,
            Comment.upvote,
            Comment.downvote,
            User.id.label("author_id"),
            User.email.label("author_email"),
            User.username.label("author_username"),
        )
        .join(User, Comment.author_id == User.id)
        .filter(Comment.id.in_(sess.query(comments_ids.c.id)))
    )
    rows = stmt.all()

    comments_details = [
        {
            "content": row.content,
            "upvote": row.upvote,
            "downvote": row.downvote,
            "author_id": row.author_id,
            "author_email": row.author_email,
            "author_username": row.author_username,
        }
        for row in rows
    ]
    return json.dumps(comments_details)



def insert_user(conn, val):
    User = m.User

    new_user = User(
        age=random.randint(10, 100),
        email=f"{val}@test.com",
        first_name=f"{val}First",
        last_name=f"{val}Last",
        username=f"{val}Username",
        hashed_password=f"{val}Password"
    )

    conn.add(new_user)
    conn.commit()

    result = json.dumps(
        {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
        }
    )
    return result



def update_comments_on_answer(sess, val):
    num = random.randrange(10_000)

    Comment = m.Comment

    new_comment = Comment(
        upvote=num,
        downvote=num // 10,
        content=f"{val['prefix']}{num}",
        author_id=random.choice(val["author_id"]),
        answer_id=random.choice(val["answer_id"]),
    )

    sess.add(new_comment)
    sess.commit()

    return json.dumps(
        {
            "id": new_comment.id,
            "upvote": new_comment.upvote,
            "downvote": new_comment.downvote,
            "content": new_comment.content,
            "author_id": new_comment.author_id,
            "answer_id": new_comment.answer_id,
        }
    )


def cleanup(ctx, sess, queryname):
    if queryname == "insert_user":
        sess.execute(
            sa.delete(m.User)
            .where(m.User.username.like(f"{INSERT_PREFIX}%"))
            .execution_options(synchronize_session=False)
        )
    elif queryname == "update_comments_on_answer":
        sess.execute(
            sa.delete(m.Comment)
            .where(m.Comment.content.like(f"{INSERT_PREFIX}%"))
            .execution_options(synchronize_session=False)
        )

    sess.commit()

