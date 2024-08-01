import random
import string
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models.users import User, Profile, Review


async def get_all_user_ids(db: AsyncSession):
    try:
        result = await db.execute(select(User.user_id))
        user_ids = result.scalars().all()
        return user_ids
    except Exception as e:
        print(f"Ошибка при получении id всех юзеров: {e}")


async def count_male_users(db: AsyncSession):
    try:
        result = await db.execute(select(func.count()).filter(
            User.gender == "Мужчина"
        ))
        count = result.scalar()
        return count
    except Exception as e:
        print(f"Ошибка в функции count_male_users: {e}")


async def count_female_users_with_no_subscription(db: AsyncSession):
    try:
        result = await db.execute(select(func.count()).filter(
            (User.gender == "Женщина") & (User.subscription_type == "None")
        ))
        count = result.scalar()
        return count
    except Exception as e:
        print(f"Ошибка в функции count_female_users_with_no_subscription: {e}")


async def get_count_profiles(db: AsyncSession, city: str) -> int:
    try:
        stmt = select(func.count(Profile.id)).where(Profile.city == city)

        # Выполняем запрос и получаем результат
        result = await db.execute(stmt)
        count = result.scalar()  # Получаем единственное значение

        return count
    except Exception as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return 0


async def get_male_users(db: AsyncSession):
    try:
        result = await db.execute(select(User).filter(User.gender == "Мужчина"))
        male_users = result.scalars().all()
        return male_users
    except Exception as e:
        print(f"Ошибка в функции get_male_users: {e}")


async def get_female_users(db: AsyncSession):
    try:
        result = await db.execute(select(User).filter(
            (User.gender == "Женщина") & (User.subscription_type == "None")
        ))
        female_users = result.scalars().all()
        return female_users
    except Exception as e:
        print(f"Ошибка в функции get_female_users: {e}")



async def get_users_with_active_subscription(db: AsyncSession):
    try:
        result = await db.execute(select(User).filter(User.subscription_status == "ACTIVE"))
        active_users = result.scalars().all()
        return active_users
    except Exception as e:
        print(f"Ошибка в функции get_users_with_active_subscription: {e}")


def generate_customer_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


async def add_or_update_user(user_id: int, gender: str, db: AsyncSession):
    try:
        async with db.begin():
            result = await db.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()
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
            await db.commit()
        return user
    except Exception as e:
        print(f"Ошибка в функции add_or_update_user: {e}")


async def update_user_subscription(db: AsyncSession, user_id: int, subscription_status: str, subscription_type: str, subscription_end_date: datetime):
    try:
        async with db.begin():
            result = await db.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()
            if user:
                user.subscription_status = subscription_status
                user.subscription_type = subscription_type
                user.subscription_end_date = subscription_end_date.replace(microsecond=0)
                user.updated_at = datetime.now()
                db.add(user)
                await db.commit()
                return user
            else:
                print(f'User with ID {user_id} not found.')
                return None
    except Exception as e:
        print(f"Ошибка в функции update_user_subscription: {e}")


async def delete_user_subscription_details(db: AsyncSession, user_id: int):
    try:
        async with db.begin():
            result = await db.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()
            if user:
                user.subscription_status = None
                user.subscription_type = None
                user.subscription_end_date = None
                user.rebill_id = None
                user.updated_at = datetime.now()
                await db.commit()
                return user
            else:
                print(f'User with ID {user_id} not found.')
                return None
    except Exception as e:
        print(f"Ошибка в функции delete_user_subscription_details: {e}")


async def get_user_info(db: AsyncSession, user_id: int):
    try:
        result = await db.execute(select(User).filter(User.user_id == user_id))
        user_info = result.scalars().first()
        if user_info:
            print(user_info)
            return user_info
        else:
            print('Не смогли найти информацию о юзере')
            return None
    except Exception as e:
        print(f"Ошибка в функции get_user_info: {e}")


async def is_profile_info(db: AsyncSession, user_id: int):
    try:
        result = await db.execute(select(Profile).filter(Profile.user_id == user_id))
        is_profile = result.scalars().first()
        return is_profile
    except Exception as e:
        print(f"Ошибка в функции is_profile_info: {e}")


async def delete_profile(db: AsyncSession, user_id: int):
    try:
        async with db.begin():
            result = await db.execute(select(Profile).filter(Profile.user_id == user_id))
            user = result.scalars().first()
            if user:
                await db.delete(user)
                await db.commit()
                print(f"{user} удален")
    except Exception as e:
        print(f"Ошибка в функции delete_profile: {e}")


async def update_user_city(db: AsyncSession, user_id: int, city: str):
    try:
        async with db.begin():
            result = await db.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()
            if user:
                user.city = city
                await db.commit()
                print(f"User {user_id} обновлен с городом {city}!")
    except Exception as e:
        print(f"Ошибка в функции update_user_city: {e}")


async def create_profile(db: AsyncSession,
                         user_id: int,
                         name: str,
                         age: int,
                         weight: int,
                         height: int,
                         breast_size: str,
                         phone_number: str,
                         apartments: bool,
                         outcall: bool,
                         photos: str,
                         city: str):
    try:
        async with db.begin():
            new_profile = Profile(
                user_id=user_id,
                name=name,
                age=age,
                weight=weight,
                height=height,
                breast_size=breast_size,
                phone_number=phone_number,
                apartments=apartments,
                outcall=outcall,
                photos=photos,
                city=city
            )
            db.add(new_profile)
            await db.commit()
            return new_profile
    except Exception as e:
        print(f"Ошибка в функции create_profile: {e}")


async def get_user_city(db: AsyncSession, user_id: int) -> str:
    try:
        result = await db.execute(select(User).filter(User.user_id == user_id))
        user = result.scalars().first()
        if user:
            return user.city
    except Exception as e:
        print(f"Ошибка в функции get_user_city: {e}")


async def get_all_profiles(db: AsyncSession, city: str):
    try:
        result = await db.execute(select(Profile).filter(Profile.city == city))
        profiles = result.scalars().all()
        if not profiles:
            print("Результатов в данном городе не найдено")
        return profiles
    except Exception as e:
        print(f"Ошибка в функции get_all_profiles: {e}")


async def get_positive_reviews(db: AsyncSession, phone_number: str):
    try:
        result = await db.execute(select(Review).filter(Review.phone_number == phone_number, Review.review_type == 'positive'))
        return result.scalars().all()
    except Exception as e:
        print(f"Ошибка в функции get_positive_reviews: {e}")


async def get_negative_reviews(db: AsyncSession, phone_number: str):
    try:
        result = await db.execute(select(Review).filter(Review.phone_number == phone_number, Review.review_type == 'negative'))
        return result.scalars().all()
    except Exception as e:
        print(f"Ошибка в функции get_negative_reviews: {e}")


async def send_women_review(db: AsyncSession, type: str, number: str, text: str, user_id: int):
    try:
        async with db.begin():
            new_review = Review(user_id=user_id, review_type=type, phone_number=number, review_text=text)
            db.add(new_review)
            await db.commit()
            print("Отзыв добавлен")
    except Exception as e:
        print(f"Ошибка в функции send_women_review: {e}")
