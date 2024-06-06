from sqlalchemy import create_engine, Column, Integer, String, Date, BIGINT
from sqlalchemy import Column, Integer, String, DateTime
import sqlalchemy
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from datetime import datetime


engine = create_engine('sqlite:///app/database/women_bot.db', echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = sqlalchemy.orm.declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)


class Admins(Base):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True)
    user_id = Column(BIGINT)


Base.metadata.create_all(engine)