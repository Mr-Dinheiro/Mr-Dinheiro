import requests
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

class Pluggy:
    API_URL = "https://api.pluggy.ai"
    ACCEPT_JSON_RESPONSE = {
        "accept": "application/json",
        "content-type": "application/json",
    }

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def call_api_endpoint(self, payload, endpoint, headers=ACCEPT_JSON_RESPONSE):
        url_to_call = f"{self.API_URL}/{endpoint}"

        try:
            response = requests.post(url_to_call, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except (RequestException, HTTPError, ConnectionError, Timeout) as e:
            logger.error(f"An error occurred: {e}")
            return None

    def generate_api_key(self):
        try:
            payload = {"clientId": self.client_id, "clientSecret": self.client_secret}
            response_json = self.call_api_endpoint(payload, "auth")
            return response_json.get("apiKey")
        except (RequestException, HTTPError, ConnectionError, Timeout) as e:
            logger.error(f"An error occurred: {e}")
            return None


def get_client_info():
    load_dotenv()

    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    if not client_id or not client_secret:
        logging.error("Please set the CLIENT_ID and CLIENT_SECRET in .env")
        exit(1)

    return client_id, client_secret


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Load environment variables from .env file
    load_dotenv()

    client_id, client_secret = get_client_info()

    pluggy = Pluggy(client_id, client_secret)
    api_key = pluggy.generate_api_key()
    logging.info(f"API Key: {api_key}")
