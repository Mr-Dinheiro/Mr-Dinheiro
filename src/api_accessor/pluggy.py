import time
from typing import Tuple
from dotenv import load_dotenv

import logging
import os
import facade
from status import ItemStatus, TransientExecutionStatus


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
    connector = pluggy.fetch_and_find_connector(
        connector_name="nubank", open_finance=True
    )

    logger.info("Creating item")
    item = pluggy.create_item_detail(
        credentials, connector=connector, open_finance=True
    )
    item_id = item.get("id", "")
    status = item.get("status", "")

    # TODO: moving this to a webhook is a much better idea
    logger.info("Waiting for item to be updated.")
    while True:
        item = pluggy.get_item_detail(item_id)
        status = item.get("status", "")
        execution_status = item.get("executionStatus")

        logging.info(f"Item id: {item_id}")
        logging.info(f"Item status: {status}")
        logging.info(f"Execution status: {execution_status}")

        if execution_status.upper() in TransientExecutionStatus:
            logger.info(getattr(TransientExecutionStatus, execution_status.upper()))

        match status:
            case ItemStatus.WAITING_USER_INPUT.name:
                # This here is a good candidate for a webhook, we need to wait for the user to input the MFA
                # When a success happens, we can then have access to the transactions, bank_info and save them
                oauth_url = item.get("parameter", {}).get("data")
                instructions = item.get("parameter", {}).get("instructions")

                logger.info(f"Instructions: {instructions}")

                if oauth_url:
                    logger.info(oauth_url)

                input("Press Enter to continue...")
            case ItemStatus.UPDATED.name:
                logger.info("Completed!")
                break
            case ItemStatus.LOGIN_ERROR.name | ItemStatus.OUTDATED.name:
                logger.error(f"{ItemStatus[status].value}")
                logger.info("Updating item and retrying...")
                pluggy.update_item_detail(item_id, credentials, connector)
                input("Press Enter to continue...")
            case _:
                logger.info("Waiting for item to be updated.")
                time.sleep(5)
    logger.info(f"Item created with ID: {item_id}")

    accounts = pluggy.get_account_list(item_id)
    credit_card_account = pluggy._find_attribute(accounts, "type", "credit")
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
