import uuid
from typing import Callable

from httpx import AsyncClient
from pytest_mock import MockerFixture

from constants.user import UserRole
from models.user import User
from schemas.user import UserCreate, UserUpdate

ROOT_ENDPOINT = "/check-point/api/v1/users/"


class TestUserApi:
    async def test_get_list(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        response = await http_client.get(ROOT_ENDPOINT, headers=auth_headers)
        assert response.status_code == 200

    async def test_get_list_not_by_admin(
        self,
        http_client: AsyncClient,
        another_user: User,
        get_auth_headers: Callable,
    ) -> None:
        user_not_admin_headers = await get_auth_headers(another_user)
        response = await http_client.get(
            ROOT_ENDPOINT, headers=user_not_admin_headers
        )
        assert response.status_code == 403

    async def test_get_profile(
        self,
        http_client: AsyncClient,
        user: User,
        auth_headers: dict,
    ) -> None:
        endpoint = f"{ROOT_ENDPOINT}profile/"
        response = await http_client.get(endpoint, headers=auth_headers)
        assert response.status_code == 200
        response_data = response.json()
        assert str(user.uid) == response_data["uid"]

    async def test_get_retrieve(
        self,
        http_client: AsyncClient,
        user: User,
        auth_headers: dict,
    ) -> None:
        endpoint = f"{ROOT_ENDPOINT}{user.uid}/"
        response = await http_client.get(endpoint, headers=auth_headers)
        assert response.status_code == 200
        response_data = response.json()
        assert str(user.uid) == response_data["uid"]

    async def test_get_retrieve_non_existent_user(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        endpoint = f"{ROOT_ENDPOINT}{uuid.uuid4()}/"
        response = await http_client.get(endpoint, headers=auth_headers)
        assert response.status_code == 404

    async def test_get_user_email(
        self,
        http_client: AsyncClient,
        user: User,
        auth_headers: dict,
    ) -> None:
        endpoint = f"{ROOT_ENDPOINT}{user.uid}/email/"
        response = await http_client.get(endpoint, headers=auth_headers)
        assert response.status_code == 200
        response_data = response.json()
        assert str(user.email) == response_data

    async def test_get_non_existent_user_email(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        endpoint = f"{ROOT_ENDPOINT}{uuid.uuid4()}/email/"
        response = await http_client.get(endpoint, headers=auth_headers)
        assert response.status_code == 404

    async def test_create(
        self,
        http_client: AsyncClient,
        mocker: MockerFixture,
    ) -> None:
        mocker_send_mail = mocker.patch(
            "utilies.email_client.EmailClient.send_mail",
            return_value=None,
        )
        data = UserCreate(
            nickname="Test Nickname Create",
            email="test_create@gmail.com",
            password="msaldkfmqor13",
            role=UserRole.admin,
            phone="88005535",
        )
        response = await http_client.post(
            ROOT_ENDPOINT, json=data.model_dump()
        )
        assert response.status_code == 201
        response_data = response.json()
        assert data.email == response_data["email"]

        # Проверка отправки приветственного письма
        arg = mocker_send_mail.mock_calls[0].args[0]
        assert arg.recipients[0] == response_data["email"]
        assert arg.subject == "Добро пожаловать!"

        # Проверка отправки письма со ссылкой подтверждения email
        arg = mocker_send_mail.mock_calls[1].args[0]
        assert arg.recipients[0] == response_data["email"]
        assert (
            arg.subject == "Необходимо подтверждение адреса электронной почты"
        )

    async def test_create_not_unique_email(
        self,
        http_client: AsyncClient,
        user: User,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch(
            "utilies.email_client.EmailClient.send_mail",
            return_value=None,
        )
        data = UserCreate(
            nickname="Test Nickname Create",
            email="test1@gmail.com",
            password="msaldkfmqor13",
            role=UserRole.admin,
            phone="88005535",
        )
        response = await http_client.post(
            ROOT_ENDPOINT, json=data.model_dump()
        )
        response_data = response.json()
        assert response.status_code == 400
        assert (
            response_data["detail"]
            == "Пользователь с таким E-mail уже зарегистрирован!"
        )

    async def test_delete(
        self,
        http_client: AsyncClient,
        user: User,
        get_auth_headers: Callable,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch(
            "utilies.email_client.EmailClient.send_mail",
            return_value=None,
        )
        user_for_delete_headers = await get_auth_headers(user)
        response = await http_client.delete(
            ROOT_ENDPOINT, headers=user_for_delete_headers
        )
        assert response.status_code == 204

        endpoint = f"{ROOT_ENDPOINT}{user.uid}/"
        response = await http_client.get(
            endpoint, headers=user_for_delete_headers
        )
        assert response.status_code == 404

    async def test_update(
        self,
        http_client: AsyncClient,
        user: User,
        get_auth_headers: Callable,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch(
            "utilies.email_client.EmailClient.send_mail",
            return_value=None,
        )
        user_for_update_headers = await get_auth_headers(user)
        new_phone = "88005536"
        update_data = UserUpdate(
            phone=new_phone,
        )
        response = await http_client.patch(
            ROOT_ENDPOINT,
            json=update_data.model_dump(exclude_unset=True),
            headers=user_for_update_headers,
        )
        assert response.status_code == 200
        response_data = response.json()
        assert str(user.uid) == response_data["uid"]
        assert new_phone == response_data["phone"]

    async def test_update_non_existing_industry(
        self,
        http_client: AsyncClient,
        user: User,
        get_auth_headers: Callable,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch(
            "utilies.email_client.EmailClient.send_mail",
            return_value=None,
        )
        user_for_update_headers = await get_auth_headers(user)
        update_data = UserUpdate(
            industry_uid=uuid.uuid4(),
        )
        response = await http_client.patch(
            ROOT_ENDPOINT,
            json=update_data.model_dump(exclude_unset=True, mode="json"),
            headers=user_for_update_headers,
        )
        assert response.status_code == 404

    async def test_email_verification_code(
        self,
        http_client: AsyncClient,
        user: User,
        auth_headers: dict,
    ) -> None:
        endpoint = f"{ROOT_ENDPOINT}verifyemail/{user.uid}/{user.email_verification_code}/"  # noqa:E501
        response = await http_client.get(endpoint, headers=auth_headers)
        assert response.status_code == 200

    async def test_email_wrong_verification_code(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        endpoint = f"{ROOT_ENDPOINT}verifyemail/{uuid.uuid4()}/{uuid.uuid4()}/"  # noqa:E501
        response = await http_client.get(endpoint, headers=auth_headers)
        assert response.status_code == 404
