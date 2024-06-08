from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime


engine = create_engine('sqlite:///app/database/women_bot.db', echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)  # Primary key
    user_id = Column(Integer, unique=True)  # Assuming user_id is unique
    gender = Column(String)
    city = Column(String)
    subscription_type = Column(String)
    subscription_status = Column(String)
    subscription_end_date = Column(Date)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    subscriptions = relationship('Subscription', order_by='Subscription.subscription_id', back_populates='user')
    profiles = relationship('Profile', order_by='Profile.profile_id', back_populates='user')
    reviews = relationship('Review', order_by='Review.review_id', back_populates='user')

class Subscription(Base):
    __tablename__ = 'subscriptions'

    subscription_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    type = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    status = Column(String, nullable=False)

    user = relationship('User', back_populates='subscriptions')


class City(Base):
    __tablename__ = 'cities'

    city_id = Column(Integer, primary_key=True, autoincrement=True)
    city_name = Column(String, unique=True, nullable=False)


class Profile(Base):
    __tablename__ = 'profiles'

    profile_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    name = Column(String)
    age = Column(Integer)
    weight = Column(Integer)
    height = Column(Integer)
    breast_size = Column(String)
    hourly_rate = Column(Integer)
    apartments = Column(Boolean)
    outcall = Column(Boolean)
    photos = Column(Text)
    city = Column(String)
    phone_number = Column(String)

    user = relationship("User", back_populates="profiles")





class Review(Base):
    __tablename__ = 'reviews'

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    phone_number = Column(String, nullable=False)
    review_text = Column(Text, nullable=False)
    review_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship('User', back_populates='reviews')


class AdminAction(Base):
    __tablename__ = 'admin_actions'

    action_id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, nullable=False)
    action_type = Column(String, nullable=False)
    action_details = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


Base.metadata.create_all(engine)