
import logging

from pynab.client import YNABClient, get_credentials
from bankutil.chase import get_pending_transactions
from bankutil.config import CONF
import os
from zlib import crc32
from datetime import datetime, date, timedelta
from bankutil.gmail import GmailClient
from bankutil.googleauth import get_credentials_from_secrets_files, get_credentials_from_secrets
from decimal import Decimal
from pynab.openapi.models.save_transaction import SaveTransaction
from pynab.openapi.models.save_transaction_wrapper import SaveTransactionWrapper
from base64 import b64decode

LOG = logging.getLogger(__name__)


def get_ynab_transactions(ynab_bearer_token, ynab_budget_id, ynab_account_id):

    os.environ['YNAB_TOKEN'] = ynab_bearer_token
    ynab_creds = get_credentials()
    client = YNABClient(ynab_creds)

    trans = client.transactions.get_transactions_by_account(
        budget_id=ynab_budget_id,
        account_id=ynab_account_id,
        since_date=datetime.now() - timedelta(7))

    return trans.data.transactions


def ynab_trans_normalize(ynab_transactions):

    # Convert ynab trans to datetime
    for item in ynab_transactions:
        item.date = datetime.combine(item.date, datetime.min.time())


def match_ynab_transaction(pending_trans, ynab_transactions):

    trans_check = [x for x in ynab_transactions if
                   x.memo and
                   x.memo.startswith(pending_trans.id)]

    if trans_check:
        return True
    else:
        return False


def ynab_add_transaction(pending_trans, ynab_bearer_token, ynab_budget_id,
                         ynab_account_id):

    memo = pending_trans.id
    LOG.info('Adding transaction %s', pending_trans)
    transobj = SaveTransactionWrapper(
                SaveTransaction(
                    account_id=ynab_account_id,
                    amount=pending_trans.millidollars,
                    payee_name=pending_trans.merchant,
                    date=pending_trans.trans_date,
                    memo=memo,
                    approved=False))
    os.environ['YNAB_TOKEN'] = ynab_bearer_token
    ynab_creds = get_credentials()
    client = YNABClient(ynab_creds)
    client.transactions.create_transaction(ynab_budget_id, transobj)


def import_transactions(days, google_credentials, ynab_bearer_token, ynab_budget_id,
                        ynab_account_id):

    gmail_client = GmailClient(google_credentials)

    gmail_trans = get_pending_transactions(gmail_client, days)
    ynab_trans = get_ynab_transactions(
        ynab_bearer_token, ynab_budget_id, ynab_account_id)

    ynab_trans_normalize(ynab_trans)

    for item in gmail_trans:
        if not match_ynab_transaction(item, ynab_trans):
            ynab_add_transaction(item, ynab_bearer_token, ynab_budget_id,
                                 ynab_account_id)


def cli_import_transactions(days):
    """Get Gmail chase notifications and match them with YNAB Transactions."""

    secrets_file = CONF.get('google_api_client_secrets_file')
    oauth_creds_file = CONF.get('google_oauth_creds_cache')

    google_credentials = get_credentials_from_secrets_files(
        secrets_file, oauth_creds_file)
    ynab_bearer_token = CONF.get('ynab_bearer_token')
    ynab_budget_id = CONF.get('ynab_budget_id')
    ynab_account_id = CONF.get('ynab_account_id')

    import_transactions(days, google_credentials, ynab_bearer_token,
                        ynab_budget_id, ynab_account_id)


def lambda_import_transactions(event, context):

    import os
    import json

    days = event.get('days', 2)
    secrets_data = json.loads(b64decode(os.environ.get('google_client_secret', '')))
    oauth_creds = json.loads(b64decode(os.environ.get('oauth_creds', '')))
    ynab_bearer_token = os.environ.get('ynab_bearer_token', '')
    ynab_budget_id = os.environ.get('ynab_budget_id', '')
    ynab_account_id = os.environ.get('ynab_account_id', '')

    google_credentials = get_credentials_from_secrets(secrets_data, oauth_creds)

    import_transactions(days, google_credentials, ynab_bearer_token,
                        ynab_budget_id, ynab_account_id)
