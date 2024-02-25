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


def load_env():
    load_dotenv()

    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")

    if not CLIENT_ID or not CLIENT_SECRET:
        logging.error("Please set the CLIENT_ID and CLIENT_SECRET in .env")
        exit(1)

    return CLIENT_ID, CLIENT_SECRET


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Load environment variables from .env file
    load_dotenv()

    CLIENT_ID, CLIENT_SECRET = load_env()

    pluggy = Pluggy(CLIENT_ID, CLIENT_SECRET)
    api_key = pluggy.generate_api_key()
    logging.info(f"API Key: {api_key}")
