from data_handler import PluggyDataHandler
from pluggy_lib import PluggyApi
import re


class ConnectionError(Exception):
    "The connection failed."


class InvalidCredentialError(Exception):
    pass


class MissingCredentialError(Exception):
    pass


API_URL = "https://api.pluggy.ai"


class PluggyFacade:
    def __init__(self, client_id: str, client_secret: str, api_url: str = API_URL):
        self.api = PluggyApi(client_id, client_secret, api_url)
        self.data_handler = PluggyDataHandler()

    def get_all_transactions(
        self, account_id, from_date=None, to_date=None, page_size=280
    ):
        """Get all transactions for a given account. Max 365 days.

        We use a greater page size to reduce the number of requests to the API.
        """
        page = 1
        all_transactions = []
        total_pages = None

        while total_pages is None or page <= total_pages:
            response = self.get_transaction_list(
                account_id, from_date, to_date, page_size, page
            )
            transactions = response.get("results", [])
            total_pages = response.get("totalPages")

            if not transactions:
                break

            all_transactions.extend(transactions)
            page += 1

        return all_transactions

    def get_transaction_list(
        self, account_id: str, from_date=None, to_date=None, page_size=20, page=1
    ) -> dict:
        if not account_id:
            raise ValueError("Account Id is needed to request transactions")

        endpoint = "transactions"

        query_params = {
            "accountId": f"{account_id}",
            "from": from_date,
            "to": to_date,
            "pageSize": page_size,
            "page": page,
        }

        query_params = {
            key: value for key, value in query_params.items() if value is not None
        }
        return self.api.get(endpoint, query_params)

    def get_connector_list(self, country_code="BR", open_finance=True) -> dict | None:
        endpoint = "connectors"
        query_params = {
            "countries": f"{country_code}",
            "isOpenFinance": "true" if open_finance else "false",
        }

        response = self.api.get(endpoint, query_params)
        return response.get("results")

    def get_connector_detail(self, connector_id) -> dict | None:
        endpoint = f"connectors/{connector_id}"
        response = self.api.get(endpoint)
        return response

    def get_account_detail(self, account_id, item_id) -> dict | None:
        endpoint = f"accounts/{account_id}"
        query_params = {"itemId": item_id}
        response = self.api.get(endpoint, query_params)
        return response

    def get_account_list(self, item_id):
        endpoint = "accounts"
        query_params = {"itemId": item_id}
        response = self.api.get(endpoint, query_params)
        return response.get("results")

    def get_item_detail(self, item_id) -> dict:
        endpoint = f"items/{item_id}"
        response = self.api.get(endpoint)
        return response

    def create_item_detail(
        self,
        credentials: dict,
        connector_name: str | None = None,
        connector_id: str | None = None,
        open_finance: bool = True,
        webhook_url: str | None = None,
        products: list | None = None,
        client_user_id: str | None = None,
    ) -> dict:
        connector = self.get_connector_details(
            connector_name, connector_id, open_finance
        )

        payload = self._create_item_payload(
            connector, credentials, webhook_url, products, client_user_id
        )
        return self.api.post("items", payload)

    def update_item_detail(
        self,
        item_id: str,
        credentials: dict,
        connector_name: str | None = None,
        connector_id: str | None = None,
        open_finance: bool = True,
        webhook_url: str | None = None,
        products: list | None = None,
        client_user_id: str | None = None,
    ) -> dict:
        connector = self.get_connector_details(
            connector_name, connector_id, open_finance
        )

        payload = self._create_item_payload(
            connector, credentials, webhook_url, products, client_user_id
        )
        return self.api.patch(f"items/{item_id}", payload)

    def _create_item_payload(
        self, connector, credentials, webhook_url, products, client_user_id
    ):
        connector_id = connector.get("id")
        required_credentials = connector.get("credentials")
        payload = {"connectorId": connector_id, "parameters": {}}

        for required_credential in required_credentials:
            credential_name = required_credential.get("name")
            print(f"Processing credential: {credential_name}")
            self._validate_credential(credential_name, required_credential, credentials)
            payload["parameters"][credential_name] = credentials[credential_name]

        return payload

    def delete_item_detail(self, item_id: str) -> int | None:
        """Returns the number of items deleted."""
        endpoint = f"items/{item_id}"
        response = self.api.delete(endpoint)
        count = response.get("count")
        return count

    def _validate_credential(
        self, credential_name: str | None, required_credential, credentials
    ):
        escaped_regex = required_credential.get("validation", {})
        optional = required_credential.get("optional", False)

        if credential_name not in credentials and not optional:
            raise MissingCredentialError(f"Missing credential: {credential_name}")

        if escaped_regex:
            if not re.match(escaped_regex, credentials[credential_name]):
                raise InvalidCredentialError(f"Invalid credential: {credential_name}")

    def get_connector_details(
        self,
        connector_name: str | None = None,
        connector_id: str | None = None,
        open_finance: bool = True,
    ):
        if not connector_id and not connector_name:
            raise ValueError("connector_id or connector_name must be provided.")

        if not self.api._connectors:
            self.api._connectors = self.get_connector_list(open_finance=open_finance)

        if connector_id:
            connector = self.find_attr(
                self.api._connectors, "id", connector_id, lower=False
            )
        elif connector_name:
            connector = self.find_attr(self.api._connectors, "name", connector_name)

        if not connector:
            raise ValueError(f"{connector_name} connector not found.")

        return connector

    def find_attr(
        self, attr_list, attribute_key: str, attribute_value: str, lower=True
    ):
        for attr in attr_list:
            if lower:
                if attr[attribute_key].lower() == attribute_value.lower():
                    return attr
            else:
                if attr[attribute_key] == attribute_value:
                    return attr
        return None
