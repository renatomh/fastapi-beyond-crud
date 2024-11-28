"""
Service for authentication methods.
"""

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from .schemas import UserCreateModel
from src.db.models import User
from .utils import generate_passwd_hash


class UserService:
    async def get_user_by_email(self, email: str, session: AsyncSession) -> User:
        statement = select(User).where(User.email == email)

        result = await session.exec(statement)

        return result.first()

    async def user_exists(self, email: str, session: AsyncSession) -> bool:
        user = await self.get_user_by_email(email, session)

        return user is not None

    async def create_user(
        self, user_data: UserCreateModel, session: AsyncSession
    ) -> User:
        user_data_dict = user_data.model_dump()

        new_user = User(
            **user_data_dict,
        )

        new_user.password_hash = generate_passwd_hash(user_data_dict["password"])
        new_user.role = "user"

        session.add(new_user)

        await session.commit()

        return new_user

    async def update_user(
        self, user: User, user_data: dict, session: AsyncSession
    ) -> User:
        for k, v in user_data.items():
            setattr(user, k, v)

        await session.commit()

        return user
