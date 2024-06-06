from sqlalchemy.orm import Session
from app.database.models.users import User


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


def update_user_city(db: Session, user_id, city):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        user.city = city
        db.commit()
        print(f"User {user_id} обновлен с городом {city}!")