import uuid
from typing import Callable, Dict

from httpx import AsyncClient

from crud.folders import folders as crud_folders
from databases.database import get_async_session
from models.account import Account
from models.folder import Folder
from schemas.folder import FolderCreate, FolderCreateDB, FolderUpdate

ROOT_ENDPOINT = "/check-point/api/v1/folders/"


class TestFolderApi:
    async def test_get_list(
        self,
        account: Account,
        http_client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        async for session in get_async_session():
            await crud_folders.create(
                session,
                obj_in=FolderCreateDB(
                    name="root",
                    order=0,
                    account_id=account.id,
                    is_root=True,
                ),
            )
        endpoint = f"{ROOT_ENDPOINT}{account.uid}/"
        response = await http_client.get(endpoint, headers=auth_headers)
        response_data = response.json()
        assert response.status_code == 200
        assert isinstance(response_data, Dict)

    async def test_get_list_by_non_existent_account(
        self,
        http_client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        endpoint = f"{ROOT_ENDPOINT}{uuid.uuid4()}/"
        response = await http_client.get(endpoint, headers=auth_headers)
        assert response.status_code == 404

    async def test_create(
        self,
        account: Account,
        folder: Folder,
        get_auth_headers: Callable,
        http_client: AsyncClient,
    ) -> None:
        data = FolderCreate(
            name="TestNameCreate",
            parent_uid=folder.uid,
            account_uid=account.uid,
        )
        user_headers = await get_auth_headers(account.user)
        response = await http_client.post(
            ROOT_ENDPOINT,
            headers=user_headers,
            json=data.model_dump(mode="json"),
        )
        response_data = response.json()
        assert response.status_code == 201
        assert data.name == response_data["name"]

    async def test_create_with_non_existent_parent(
        self,
        account: Account,
        get_auth_headers: Callable,
        http_client: AsyncClient,
    ) -> None:
        data = FolderCreate(
            name="TestNameCreate",
            parent_uid=uuid.uuid4(),
            account_uid=account.uid,
        )
        user_headers = await get_auth_headers(account.user)
        response = await http_client.post(
            ROOT_ENDPOINT,
            headers=user_headers,
            json=data.model_dump(mode="json"),
        )
        assert response.status_code == 404

    async def test_create_by_non_existent_account(
        self,
        account: Account,
        folder: Folder,
        get_auth_headers: Callable,
        http_client: AsyncClient,
    ) -> None:
        data = FolderCreate(
            name="TestNameCreate",
            parent_uid=folder.uid,
            account_uid=uuid.uuid4(),
        )
        user_headers = await get_auth_headers(account.user)
        response = await http_client.post(
            ROOT_ENDPOINT,
            headers=user_headers,
            json=data.model_dump(mode="json"),
        )
        assert response.status_code == 404

    async def test_update(
        self,
        http_client: AsyncClient,
        account: Account,
        folder: Folder,
        get_auth_headers: Callable,
    ) -> None:
        user_headers = await get_auth_headers(account.user)
        new_name = "TestUpdateName"
        update_data = FolderUpdate(
            name=new_name,
        )
        endpoint = f"{ROOT_ENDPOINT}{folder.uid}/"
        response = await http_client.patch(
            endpoint,
            json=update_data.model_dump(exclude_unset=True),
            headers=user_headers,
        )
        assert response.status_code == 200
        response_data = response.json()
        assert str(folder.uid) == response_data["uid"]
        assert new_name == response_data["name"]

    async def test_update_with_non_existent_parent(
        self,
        http_client: AsyncClient,
        account: Account,
        folder: Folder,
        get_auth_headers: Callable,
    ) -> None:
        user_headers = await get_auth_headers(account.user)
        update_data = FolderUpdate(
            name="TestUpdateName",
            parent_uid=uuid.uuid4(),
        )
        endpoint = f"{ROOT_ENDPOINT}{folder.uid}/"
        response = await http_client.patch(
            endpoint,
            json=update_data.model_dump(exclude_unset=True, mode="json"),
            headers=user_headers,
        )
        assert response.status_code == 404

    async def test_update_non_existent_folder(
        self,
        http_client: AsyncClient,
        account: Account,
        get_auth_headers: Callable,
    ) -> None:
        user_headers = await get_auth_headers(account.user)
        update_data = FolderUpdate(
            name="TestUpdateName",
        )
        folder_uid = uuid.uuid4()
        endpoint = f"{ROOT_ENDPOINT}{folder_uid}/"
        response = await http_client.patch(
            endpoint,
            json=update_data.model_dump(exclude_unset=True, mode="json"),
            headers=user_headers,
        )
        assert response.status_code == 404

    async def test_delete(
        self,
        http_client: AsyncClient,
        account: Account,
        folder: Folder,
        get_auth_headers: Callable,
    ) -> None:
        user_headers = await get_auth_headers(account.user)
        endpoint = f"{ROOT_ENDPOINT}{folder.uid}/"
        response = await http_client.delete(endpoint, headers=user_headers)
        assert response.status_code == 204

        endpoint = f"{ROOT_ENDPOINT}{folder.uid}/"
        response = await http_client.get(endpoint, headers=user_headers)
        assert response.status_code == 404
