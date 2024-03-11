import requests
from requests import exceptions
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ACCEPT_JSON_RESPONSE_HEADER = {
    "accept": "application/json",
    "content-type": "application/json",
}


class PluggyApi:
    API_KEY_EXPIRE_HOURS = 2

    def __init__(self, client_id: str, client_secret: str, api_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = api_url
        self._api_key, self._api_key_last_updated = self.load_cached_api_key()
        self._connectors: dict | None = None

    def cache_api_key(self):
        data = {
            "api_key": self._api_key,
            "api_key_last_updated": self._api_key_last_updated.isoformat(),
        }
        with open("api_key.json", "w") as f:
            json.dump(data, f)

    def load_cached_api_key(self):
        if not Path("api_key.json").is_file():
            logger.info("No cached API key found.")
            return None, None

        with open("api_key.json", "r") as f:
            data = json.load(f)
            return data.get("api_key"), datetime.fromisoformat(
                data.get("api_key_last_updated")
            )

    @property
    def headers(self):
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

    def request_new_api_key(self):
        payload = {"clientId": self.client_id, "clientSecret": self.client_secret}
        response_json = self._call_api("POST", "auth", payload)
        self._api_key = response_json.get("apiKey")
        self._api_key_last_updated = datetime.now()
        self.cache_api_key()

    def get(
        self,
        endpoint: str,
        query_params: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
        return self._call_api(
            "GET", endpoint=endpoint, query_params=query_params, headers=headers
        )

    def post(
        self,
        endpoint: str,
        payload: dict | None = None,
        query_params: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
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
        payload: dict | None = None,
        query_params: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
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
        payload: dict | None = None,
        query_params: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
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
        payload: dict | None = None,
        query_params: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
        return self._call_api(
            "DELETE",
            endpoint=endpoint,
            payload=payload,
            query_params=query_params,
            headers=headers,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def _call_api(
        self,
        method: str,
        endpoint: str,
        payload: dict | None = None,
        query_params: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
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
            response_json = response.json()
            if response.status_code != 200:
                message = response_json.get("message", "")
                logger.error(
                    f"Error calling API endpoint {endpoint}: {response.status_code} - {message}"
                )
                raise exceptions.HTTPError(
                    f"Error calling API endpoint {endpoint}: {response.status_code} - {message}"
                )
            response.raise_for_status()
            return response_json
        except exceptions.Timeout as e:
            logger.error(f"Timeout error calling API endpoint: {e}")
            raise e
        except (exceptions.RequestException, exceptions.HTTPError) as e:
            logger.error(f"Error calling API endpoint: {e}")
            raise e
