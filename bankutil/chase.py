
import logging
import re
from base64 import b64decode
from operator import attrgetter
from datetime import datetime

from bankutil.gmail import GmailClient

LABEL_NAME = 'Chase Transactions'
TRANS_MATCH = re.compile(r'A charge of \(\$USD\) ([0-9.]+) at (.*) has been '
                         r'authorized on')

LOG = logging.getLogger(__name__)


class ChasePendingDetails(object):
    """Model to represent a transaction"""

    def __init__(self, message):
        self._message = message

        self.is_transaction = False
        self.id = None
        self.dollars = None
        self.merchant = None
        self.trans_date = None
        self.load()

    def __repr__(self):
        str_date = self.trans_date.strftime('%m/%d/%Y')
        return "{} on {} at {}".format(self.dollars, str_date, self.merchant)

    @property
    def millidollars(self):
        return int(self.dollars * 1000)

    def load(self):

        trans_details = TRANS_MATCH.search(self._message.body)
        if trans_details:
            dollars, merchant = trans_details.groups()

            if merchant.endswith('...'):
                merchant = merchant[:-3]

            self.id = self._message.id
            self.dollars = float(dollars) * -1.0
            self.merchant = merchant
            self.trans_date = self._message.date
            self.is_transaction = True

    @property
    def body(self):
        text = b64decode(self._message['payload']['body']['data'])
        text = text.replace(b'\r', b'')
        text = text.replace(b'\n', b'')
        text = text.decode('')

        return text

    @property
    def date(self):
        return self._message.date


def get_pending_transactions(gmail: GmailClient, days=1):
    """ Load matching gmail messages and extract transaction details
        Returns list of ChasePendingDetails
    """
    msgs = gmail.recent_msg_by_labelname(LABEL_NAME, days=days)
    transactions = []
    for message in msgs:

        parsed = ChasePendingDetails(message)
        if parsed.is_transaction:
            transactions.append(parsed)

    transactions.sort(key=attrgetter('date'))
    return transactions
