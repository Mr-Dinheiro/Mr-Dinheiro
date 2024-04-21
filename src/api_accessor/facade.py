from typing import Any
from data_handler import PluggyDataHandler
from pluggy_api import PluggyApi
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
        # simple cache
        self._connectors: dict | None = None

    # transactions
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
            transactions, total_pages = self.get_transaction_list(
                account_id, from_date, to_date, page_size, page
            )

            if not transactions:
                break

            all_transactions.extend(transactions)
            page += 1

        return all_transactions

    def get_transaction_list(
        self, account_id: str, from_date=None, to_date=None, page_size=20, page=1
    ) -> tuple[dict[Any, Any], dict[Any, Any]]:
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
        response, status_code = self.api.get(endpoint, query_params)
        # TODO: handle status_code
        return response.get("results", {}), response.get("totalPages", {})

    # connectors
    def get_connector_list(self, country_code="BR", open_finance=True) -> dict | None:
        endpoint = "connectors"
        query_params = {
            "countries": f"{country_code}",
            "isOpenFinance": "true" if open_finance else "false",
        }

        response, status_code = self.api.get(endpoint, query_params)
        # TODO: handle status_code
        return response.get("results")

    def get_connector_detail(self, connector_id) -> dict | None:
        endpoint = f"connectors/{connector_id}"
        response, status_code = self.api.get(endpoint)
        # TODO: handle status_code
        return response

    def fetch_and_find_connector(
        self,
        connector_name: str | None = None,
        connector_id: str | None = None,
        open_finance: bool = True,
    ):
        self._fetch_connectors_if_needed(open_finance)

        connector = self._find_connector_by_id_or_name(connector_id, connector_name)

        if not connector:
            raise ValueError(f"{connector_name or connector_id} connector not found.")

        return connector

    def _fetch_connectors_if_needed(self, open_finance: bool) -> dict | None:
        if not self._connectors:
            self._connectors = self.get_connector_list(open_finance=open_finance)
        return self._connectors

    def _find_connector_by_id_or_name(
        self, connector_id: str | None, connector_name: str | None
    ) -> dict | None:
        if not connector_id and not connector_name:
            raise ValueError("connector_id or connector_name must be provided.")

        if connector_id:
            return self._find_attribute(
                self._connectors, "id", connector_id, lower=False
            )
        elif connector_name:
            return self._find_attribute(self._connectors, "name", connector_name)

        return None

    def _find_attribute(
        self,
        attributes: dict | None,
        attribute_key: str,
        attribute_target: str,
        lower=True,
    ) -> dict | None:
        """Find an attribute in a list of attributes by key and target value."""
        if not attributes:
            return None

        for attribute in attributes:
            attribute_value = attribute.get(attribute_key, "")
            if (
                lower
                and isinstance(attribute_value, str)
                and isinstance(attribute_target, str)
            ):
                if attribute_value.lower() == attribute_target.lower():
                    return attribute
            else:
                if attribute_value == attribute_target:
                    return attribute
        return None

    # account
    def get_account_detail(self, account_id, item_id) -> dict | None:
        endpoint = f"accounts/{account_id}"
        query_params = {"itemId": item_id}
        response, status_code = self.api.get(endpoint, query_params)
        return response

    def get_account_list(self, item_id):
        endpoint = "accounts"
        query_params = {"itemId": item_id}
        response = self.api.get(endpoint, query_params)
        return response.get("results")

    # item
    def get_item_detail(self, item_id: str) -> dict[Any, Any]:
        endpoint = f"items/{item_id}"
        response, status_code = self.api.get(endpoint)
        return response

    def create_item_detail(
        self,
        credentials: dict,
        connector: dict,
        webhook_url: str | None = None,
        products: list | None = None,
        client_user_id: str | None = None,
    ) -> dict:
        payload = self._create_item_payload(
            connector, credentials, webhook_url, products, client_user_id
        )
        response, status_code = self.api.post("items", payload)
        # TODO: handle status_code
        return response

    def update_item_detail(
        self,
        item_id: str,
        credentials: dict,
        connector: dict,
        webhook_url: str | None = None,
        products: list | None = None,
        client_user_id: str | None = None,
    ) -> dict:
        payload = self._create_item_payload(
            connector, credentials, webhook_url, products, client_user_id
        )
        response, status_code = self.api.patch(f"items/{item_id}", payload)
        # TODO: handle status_code
        return response

    def _create_item_payload(
        self,
        connector: dict[str, Any],
        credentials: dict[str, Any],
        webhook_url: str | None,
        products: list[str] | None,
        client_user_id: str | None,
    ) -> dict[str, Any]:
        """_summary_

        Args:
            connector (dict[str, Any]): connector dict with the connector's id and credentials
            credentials (dict[str, Any]): Connector's credentials that are required to
                                          execute on a Key-Value object or a string if
                                          they are encrypted
            webhook_url (str | None): Url to be notified of item changes
            products (list[str] | None): Products to be collected in the connection
            client_user_id (str | None): Client's identifier for the user, it can be a ID, UUID or even an email.

        Returns:
            dict[str, Any]: contains the payload required by the API to create an item
        """
        connector_id = connector.get("id")
        required_credentials = connector.get("credentials", [])
        payload: dict[str, Any] = {"connectorId": connector_id, "parameters": {}}

        if webhook_url is not None:
            payload["parameters"]["webhookUrl"] = webhook_url
        if products is not None:
            payload["parameters"]["products"] = products
        if client_user_id is not None:
            payload["parameters"]["clientUserId"] = client_user_id

        for required_credential in required_credentials:
            credential_name = required_credential.get("name")
            self._validate_credential(credential_name, required_credential, credentials)
            payload["parameters"][credential_name] = credentials[credential_name]

        return payload

    def delete_item_detail(self, item_id: str) -> int:
        """Returns the number of items deleted."""
        endpoint = f"items/{item_id}"
        response, status_code = self.api.delete(endpoint)
        # TODO: handle status_code
        count = response.get("count", 0)
        return count

    def _validate_credential(
        self,
        credential_name: str,
        required_credential: dict[str, Any],
        credentials: dict[str, Any],
    ):
        escaped_regex = required_credential.get("validation", None)
        optional = required_credential.get("optional", False)

        if credential_name not in credentials and not optional:
            raise MissingCredentialError(f"Missing credential: {credential_name}")

        if escaped_regex is not None:
            if not re.match(escaped_regex, credentials[credential_name]):
                raise InvalidCredentialError(f"Invalid credential: {credential_name}")
