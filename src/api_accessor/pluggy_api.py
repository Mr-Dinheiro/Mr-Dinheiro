import requests
from requests import JSONDecodeError, exceptions
from datetime import datetime, timedelta
import json
from pathlib import Path
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
from typing import Any
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ACCEPT_JSON_RESPONSE_HEADER = {
    "accept": "application/json",
    "content-type": "application/json",
}


class PluggyApi:
    API_KEY_EXPIRE_HOURS: int = 2

    def __init__(self, client_id: str, client_secret: str, api_url: str) -> None:
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.api_url: str = api_url
        self._api_key: str | None
        self._api_key_last_updated: datetime | None
        self._api_key, self._api_key_last_updated = self.load_cached_api_key()

    def cache_api_key(self) -> None:
        data = {
            "api_key": self._api_key,
            "api_key_last_updated": (
                self._api_key_last_updated.isoformat()
                if self._api_key_last_updated
                else None
            ),
        }
        with open("api_key.json", "w") as f:
            json.dump(data, f)

    def load_cached_api_key(self) -> tuple[str | None, datetime | None]:
        if not Path("api_key.json").is_file():
            logger.info("No cached API key found.")
            return None, None

        with open("api_key.json", "r") as f:
            data = json.load(f)
            return data.get("api_key"), datetime.fromisoformat(
                data.get("api_key_last_updated")
            )

    @property
    def headers(self) -> dict[str, str]:
        return (
            {"X-API-KEY": self._api_key, **ACCEPT_JSON_RESPONSE_HEADER}
            if self._api_key
            else ACCEPT_JSON_RESPONSE_HEADER
        )

    def generate_api_key(self) -> str | None:
        if self._api_key_last_updated and abs(
            datetime.now() - self._api_key_last_updated
        ) > timedelta(hours=self.API_KEY_EXPIRE_HOURS):
            logger.debug("API Key expired. Generating a new one.")
            self.request_new_api_key()

        if not self._api_key:
            logger.debug("Generating API Key for the first time.")
            self.request_new_api_key()

        logger.debug(f"API Key: {self._api_key}")
        return self._api_key

    def request_new_api_key(self) -> None:
        payload = {"clientId": self.client_id, "clientSecret": self.client_secret}
        response_json, return_code = self._call_api("POST", "auth", payload)
        self._api_key = response_json.get("apiKey")
        self._api_key_last_updated = datetime.now()
        self.cache_api_key()

    def get(
        self,
        endpoint: str,
        query_params: dict[Any, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[dict[Any, Any], int]:
        return self._call_api(
            "GET", endpoint=endpoint, query_params=query_params, headers=headers
        )

    def post(
        self,
        endpoint: str,
        payload: dict[Any, Any] | None = None,
        query_params: dict[Any, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[dict[Any, Any], int]:
        return self._call_api(
            "POST",
            endpoint=endpoint,
            payload=payload,
            query_params=query_params,
            headers=headers,
        )

    def patch(
        self,
        endpoint: str,
        payload: dict[Any, Any] | None = None,
        query_params: dict[Any, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[dict[Any, Any], int]:
        return self._call_api(
            "PATCH",
            endpoint=endpoint,
            payload=payload,
            query_params=query_params,
            headers=headers,
        )

    def put(
        self,
        endpoint: str,
        payload: dict[Any, Any] | None = None,
        query_params: dict[Any, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[dict[Any, Any], int]:
        return self._call_api(
            "PUT",
            endpoint=endpoint,
            payload=payload,
            query_params=query_params,
            headers=headers,
        )

    def delete(
        self,
        endpoint: str,
        payload: dict[Any, Any] | None = None,
        query_params: dict[Any, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[dict[Any, Any], int]:
        return self._call_api(
            "DELETE",
            endpoint=endpoint,
            payload=payload,
            query_params=query_params,
            headers=headers,
        )

    @retry(  # type: ignore
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(exceptions.Timeout),
    )
    def _call_api(
        self,
        method: str,
        endpoint: str,
        payload: dict[Any, Any] | None = None,
        query_params: dict[Any, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[dict[Any, Any], int]:
        url_to_call = f"{self.api_url}/{endpoint}"
        default_timeout = 30

        if headers is None:
            headers = {}

        logger.debug(f"calling API endpoint: {url_to_call}")
        logger.debug(f"method: {method}")
        logger.debug(f"payload: {payload}")
        logger.debug(f"query parameters: {query_params}")
        logger.debug(f"headers: {headers}")

        try:
            response = requests.request(
                method,
                url_to_call,
                json=payload,
                headers={**self.headers, **headers},
                timeout=default_timeout,
                params=query_params,
            )
            try:
                response_json = response.json()
            except JSONDecodeError:
                logger.error("Error decoding JSON response")
                response_json = {}

            if response.status_code != 200:
                message = response_json.get("message", "")
                logger.error(
                    f"Error calling API endpoint {endpoint}: {response.status_code} - {message}"
                )
                raise exceptions.HTTPError(
                    f"Error calling API endpoint {endpoint}: {response.status_code} - {message}"
                )

            response.raise_for_status()
            if isinstance(response_json, dict):
                return response_json, response.status_code
            logger.error(
                f"JSON response of unexpected type: {type(response_json)}, response: {response_json}",
            )
            return {}, response.status_code
        except exceptions.Timeout as e:
            logger.error(f"Timeout error calling API endpoint: {e}")
            raise e
        except (exceptions.RequestException, exceptions.HTTPError) as e:
            logger.error(f"Error calling API endpoint: {e}")
            raise e
