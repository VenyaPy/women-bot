import random
import string
from datetime import datetime

from sqlalchemy.orm import Session
from app.database.models.users import User, Profile, Review


def get_all_user_ids(db: Session) -> list:
    user_ids = db.query(User.user_id).all()
    return [user_id[0] for user_id in user_ids]


def get_male_users(db: Session) -> list:
    male_users = db.query(User).filter(User.gender == "Мужчина").all()
    return male_users


def get_female_users(db: Session) -> list:
    female_users = db.query(User).filter(User.gender == "Женщина").all()
    return female_users


def get_users_with_active_subscription(db: Session) -> list:
    active_users = db.query(User).filter(User.subscription_status == "True").all()
    return active_users


def generate_customer_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


def add_or_update_user(user_id: int, gender: str, db: Session):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        user.gender = gender
        user.updated_at = datetime.now()
    else:
        user = User(
            user_id=user_id,
            gender=gender,
            customer_key=generate_customer_key()
        )
        db.add(user)
    db.commit()
    return user


def update_user_subscription(db: Session,
                             user_id: int,
                             subscription_status: str,
                             subscription_type: str,
                             subscription_end_date,
                             rebill_id: str):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        user.subscription_status = subscription_status
        user.subscription_type = subscription_type
        user.subscription_end_date = subscription_end_date
        user.rebill_id = rebill_id
        user.updated_at = datetime.now()
        db.commit()
        return user
    else:
        print(f'User with ID {user_id} not found.')
        return None



def get_user_info(db: Session, user_id: int):
    user_info = db.query(User).filter(User.user_id == user_id).first()

    if user_info:
        print(user_info)
        return user_info
    else:
        print('Не смогли найти информацию о юзере')
        return None


def is_profile_info(db: Session, user_id: int):
    is_profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    if not is_profile:
        return None

    return is_profile


def delete_profile(db: Session, user_id: int):
    user = db.query(Profile).filter(Profile.user_id == user_id).first()
    db.delete(user)
    db.commit()

    print(f"{user} удален")


def update_user_city(db: Session, user_id, city):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        user.city = city
        db.commit()
        print(f"User {user_id} обновлен с городом {city}!")


def create_profile(db: Session,
                   user_id: int,
                   name: str,
                   age: int,
                   weight: int,
                   height: int,
                   breast_size: str,
                   hourly_rate: int,
                   phone_number: str,
                   apartments: bool,
                   outcall: bool,
                   photos: str,
                   city: str):
    new_profile = Profile(
        user_id=user_id,
        name=name,
        age=age,
        weight=weight,
        height=height,
        breast_size=breast_size,
        hourly_rate=hourly_rate,
        phone_number=phone_number,
        apartments=apartments,
        outcall=outcall,
        photos=photos,
        city=city
    )
    db.add(new_profile)
    db.commit()
    return new_profile


def get_user_city(db: Session, user_id: int) -> str:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        return user.city



def get_all_profiles(db: Session, city: str):
    profiles = db.query(Profile).filter(Profile.city == city).all()
    if not profiles:
        print("Результатов в данном городе не найдено")
    return profiles


def get_positive_reviews(db: Session, phone_number: str):
    return db.query(Review).filter(Review.phone_number == phone_number, Review.review_type == 'positive').all()

def get_negative_reviews(db: Session, phone_number: str):
    return db.query(Review).filter(Review.phone_number == phone_number, Review.review_type == 'negative').all()


def send_women_review(db: Session, type: str, number: str, text: str, user_id: int):
    new_review = Review(user_id=user_id, review_type=type, phone_number=number, review_text=text)
    db.add(new_review)
    db.commit()
    print("Отзыв добавлен")


