import random
import string
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models.users import User, Profile, Review


async def get_all_user_ids(db: AsyncSession):
    result = await db.execute(select(User.user_id))
    user_ids = result.scalars().all()
    return user_ids


async def get_male_users(db: AsyncSession):
    result = await db.execute(select(User).filter(User.gender == "Мужчина"))
    male_users = result.scalars().all()
    return male_users


async def get_female_users(db: AsyncSession):
    result = await db.execute(select(User).filter(User.gender == "Женщина"))
    female_users = result.scalars().all()
    return female_users


async def get_users_with_active_subscription(db: AsyncSession):
    result = await db.execute(select(User).filter(User.subscription_status == "ACTIVE"))
    active_users = result.scalars().all()
    return active_users


def generate_customer_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


async def add_or_update_user(user_id: int, gender: str, db: AsyncSession):
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


async def update_user_subscription(db: AsyncSession, user_id: int, subscription_status: str, subscription_type: str, subscription_end_date: datetime, rebill_id: str, payment_id: str):
    async with db.begin():
        result = await db.execute(select(User).filter(User.user_id == user_id))
        user = result.scalars().first()
        if user:
            user.subscription_status = subscription_status
            user.subscription_type = subscription_type
            user.subscription_end_date = subscription_end_date.replace(microsecond=0)
            user.rebill_id = rebill_id
            user.payment_id = payment_id
            user.updated_at = datetime.now()
            db.add(user)
            await db.commit()
            return user
        else:
            print(f'User with ID {user_id} not found.')
            return None


async def delete_user_subscription_details(db: AsyncSession, user_id: int):
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


async def get_user_info(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.user_id == user_id))
    user_info = result.scalars().first()
    if user_info:
        print(user_info)
        return user_info
    else:
        print('Не смогли найти информацию о юзере')
        return None


async def is_profile_info(db: AsyncSession, user_id: int):
    result = await db.execute(select(Profile).filter(Profile.user_id == user_id))
    is_profile = result.scalars().first()
    return is_profile


async def delete_profile(db: AsyncSession, user_id: int):
    async with db.begin():
        result = await db.execute(select(Profile).filter(Profile.user_id == user_id))
        user = result.scalars().first()
        if user:
            await db.delete(user)
            await db.commit()
            print(f"{user} удален")


async def update_user_city(db: AsyncSession, user_id: int, city: str):
    async with db.begin():
        result = await db.execute(select(User).filter(User.user_id == user_id))
        user = result.scalars().first()
        if user:
            user.city = city
            await db.commit()
            print(f"User {user_id} обновлен с городом {city}!")


async def create_profile(db: AsyncSession,
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
    async with db.begin():
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
        await db.commit()
        return new_profile



async def get_user_city(db: AsyncSession, user_id: int) -> str:
    result = await db.execute(select(User).filter(User.user_id == user_id))
    user = result.scalars().first()
    if user:
        return user.city


async def get_all_profiles(db: AsyncSession, city: str):
    result = await db.execute(select(Profile).filter(Profile.city == city))
    profiles = result.scalars().all()
    if not profiles:
        print("Результатов в данном городе не найдено")
    return profiles


async def get_positive_reviews(db: AsyncSession, phone_number: str):
    result = await db.execute(select(Review).filter(Review.phone_number == phone_number, Review.review_type == 'positive'))
    return result.scalars().all()


async def get_negative_reviews(db: AsyncSession, phone_number: str):
    result = await db.execute(select(Review).filter(Review.phone_number == phone_number, Review.review_type == 'negative'))
    return result.scalars().all()


async def send_women_review(db: AsyncSession, type: str, number: str, text: str, user_id: int):
    async with db.begin():
        new_review = Review(user_id=user_id, review_type=type, phone_number=number, review_text=text)
        db.add(new_review)
        await db.commit()
        print("Отзыв добавлен")
