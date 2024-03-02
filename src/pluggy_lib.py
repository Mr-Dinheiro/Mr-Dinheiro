import requests

from requests import exceptions


class ConnectionError(Exception):
    "The connection failed."


class PluggyConnector:

    def __init__(self, client_id: str, client_secret: str, api_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = api_url

    def _call_api_endpoint(self, payload: str, endpoint: str, headers: str) -> None:
        url_to_call = f"{self.api_url}/{endpoint}"

        try:
            response = requests.post(url_to_call, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except (exceptions.RequestException, exceptions.HTTPError, exceptions.Timeout):
            raise ConnectionError("Error calling API endpoint.")

    def generate_api_key(self, headers: str) -> str:
        try:
            payload = {"clientId": self.client_id, "clientSecret": self.client_secret}
            response_json = self._call_api_endpoint(payload, "auth", headers)
            return response_json.get("apiKey")
        except ConnectionError as e:
            raise e
            