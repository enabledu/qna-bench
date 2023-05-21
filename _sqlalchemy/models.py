from sqlalchemy import (
    CheckConstraint,
    Column,
    Integer,
    String,
    Text,
    Boolean,
    SmallInteger,
    ForeignKey,
    ARRAY,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "User"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    is_verified = Column(Boolean, nullable=False, default=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    age = Column(
        SmallInteger, CheckConstraint("age >= 0 AND age <= 110"), nullable=False
    )


class Question(Base):
    __tablename__ = "Question"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    upvote = Column(SmallInteger, nullable=False, default=0)
    downvote = Column(SmallInteger, nullable=False, default=0)
    author_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    title = Column(String(255), nullable=False)
    tags = Column(ARRAY(String(255)))
    is_accepted = Column(Boolean, nullable=False, default=False)
    author = relationship("User", backref="questions")


class Answer(Base):
    __tablename__ = "Answer"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    upvote = Column(SmallInteger, nullable=False, default=0)
    downvote = Column(SmallInteger, nullable=False, default=0)
    author_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("Question.id"), nullable=False)
    is_accepted = Column(Boolean, nullable=False, default=False)
    author = relationship("User", backref="answers")
    question = relationship("Question", backref="answers")


class Comment(Base):
    __tablename__ = "Comment"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    upvote = Column(SmallInteger, nullable=False, default=0)
    downvote = Column(SmallInteger, nullable=False, default=0)
    author_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("Question.id"))
    answer_id = Column(Integer, ForeignKey("Answer.id"))
    author = relationship("User", backref="comments")
    question = relationship("Question", backref="comments")
    answer = relationship("Answer", backref="comments")
