import uuid
from typing import Callable, List

from httpx import AsyncClient
from pytest_mock import MockerFixture

from constants.comment import COMMENTS_NESTING_MAX_DEPTH
from models.comment import JobComment
from models.job import Job
from models.user import User
from schemas.comment import JobCommentCreate, JobCommentUpdate

ROOT_ENDPOINT = "/check-point/api/v1/comment/"


class TestJobCommentApi:
    async def test_get_list(
        self,
        http_client: AsyncClient,
        job: Job,
        auth_headers: dict,
    ):
        endpoint = f"{ROOT_ENDPOINT}job/{job.uid}/"
        response = await http_client.get(endpoint, headers=auth_headers)

        assert response.status_code == 200
        assert isinstance(response.json(), List)

    async def test_get_retrieve(
        self,
        http_client: AsyncClient,
        job_comment: JobComment,
        auth_headers: dict,
    ):
        endpoint = f"{ROOT_ENDPOINT}{job_comment.uid}/"
        response = await http_client.get(endpoint, headers=auth_headers)
        assert response.status_code == 200

    async def test_create(
        self,
        http_client: AsyncClient,
        job: Job,
        auth_headers: dict,
        user: User,
        mocker: MockerFixture,
    ):
        mocker_send_notification = mocker.patch(
            "notifications.ws_manager.WebSocketManager.send_to_user",
            return_value=None,
        )
        data = JobCommentCreate(
            text="Creation test",
            job_uid=job.uid,
            author_uid=user.uid,
        )
        response = await http_client.post(
            ROOT_ENDPOINT,
            headers=auth_headers,
            json=data.model_dump(mode="json"),
        )
        assert response.status_code == 201
        assert mocker_send_notification.call_count == 1
        arg = mocker_send_notification.call_args[1]["message"]["message"]
        assert arg == "New notification"

    async def test_update(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
        job_comment: JobComment,
        mocker: MockerFixture,
    ):
        mocker_send_notification = mocker.patch(
            "notifications.ws_manager.WebSocketManager.send_to_user",
            return_value=None,
        )
        data = JobCommentUpdate(text="Update test")
        endpoint = f"{ROOT_ENDPOINT}{job_comment.uid}/"
        response = await http_client.patch(
            endpoint,
            json=data.model_dump(),
            headers=auth_headers,
        )
        assert response.status_code == 200
        response_data = response.json()
        assert data.text == response_data["text"]
        assert str(job_comment.uid) == response_data["uid"]
        assert mocker_send_notification.call_count == 1
        arg = mocker_send_notification.call_args[1]["message"]["message"]
        assert arg == "New notification"

    async def test_delete(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
        job_comment: JobComment,
    ):
        endpoint = f"{ROOT_ENDPOINT}{job_comment.uid}/"
        response = await http_client.delete(endpoint, headers=auth_headers)
        assert response.status_code == 204

        response = await http_client.get(endpoint, headers=auth_headers)
        assert response.status_code == 404

    async def test_get_retrieve_with_invalid_uid(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
    ):
        endpoint = f"{ROOT_ENDPOINT}{uuid.uuid4()}/"
        response = await http_client.get(endpoint, headers=auth_headers)
        assert response.status_code == 404

    async def test_create_with_invalid_job(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
        user: User,
    ):
        data = JobCommentCreate(
            text="Creation test",
            job_uid=uuid.uuid4(),
            author_uid=user.uid,
        )
        response = await http_client.post(
            ROOT_ENDPOINT,
            headers=auth_headers,
            json=data.model_dump(mode="json"),
        )
        assert response.status_code == 404

    async def test_create_nested_comments_above_limit(
        self,
        http_client: AsyncClient,
        job: Job,
        auth_headers: dict,
        user: User,
        mocker: MockerFixture,
    ):
        mocker.patch(
            "notifications.ws_manager.WebSocketManager.send_to_user",
            return_value=None,
        )
        parent_uid = None
        for i in range(COMMENTS_NESTING_MAX_DEPTH + 1):
            comment = JobCommentCreate(
                text=f"Create comment {i + 1}",
                parent_uid=parent_uid,
                job_uid=job.uid,
                author_uid=user.uid,
            )
            response = await http_client.post(
                ROOT_ENDPOINT,
                headers=auth_headers,
                json=comment.model_dump(mode="json"),
            )
            if i == COMMENTS_NESTING_MAX_DEPTH:
                assert response.status_code == 400
            else:
                assert response.status_code == 201
                response_data = response.json()
                parent_uid = response_data["uid"]

    async def test_update_by_not_author(
        self,
        http_client: AsyncClient,
        get_auth_headers: Callable,
        another_user: User,
        job_comment: JobComment,
    ):
        data = JobCommentUpdate(text="Update test")
        endpoint = f"{ROOT_ENDPOINT}{job_comment.uid}/"
        user_headers = await get_auth_headers(another_user)
        response = await http_client.patch(
            endpoint,
            json=data.model_dump(),
            headers=user_headers,
        )
        assert response.status_code == 403

    async def test_update_with_invalid_uid(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
    ):
        data = JobCommentUpdate(text="Update test")
        endpoint = f"{ROOT_ENDPOINT}{uuid.uuid4()}/"
        response = await http_client.patch(
            endpoint,
            json=data.model_dump(),
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_add_remove_like(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
        job_comment: JobComment,
        mocker: MockerFixture,
    ):
        mocker_send_notification = mocker.patch(
            "notifications.ws_manager.WebSocketManager.send_to_user",
            return_value=None,
        )
        endpoint = f"{ROOT_ENDPOINT}add_like/{job_comment.uid}/"
        response = await http_client.post(
            endpoint,
            headers=auth_headers,
        )
        response_data = response.json()
        assert response.status_code == 200
        assert response_data["users_likes"] != []
        assert mocker_send_notification.call_count == 1
        arg = mocker_send_notification.call_args[1]["message"]["message"]
        assert arg == "New notification"

        endpoint2 = f"{ROOT_ENDPOINT}remove_like/{job_comment.uid}/"
        response2 = await http_client.post(
            endpoint2,
            headers=auth_headers,
        )
        response_data2 = response2.json()
        assert response2.status_code == 200
        assert response_data2["users_likes"] == []

    async def test_add_like_to_invalid_comment(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
    ):
        endpoint = f"{ROOT_ENDPOINT}add_like/{uuid.uuid4()}/"
        response = await http_client.post(
            endpoint,
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_remove_like_from_invalid_comment(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
    ):
        endpoint = f"{ROOT_ENDPOINT}remove_like/{uuid.uuid4()}/"
        response = await http_client.post(
            endpoint,
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_delete_with_invalid_uid(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
    ):
        endpoint = f"{ROOT_ENDPOINT}{uuid.uuid4()}/"
        response = await http_client.delete(endpoint, headers=auth_headers)
        assert response.status_code == 404
