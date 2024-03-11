from enum import Enum


class ItemStatus(Enum):
    UPDATING = "The connection is syncing with the provider. An update process is in progress and will be updated soon."
    LOGIN_ERROR = "The sync process finished with errors. The connection must be updated to execute again. We won't trigger auto-sync updates until new credentials parameters are provided."
    OUTDATED = "The sync process finished with errors. The parameters were correctly validated, but there was an error in the last execution. It can be retried."
    WAITING_USER_INPUT = "The sync process needs user's input to continue. The connection requires user's input to continue the sync process, this is common for MFA authentication connectors."
    UPDATED = "The sync process finished successfully. The last sync process has completed successfully and all new data is available to collect."


class ItemStatusToExecutionStatus(Enum):
    UPDATING = [
        "CREATED",
        "LOGIN_IN_PROGRESS",
        "LOGIN_MFA_IN_PROGRESS",
        "ACCOUNTS_IN_PROGRESS",
        "CREDITCARDS_IN_PROGRESS",
        "TRANSACTIONS_IN_PROGRESS",
        "INVESTMENTS_IN_PROGRESS",
        "IDENTITY_IN_PROGRESS",
    ]
    WAITING_USER_INPUT = ["WAITING_USER_INPUT"]
    LOGIN_ERROR = [
        "INVALID_CREDENTIALS",
        "ACCOUNT_LOCKED",
        "USER_AUTHORIZATION_NOT_GRANTED",
        "ACCOUNT_CREDENTIALS_RESET",
    ]
    OUTDATED = [
        "SITE_NOT_AVAILABLE",
        "INVALID_CREDENTIALS_MFA",
        "ALREADY_LOGGED_IN",
        "ACCOUNT_LOCKED",
        "ACCOUNT_NEEDS_ACTION",
        "ERROR",
        "CONNECTION_ERROR",
        "USER_AUTHORIZATION_PENDING",
        "USER_INPUT_TIMEOUT",
        "USER_NOT_SUPPORTED",
        "ACCOUNT_CREDENTIALS_RESET",
    ]
    UPDATED = ["SUCCESS", "PARTIAL_SUCCESS"]


class ExecutionStatusDetail(Enum):
    CREATED = "The connection was successfully initiated."
    LOGIN_IN_PROGRESS = "The connection is currently in the Login authentication step."
    LOGIN_MFA_IN_PROGRESS = "The connection is currently in the second Login authentication step. This state happens after submitting an MFA token parameter only."
    ACCOUNTS_IN_PROGRESS = "Currently collecting Accounts data. Implies Login step has just been completed."
    CREDITCARDS_IN_PROGRESS = "Currently collecting Credit Cards data. Implies Accounts collection step has just been completed (or skipped)."
    TRANSACTIONS_IN_PROGRESS = "Currently collecting Accounts and Credit Cards Transactions data. Implies Credit Cards collection step has just been completed (or skipped)."
    INVESTMENT_TRANSACTIONS_IN_PROGRESS = "Currently collecting Investment Transactions. Note: Only a few connectors support this product. Implies Transactions collection step has just been completed (or skipped)."
    PAYMENT_DATA_IN_PROGRESS = "Currently collecting Transactions Payment data. Note: Only a few connectors support this product. Implies Investment Transactions collection step has just been completed (or skipped)."
    IDENTITY_IN_PROGRESS = "Currently collecting Identity data. Implies Transactions (and Payment Data, if any) steps have just been completed (or skipped)."
    OPPORTUNITIES_IN_PROGRESS = "Currently collecting Opportunities data. Implies Identity steps have just been completed (or skipped)."
    MERGING = "Analyzing and storing all the collected data. Implies all of the available Institution data has been collected."
