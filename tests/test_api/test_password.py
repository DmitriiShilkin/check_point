import uuid

from httpx import AsyncClient
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from schemas.password import ResetEmailPassword, ResetPassword, SetPassword

ROOT_ENDPOINT = "/check-point/api/v1/password/"


class TestPasswordApi:
    async def test_set(
        self,
        user: User,
        http_client: AsyncClient,
    ) -> None:
        data = SetPassword(
            user_uid=user.uid,
            password="msaldkfmqor14",
        )
        endpoint = f"{ROOT_ENDPOINT}set_password/{user.uid}/"
        response = await http_client.post(endpoint, json=data.model_dump())
        assert response.status_code == 200
        assert str(user.uid) == response.json()

    async def test_set_by_non_existent_user(
        self,
        http_client: AsyncClient,
    ) -> None:
        user_uid = uuid.uuid4()
        data = SetPassword(
            user_uid=user_uid,
            password="msaldkfmqor14",
        )
        endpoint = f"{ROOT_ENDPOINT}set_password/{user_uid}/"
        response = await http_client.post(endpoint, json=data.model_dump())
        assert response.status_code == 404

    async def test_reset_by_email(
        self,
        user: User,
        http_client: AsyncClient,
        async_session: AsyncSession,
        mocker: MockerFixture,
    ) -> None:
        mocker_send_mail = mocker.patch(
            "utilies.email_client.EmailClient.send_mail",
            return_value=None,
        )
        user.email_verify = True
        await async_session.commit()

        data = ResetEmailPassword(
            email=user.email,
        )
        endpoint = f"{ROOT_ENDPOINT}reset_password_email/"
        response = await http_client.post(
            endpoint,
            json=data.model_dump(),
        )
        assert response.status_code == 200
        assert "/restore/" in response.json()

        # Проверка отправки письма при восстановлении пароля
        arg = mocker_send_mail.mock_calls[0].args[0]
        assert arg.recipients[0] == data.email
        assert arg.subject == "Восстановление пароля"

    async def test_reset_by_unverified_email(
        self,
        user: User,
        http_client: AsyncClient,
    ) -> None:
        data = ResetEmailPassword(
            email=user.email,
        )
        endpoint = f"{ROOT_ENDPOINT}reset_password_email/"
        response = await http_client.post(
            endpoint,
            json=data.model_dump(),
        )
        assert response.status_code == 403

    async def test_reset_unset_password_by_email(
        self,
        user: User,
        http_client: AsyncClient,
        async_session: AsyncSession,
    ) -> None:
        user.email_verify = True
        user.hashed_password = ""
        await async_session.commit()

        data = ResetEmailPassword(
            email=user.email,
        )
        endpoint = f"{ROOT_ENDPOINT}reset_password_email/"
        response = await http_client.post(
            endpoint,
            json=data.model_dump(),
        )
        assert response.status_code == 403

    async def test_reset_by_invalid_email(
        self,
        http_client: AsyncClient,
    ) -> None:
        data = ResetEmailPassword(
            email="test2@gmail.com",
        )
        endpoint = f"{ROOT_ENDPOINT}reset_password_email/"
        response = await http_client.post(
            endpoint,
            json=data.model_dump(),
        )
        assert response.status_code == 404

    async def test_reset(
        self,
        user: User,
        http_client: AsyncClient,
    ) -> None:
        data = ResetPassword(
            email=user.email,
            old_password="password",
            new_password="msaldkfmqor14",
        )
        endpoint = f"{ROOT_ENDPOINT}reset_password/"
        response = await http_client.post(
            endpoint,
            json=data.model_dump(),
        )
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["Result"] == "OK"

    async def test_reset_with_invalid_password(
        self,
        user: User,
        http_client: AsyncClient,
    ) -> None:
        data = ResetPassword(
            email=user.email,
            old_password="msaldkfmqor13",
            new_password="msaldkfmqor14",
        )
        endpoint = f"{ROOT_ENDPOINT}reset_password/"
        response = await http_client.post(
            endpoint,
            json=data.model_dump(),
        )
        assert response.status_code == 404

    async def test_reset_with_invalid_email(
        self,
        http_client: AsyncClient,
    ) -> None:
        data = ResetPassword(
            email="test2@gmail.com",
            old_password="password",
            new_password="msaldkfmqor14",
        )
        endpoint = f"{ROOT_ENDPOINT}reset_password/"
        response = await http_client.post(
            endpoint,
            json=data.model_dump(),
        )
        assert response.status_code == 404

    async def test_send_first_login(
        self,
        user: User,
        http_client: AsyncClient,
        mocker: MockerFixture,
    ) -> None:
        mocker_send_mail = mocker.patch(
            "utilies.email_client.EmailClient.send_mail",
            return_value=None,
        )
        endpoint = f"{ROOT_ENDPOINT}send_login_email/{user.id}/"
        response = await http_client.get(endpoint)
        assert response.status_code == 307

        # Проверка отправки письма при первом входе
        arg = mocker_send_mail.mock_calls[0].args[0]
        assert arg.recipients[0] == user.email
        assert arg.subject == "Первый вход"

    async def test_send_first_login_by_non_existent_user(
        self,
        http_client: AsyncClient,
    ) -> None:
        endpoint = f"{ROOT_ENDPOINT}send_login_email/123/"
        response = await http_client.get(endpoint)
        assert response.status_code == 404

    async def test_check(
        self,
        user: User,
        http_client: AsyncClient,
    ) -> None:
        data = ResetEmailPassword(
            email=user.email,
        )
        endpoint = f"{ROOT_ENDPOINT}check/"
        response = await http_client.post(
            endpoint,
            json=data.model_dump(),
        )
        assert response.status_code == 200

    async def test_check_unset_password(
        self,
        user: User,
        http_client: AsyncClient,
        async_session: AsyncSession,
    ) -> None:
        user.hashed_password = ""
        await async_session.commit()

        data = ResetEmailPassword(
            email=user.email,
        )
        endpoint = f"{ROOT_ENDPOINT}check/"
        response = await http_client.post(
            endpoint,
            json=data.model_dump(),
        )
        assert response.status_code == 403

    async def test_check_non_existent_user(
        self,
        http_client: AsyncClient,
    ) -> None:
        data = ResetEmailPassword(
            email="test2@gmail.com",
        )
        endpoint = f"{ROOT_ENDPOINT}check/"
        response = await http_client.post(
            endpoint,
            json=data.model_dump(),
        )
        assert response.status_code == 404
