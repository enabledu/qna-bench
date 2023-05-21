import json
import random
import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_asyncio
import sqlalchemy.orm as orm
import _sqlalchemy.models as m


engine = None
session_factory = None
ASYNC = True
INSERT_PREFIX = "insert_test__"


async def connect(ctx):
    global engine
    global session_factory

    if session_factory is None:
        engine = sa_asyncio.create_async_engine(
            f"postgresql+asyncpg://sqlalch_bench:edgedbbenchmark@"
            f"{ctx.db_host}:{ctx.pg_port}/sqlalch_bench"
        )
        session_factory = orm.sessionmaker(
            bind=engine, expire_on_commit=False, class_=sa_asyncio.AsyncSession
        )

    return session_factory()


async def close(ctx, sess):
    await sess.close()
    await sess.bind.dispose()


async def load_ids(ctx, sess):
    users = ( await sess.scalars(
        sa.select(m.User).order_by(sa.func.random()).limit(ctx.number_of_ids)
    )).all()

    questions = (await sess.scalars(
        sa.select(m.Question).order_by(sa.func.random()).limit(ctx.number_of_ids)
    )).all()

    answers = (await sess.scalars(
        sa.select(m.Answer).order_by(sa.func.random()).limit(ctx.number_of_ids)
    )).all()

    comments = (await sess.scalars(
        sa.select(m.Comment).order_by(sa.func.random()).limit(ctx.number_of_ids)
    )).all()

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


async def get_answer(sess, id):
    Answer = m.Answer
    User = m.User
    Comment = m.Comment

    stmt = (
        sa.select(
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
        .select_from(Answer)
        .join(User, Answer.author_id == User.id)
        .outerjoin(Comment, Answer.id == Comment.answer_id)
        .where(Answer.id == id)
    )

    result = (await sess.execute(stmt)).first()

    if result is not None:
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
    else:
        return None


async def get_comments_on_question(sess, id):
    Comment = m.Comment
    Question = m.Question
    User = m.User

    comments_ids = (
        sa.select(Comment.id)
        .join(Question, Question.id == Comment.question_id)
        .where(Question.id == id)
        .subquery()
    )

    stmt = (
        sa.select(
            Comment.content,
            Comment.upvote,
            Comment.downvote,
            User.id.label("author_id"),
            User.email.label("author_email"),
            User.username.label("author_username"),
        )
        .join(User, Comment.author_id == User.id)
        .where(Comment.id.in_(comments_ids))
    )
    rows = await sess.execute(stmt)

    comments_details = [
        {
            "content": row.content,
            "upvote": row.upvote,
            "downvote": row.downvote,
            "author_id": row.author_id,
            "author_email": row.author_email,
            "author_username": row.author_username,
        }
        for row in rows.all()
    ]
    return json.dumps(comments_details)



async def insert_user(sess, val):
    User = m.User

    new_user = User(
        age=random.randint(10, 100),
        email=f"{val}@test.com",
        first_name=f"{val}First",
        last_name=f"{val}Last",
        username=f"{val}Username",
        hashed_password=f"{val}Password",
    )

    sess.add(new_user)
    await sess.commit()

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



async def update_comments_on_answer(sess, val):
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
    await sess.commit()

    result = json.dumps(
        {
            "id": new_comment.id,
            "upvote": new_comment.upvote,
            "downvote": new_comment.downvote,
            "content": new_comment.content,
            "author_id": new_comment.author_id,
            "answer_id": new_comment.answer_id,
        }
    )
    return result



async def cleanup(ctx, sess, queryname):
    if queryname == "insert_user":
        await sess.execute(
            sa.delete(m.User)
            .where(m.User.username.like(f"{INSERT_PREFIX}%"))
            .execution_options(synchronize_session=False)
        )
    elif queryname == "update_comments_on_answer":
        await sess.execute(
            sa.delete(m.Comment)
            .where(m.Comment.content.like(f"{INSERT_PREFIX}%"))
            .execution_options(synchronize_session=False)
        )

    await sess.commit()
