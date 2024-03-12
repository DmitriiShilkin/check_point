import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from constants.user import UserRole
from models.user import User
from schemas.user import UserCreate, UserUpdate


class TestUserModel:
    async def test_fields(
        self,
        async_session: AsyncSession,
    ):
        """
        Тест проверки на соответствие полей текущей модели со Схемой БД
        - current_fields_name (list[str]):
            Текущие поля модели.
        - schema_fields_name (list[str]):
            Поля модели из схемы БД.
            Некоторые поля переименованы
            password (Схема БД) -> hashed_password (Текущие поля модели)
        """
        current_fields_name = [i.name for i in User.__table__.columns]
        related_fields = [
            i._dependency_processor.key for i in User.__mapper__.relationships
        ]
        all_model_fields = current_fields_name + related_fields
        schema_fields_name = {
            "nickname",
            "email",
            "hashed_password",
            "user_photo",
            # "extra_permission",
            "preferences",
            "created_at",
            "updated_at",
            "phone",
            "industry",
            "known_about_us",
            "tariff",
        }
        for field in schema_fields_name:
            assert field in all_model_fields, (
                "Нет необходимого поля %s" % field
            )

    async def test_create_without_nickname(
        self,
    ):
        """
        Тест проверки создания пользователя с пустым полем nickname
            - проверяемое ограничение min_length = 3
        """
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                nickname="",
                email="test_create@gmail.com",
                password="msaldkfmqor13",
                role=UserRole.admin,
                phone="88005535",
            )

        exception_msg = exc_info.value
        assert exc_info.type is ValidationError
        assert "string_too_short" in str(exception_msg)

    async def test_create_without_email(
        self,
    ):
        """
        Тест проверки создания пользователя с пустым полем email
        """
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                nickname="Test Nickname Create",
                email="",
                password="msaldkfmqor13",
                role=UserRole.admin,
                phone="88005535",
            )

        exception_msg = exc_info.value
        assert exc_info.type is ValidationError
        assert (
            "The email address is not valid. It must have exactly one @-sign."
            in str(exception_msg)
        )

    async def test_update_empty_nickname(
        self,
    ):
        """
        Тест проверки обновления поля nickname на пустое значение
            - проверяемое ограничение min_length = 3
        """
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(
                nickname="",
            )
        exception_msg = exc_info.value
        assert exc_info.type is ValidationError
        assert "string_too_short" in str(exception_msg)
