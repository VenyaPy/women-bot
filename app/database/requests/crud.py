from sqlalchemy.orm import Session
from app.database.models.users import User, Profile, Review


def add_or_update_user(db: Session, user_id, gender):
    user = db.query(User).filter(User.user_id == user_id).first()

    if user:
        user.gender = gender
        print(f"User {user_id} обновлен!")
    else:
        new_user = User(user_id=user_id, gender=gender)
        db.add(new_user)
        print(f"User {user_id} добавлен!")

    db.commit()


def get_user_info(db: Session, user_id: int):
    user_info = db.query(User).filter(User.user_id == user_id).first()

    if user_info:
        print(user_info)
        return user_info
    else:
        print('Не смогли найти информацию о юзере')
        return None


def update_user_city(db: Session, user_id, city):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        user.city = city
        db.commit()
        print(f"User {user_id} обновлен с городом {city}!")


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


