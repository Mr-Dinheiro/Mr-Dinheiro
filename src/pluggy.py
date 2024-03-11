import time
from typing import Tuple
from dotenv import load_dotenv

import logging
import os
import facade
from status import ItemStatus


def get_client_info() -> Tuple[str, str]:
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

    pluggy = facade.PluggyFacade(client_id, client_secret)

    api_key = pluggy.api.generate_api_key()
    credentials = {
        "cpf": os.getenv("CPF"),
    }
    connector = pluggy.get_connector_details(connector_name="nubank", open_finance=True)
    logger.info("Creating item")

    item = pluggy.create_item_detail(
        credentials, connector_name="nubank", open_finance=True
    )

    item_id = item.get("id", "")
    status = item.get("status")

    # TODO: moving this to a webhook is a much better idea
    logger.info("Waiting for item to be updated.")
    while True:
        item = pluggy.get_item_detail(item_id)
        status = item.get("status")
        logging.info(f"Item id: {item_id}")
        logging.info(f"Item status: {status}")

        if status == ItemStatus.WAITING_USER_INPUT.name:
            oauth_url = item.get("parameter", {}).get("data")
            instructions = item.get("parameter", {}).get("instructions")
            logger.info(f"Instructions: {instructions}")
            if oauth_url:
                logger.info(oauth_url)

        if status == ItemStatus.UPDATED.name:
            logger.info("Completed!")
            break

        if status == ItemStatus.LOGIN_ERROR.name:
            # Connection must be updated again
            logger.error(f"{ItemStatus.LOGIN_ERROR.value}")
            pluggy.update_item_detail(item_id=item_id, credentials=credentials)

        if status == ItemStatus.OUTDATED.name:
            # Connection must be updated again
            logger.error("Connection must be updated again")
            pluggy.update_item_detail(item_id=item_id, credentials=credentials)
        else:
            logger.info("Waiting for item to be updated.")
            time.sleep(5)

    logger.info(f"Item created with ID: {item_id}")

    accounts = pluggy.get_account_list(item_id)

    credit_card_account = pluggy.find_attr(accounts, "type", "credit")

    if not credit_card_account:
        logging.error("No credit card account found.")
        exit(1)
    credit_card_account_id = credit_card_account.get("id")

    transactions = pluggy.get_all_transactions(credit_card_account_id)

    pluggy.data_handler.save_transactions_as(
        transactions,
        format="csv",
        file_path="../experimental/nubank_credit_card/last_year_transactions",
    )
