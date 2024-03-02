from dotenv import load_dotenv

import logging
import os
import pluggy_lib

API_URL = "https://api.pluggy.ai"

ACCEPT_JSON_RESPONSE = {
    "accept": "application/json",
    "content-type": "application/json",
}

def get_client_info() -> None:
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("ClientID or ClientSecret not found.")
    return client_id, client_secret


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    load_dotenv()

    try:
        client_id, client_secret = get_client_info()
    except RuntimeError:
        logging.error("Please set the CLIENT_ID and CLIENT_SECRET in .env")
        exit(1)

    pluggy = pluggy_lib.PluggyConnector(client_id, client_secret, API_URL)

    try: 
        api_key = pluggy.generate_api_key(ACCEPT_JSON_RESPONSE)
        logging.info(f"API Key: {api_key}")
    except pluggy_lib.ConnectionError as e:
        logger.error(f"An error occurred: {e}")

