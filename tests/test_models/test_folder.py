import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from models.folder import Folder
from schemas.folder import FolderCreate


class TestFolderModel:
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
        current_fields_name = [i.name for i in Folder.__table__.columns]
        related_fields = [
            i._dependency_processor.key if i._dependency_processor else None
            for i in Folder.__mapper__.relationships
        ]
        all_model_fields = current_fields_name + related_fields
        schema_fields_name = {
            "account",
            "name",
            "parent",
            "order",
        }
        for field in schema_fields_name:
            assert field in all_model_fields, (
                "Нет необходимого поля %s" % field
            )

    async def test_create_without_name(
        self,
    ):
        with pytest.raises(ValidationError) as exc_info:
            FolderCreate(
                parent_uid=uuid.uuid4(),
                account_uid=uuid.uuid4(),
            )

        exception_msg = exc_info.value
        assert exc_info.type is ValidationError
        assert "Field required" in str(exception_msg)

    async def test_create_without_account_uid(
        self,
    ):
        with pytest.raises(ValidationError) as exc_info:
            FolderCreate(
                name="TestNameCreate",
                parent_uid=uuid.uuid4(),
            )

        exception_msg = exc_info.value
        assert exc_info.type is ValidationError
        assert "Field required" in str(exception_msg)

    async def test_create_without_parent_uid(
        self,
    ):
        with pytest.raises(ValidationError) as exc_info:
            FolderCreate(
                name="TestNameCreate",
                account_uid=uuid.uuid4(),
            )

        exception_msg = exc_info.value
        assert exc_info.type is ValidationError
        assert "Field required" in str(exception_msg)
