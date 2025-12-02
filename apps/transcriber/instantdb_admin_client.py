"""InstantDB Admin API client for Python.

This module provides a Python client for the InstantDB Admin API, offering functionality for
data operations, user management, and file storage.

Adapted from the official typescript InstantDB admin client (@instantdb/admin 0.14.19)
and the unofficial InstantDB Admin HTTP API documentation:
https://paper.dropbox.com/doc/Unofficial-Admin-HTTP-API--CZhqKIu6Vbgt3Slg~ChQSKygAg-k37TvkOqKJILYwwiesweU

The client provides three main components:
- InstantDBAdminAPI: The main client class for interacting with InstantDB
- Auth: Handles authentication operations
- Storage: Manages file storage operations

(written mostly by claude-3-5-sonnet-20241022 with gentle guidance by @aphexcx)
"""


from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, BinaryIO, Dict, List, Optional, Union

import aiohttp
from typing_extensions import TypedDict

# Version constants, used for API headers
# and corresponding to the InstantDB version this client is based off of
VERSION = "v0.17.31"
CORE_VERSION = "v0.17.31"

# ruff: noqa: UP006, UP007

@dataclass
class Step:
    """Base class for database operation steps."""

    def to_list(self) -> list[str | dict[str, Any]]:
        """Convert step to InstantDB transaction format."""
        raise NotImplementedError


@dataclass
class Update(Step):
    """Update or create an entity."""

    collection: str
    id: str
    data: dict[str, Any]

    def to_list(self) -> list[str | dict[str, Any]]:
        return ["update", self.collection, self.id, self.data]


@dataclass
class Merge(Step):
    """Merge partial data into an existing entity."""

    collection: str
    id: str
    data: dict[str, Any]

    def to_list(self) -> list[str | dict[str, Any]]:
        return ["merge", self.collection, self.id, self.data]


@dataclass
class Delete(Step):
    """Delete an entity."""

    collection: str
    id: str

    def to_list(self) -> list[str | dict[str, Any]]:
        return ["delete", self.collection, self.id]


@dataclass
class Link(Step):
    """Create links between entities."""

    collection: str
    id: str
    links: dict[str, str | list[str]]

    def to_list(self) -> list[str | dict[str, Any]]:
        return ["link", self.collection, self.id, self.links]


@dataclass
class Unlink(Step):
    """Remove links between entities."""

    collection: str
    id: str
    links: dict[str, str | list[str]]

    def to_list(self) -> list[str | dict[str, Any]]:
        return ["unlink", self.collection, self.id, self.links]


# Type definitions
class User(TypedDict):
    id: str
    email: str
    refresh_token: str


class CardinalityKind(Enum):
    ONE = "one"
    MANY = "many"


@dataclass
class DebugCheckResult:
    id: str
    entity: str
    record: Dict[str, Any]
    check: Any


@dataclass
class StorageFile:
    """Represents a file stored in InstantDB storage."""

    key: str
    name: str
    size: int
    etag: str
    last_modified: int


class Auth:
    """Handles authentication operations for InstantDB.

    Provides methods for user authentication, token management, and user operations.
    """

    def __init__(self, config: Dict[str, str], headers: Dict[str, str]):
        self.base_url = config["base_url"]
        self.app_id = config["app_id"]
        self.headers = headers

    async def generate_magic_code(self, email: str) -> Dict[str, str]:
        """Generate a magic code for the user with the given email.

        Useful for writing custom auth flows.

        Args:
            email (str): User's email address

        Returns:
            Dict[str, str]: Response containing the magic code

        Example:
            Generate and send magic code:
                code = await db.auth.generate_magic_code("user@example.com")
                # Send email to user with magic code

        Raises:
            Exception: If magic code generation fails

        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(f"{self.base_url}/admin/magic_code", json={"email": email}) as response:
                if response.status != 200:
                    raise Exception(f"Failed to generate magic code: {await response.text()}")
                return await response.json()

    async def create_token(self, email: str) -> str:
        """Create a login token for the user with the given email.

        Creates a new user if they don't exist. Useful for custom auth flows.

        Args:
            email (str): User's email address

        Returns:
            str: Authentication token

        Example:
            Create and return token:
                token = await db.auth.create_token("user@example.com")
                return {"token": token}

        Raises:
            Exception: If token creation fails

        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(
                    f"{self.base_url}/admin/refresh_tokens",
                    json={"email": email},
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to create token: {await response.text()}")
                data = await response.json()
                return data["user"]["refresh_token"]

    async def verify_token(self, token: str) -> User:
        """Verify a token and return the associated user.

        Useful for writing custom endpoints where you need to authenticate users.

        Args:
            token (str): Authentication token to verify

        Returns:
            User: User information if token is valid

        Example:
            Verify user token:
                user = await db.auth.verify_token(request.headers["token"])
                if not user:
                    return {"error": "Not authenticated"}

        Raises:
            Exception: If token verification fails

        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{self.base_url}/runtime/auth/verify_refresh_token",
                    json={"app-id": self.app_id, "refresh-token": token},
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to verify token: {await response.text()}")
                data = await response.json()
                return data["user"]

    async def get_user(self, **params: Dict[str, str]) -> User:
        """Retrieve a user by id, email, or refresh token.

        Args:
            **params: Keyword arguments to identify the user:
                email (str): User's email
                id (str): User's ID
                refresh_token (str): User's refresh token

        Returns:
            User: User information

        Example:
            Get user by email:
                user = await db.auth.get_user(email="user@example.com")
                print(f"Found user: {user}")

        Raises:
            Exception: If user retrieval fails

        """
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{self.base_url}/admin/users?{query_string}") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get user: {await response.text()}")
                data = await response.json()
                return data["user"]

    async def delete_user(self, **params: Dict[str, str]) -> User:
        """Delete a user by id, email, or refresh token.

        Note: This only deletes the user; it does not delete all user data.
        You will need to handle this manually.

        Args:
            **params: Keyword arguments to identify the user:
                email (str): User's email
                id (str): User's ID
                refresh_token (str): User's refresh token

        Returns:
            User: Deleted user information

        Example:
            Delete user by email:
                deleted_user = await db.auth.delete_user(email="user@example.com")
                print(f"Deleted user: {deleted_user}")

        Raises:
            Exception: If user deletion fails

        """
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.delete(f"{self.base_url}/admin/users?{query_string}") as response:
                if response.status != 200:
                    raise Exception(f"Failed to delete user: {await response.text()}")
                data = await response.json()
                return data["deleted"]

    async def sign_out(self, email: str) -> None:
        """Sign out a user and invalidate their tokens.

        Args:
            email (str): Email of the user to sign out

        Example:
            Sign out user:
                await db.auth.sign_out("user@example.com")
                print("Successfully signed out")

        Raises:
            Exception: If sign out fails or user not found

        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(f"{self.base_url}/admin/sign_out", json={"email": email}) as response:
                if response.status != 200:
                    raise Exception(f"Failed to sign out user: {await response.text()}")


class Storage:
    """Handles file storage operations for InstantDB."""

    def __init__(self, config: Dict[str, str], headers: Dict[str, str]):
        self.base_url = config["base_url"]
        self.app_id = config["app_id"]
        self.headers = headers

    async def uploadFile(
            self,
            pathname: str,
            file: Union[bytes, BinaryIO],
            options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Upload a file to InstantDB storage.

        Args:
            pathname (str): The path where the file will be stored
            file (Union[bytes, BinaryIO]): The file data as bytes or file-like object
            options (Optional[Dict[str, Any]], optional): Options for the upload
                - contentType: The content type of the file
                - contentDisposition: The content disposition header

        Returns:
            Dict[str, Any]: Upload result containing file ID and URL

        Example:
            Upload a file:
                with open("photo.jpg", "rb") as f:
                    result = await db.storage.uploadFile(
                        "photos/profile.jpg",
                        f,
                        {"contentType": "image/jpeg"}
                    )
                    print(f"File ID: {result['id']}")

        Raises:
            Exception: If upload fails

        """
        options = options or {}
        content_type = options.get("contentType", "application/octet-stream")

        # Prepare headers
        headers = {**self.headers, "path": pathname, "content-type": content_type}

        # Add content disposition if provided
        if "contentDisposition" in options:
            headers["content-disposition"] = options["contentDisposition"]

        # Prepare file data
        if isinstance(file, bytes):
            file_data = file
        else:
            file_data = file.read()

        # Direct upload to /admin/storage/upload
        async with aiohttp.ClientSession() as session:
            async with session.put(
                    f"{self.base_url}/admin/storage/upload",
                    data=file_data,
                    headers=headers,
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to upload file: {await response.text()}")

                try:
                    data = await response.json()
                    # Return the data as-is, which should have the format { data: { id: string } }
                    return data
                except Exception:
                    # If there's an error parsing the JSON, return a simplified response
                    return {"data": {"id": None}, "success": response.status == 200}

    async def upload(
            self,
            pathname: str,
            file: Union[bytes, BinaryIO],
            content_type: str = "application/octet-stream",
            metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Upload a file to InstantDB storage. (Deprecated)

        This method is deprecated. Use uploadFile instead.

        Args:
            pathname (str): The path where the file will be stored
            file (Union[bytes, BinaryIO]): The file data as bytes or file-like object
            content_type (str, optional): The content type of the file
            metadata (Optional[Dict[str, Any]], optional): Additional metadata for the file

        Returns:
            Dict[str, Any]: Upload result containing file ID and URL

        Raises:
            Exception: If upload fails

        """
        # Call the new uploadFile method
        return await self.uploadFile(
            pathname=pathname,
            file=file,
            options={"contentType": content_type, **(metadata or {})},
        )

    async def get_download_url(self, pathname: str) -> str:
        """Get a download URL for a file.

        Args:
            pathname (str): The path of the file

        Returns:
            str: The download URL

        Example:
            Get download URL for a file:
                url = await db.storage.get_download_url("photos/profile.jpg")
                print(f"Download URL: {url}")

        Raises:
            Exception: If getting download URL fails

        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(
                    f"{self.base_url}/admin/storage/signed-download-url",
                    params={"app_id": self.app_id, "filename": pathname},
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get download URL: {await response.text()}")
                data = await response.json()
                return data["data"]

    async def list(self) -> List[StorageFile]:
        """List all files in storage.

        Returns:
            List[StorageFile]: List of stored files

        Example:
            List all stored files:
                files = await db.storage.list()
                for file in files:
                    print(f"File: {file.name}, Size: {file.size}")

        Raises:
            Exception: If listing files fails

        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{self.base_url}/admin/storage/files", headers=self.headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to list files: {await response.text()}")
                data = await response.json()
                return [StorageFile(**file) for file in data["data"]]

    async def delete(self, pathname: str) -> None:
        """Delete a file from storage.

        Args:
            pathname (str): The path of the file to delete

        Example:
            Delete a file:
                await db.storage.delete("photos/old-profile.jpg")

        Raises:
            Exception: If file deletion fails

        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.delete(
                    f"{self.base_url}/admin/storage/files",
                    params={"filename": pathname},
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to delete file: {await response.text()}")

    async def delete_many(self, pathnames: List[str]) -> None:
        """Delete multiple files from storage.

        Args:
            pathnames (List[str]): List of file paths to delete

        Example:
            Delete multiple files:
                await db.storage.delete_many([
                    "photos/1.jpg",
                    "photos/2.jpg",
                    "photos/3.jpg"
                ])

        Raises:
            Exception: If deleting files fails

        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(
                    f"{self.base_url}/admin/storage/files/delete",
                    json={"filenames": pathnames},
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to delete files: {await response.text()}")


class InstantDBAdminAPI:
    """InstantDB Admin API client for Python.

    A client for interacting with InstantDB's admin API, providing functionality for
    data operations, user management, and file storage.

    Args:
        app_id (str): Your InstantDB application ID
        admin_token (str): Your InstantDB admin token
        base_url (str, optional): InstantDB API base URL. Defaults to "https://api.instantdb.com"

    Example:
        Initialize the client and query data:
        client = InstantDBAdminAPI(app_id="your-app-id", admin_token="your-token")
        result = await client.query({"users": {}})

    """

    def __init__(self, app_id: str, admin_token: str, base_url: str = "https://api.instantdb.com"):
        self.config = {"app_id": app_id, "base_url": base_url}
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {admin_token}",
            "App-Id": app_id,
            "Instant-Admin-Version": VERSION,
            "Instant-Core-Version": CORE_VERSION,
        }

        # Initialize components
        self.auth = Auth(self.config, self.headers)
        self.storage = Storage(self.config, self.headers)
        self._impersonation_opts: Optional[Dict[str, Any]] = None

    def as_user(self, **opts: Dict[str, Any]) -> InstantDBAdminAPI:
        """Create a new client instance that makes requests on behalf of a user.

        Sometimes you want to scope queries to a specific user. You can provide a user's
        auth token, email, or impersonate a guest.

        Args:
            **opts: Keyword arguments for user impersonation:
                email (str): Email of the user to impersonate
                token (str): Auth token of the user to impersonate
                guest (bool): True to impersonate a guest user

        Returns:
            InstantDBAdminAPI: A new client instance with user impersonation

        Example:
            Query data as a specific user:
                user_client = client.as_user(email="user@example.com")
                result = await user_client.query({"goals": {}})

        """
        new_client = InstantDBAdminAPI(
            self.config["app_id"],
            self.headers["Authorization"].split(" ")[1],
            self.config["base_url"],
        )
        new_client._impersonation_opts = opts
        new_client._update_headers_with_impersonation()
        return new_client

    def _update_headers_with_impersonation(self) -> None:
        """Update headers with impersonation options."""
        if not self._impersonation_opts:
            return

        if "email" in self._impersonation_opts:
            self.headers["as-email"] = self._impersonation_opts["email"]
        elif "token" in self._impersonation_opts:
            self.headers["as-token"] = self._impersonation_opts["token"]
        elif "guest" in self._impersonation_opts:
            self.headers["as-guest"] = "true"

    async def query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an InstaQL query to fetch data.

        Use this to query your data using InstantDB's InstaQL query language.

        Args:
            query (Dict[str, Any]): The InstaQL query object

        Returns:
            Dict[str, Any]: Query results

        Example:
            Fetch all goals:
                await db.query({"goals": {}})

            Goals where title is "Get Fit":
                await db.query({
                    "goals": {
                        "$": {
                            "where": {"title": "Get Fit"}
                        }
                    }
                })

            All goals alongside their todos:
                await db.query({"goals": {"todos": {}}})

        Raises:
            Exception: If the query fails

        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(
                    f"{self.config['base_url']}/admin/query",
                    json={"query": query},
            ) as response:
                if response.status != 200:
                    raise Exception(f"Query failed: {await response.text()}")
                return await response.json()

    async def debug_query(
            self,
            query: Dict[str, Any],
            rules: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a query with debug information about permissions.

        Like query(), but returns debugging information for permissions checks.
        Useful for inspecting the values returned by permissions checks.

        Args:
            query (Dict[str, Any]): The InstaQL query object
            rules (Optional[Dict[str, Any]]): Optional rules override

        Returns:
            Dict[str, Any]: Query results and debug information

        Example:
            Debug query with custom rules:
                result = await db.as_user(guest=True).debug_query(
                    {"goals": {}},
                    rules={"goals": {"allow": {"read": "auth.id != null"}}}
                )

        Raises:
            Exception: If the debug query fails

        """
        async with aiohttp.ClientSession(headers=self.headers) as session, session.post(
                f"{self.config['base_url']}/admin/query_perms_check",
                json={"query": query, "rules-override": rules},
        ) as response:
            if response.status != 200:
                raise Exception(f"Debug query failed: {await response.text()}")
            data = await response.json()
            return {
                "result": data["result"],
                "checkResults": [DebugCheckResult(**r) for r in data["check-results"]],
            }

    async def transact(self, steps: list[Step]) -> dict[str, Any]:
        """Execute a transaction using type-safe Step objects.

        Args:
            steps: List of Step objects representing database operations

        Returns:
            dict[str, Any]: Transaction results

        Example:
            Create and link objects:
                await db.transact([
                    Update(
                        collection="todos",
                        id="todo-123",
                        data={"title": "Go running"}
                    ),
                    Link(
                        collection="goals",
                        id="goal-123",
                        links={"todos": "todo-123"}
                    )
                ])

        Raises:
            Exception: If the transaction fails

        """
        # Convert Step objects to lists
        step_lists = [step.to_list() for step in steps]

        async with aiohttp.ClientSession(headers=self.headers) as session, session.post(
                f"{self.config['base_url']}/admin/transact",
                json={"steps": step_lists},
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Transaction failed: {error_text}")
            return await response.json()

    async def debug_transact(
            self,
            steps: List[List[Any]],
            rules: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a transaction with debug information about permissions.

        Like transact(), but does not write to the database and returns
        debugging information for permissions checks.

        Args:
            steps (List[List[Any]]): List of transaction steps
            rules (Optional[Dict[str, Any]]): Optional rules override

        Returns:
            Dict[str, Any]: Debug information about permissions checks

        Example:
            Debug transaction as a guest user:
                result = await db.as_user(guest=True).debug_transact([
                    ["update", "goals", "goal-123", {"title": "Get fit"}]
                ])

        Raises:
            Exception: If the debug transaction fails

        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(
                    f"{self.config['base_url']}/admin/transact_perms_check",
                    json={"steps": steps, "rules-override": rules},
            ) as response:
                if response.status != 200:
                    raise Exception(f"Debug transaction failed: {await response.text()}")
                return await response.json()
