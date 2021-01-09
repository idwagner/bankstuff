from pynab.client import YNABClient, get_credentials
from pynab.openapi.models import SaveMonthCategoryWrapper, SaveMonthCategory
from bankutil.config import CONF
import os
import re
import logging
from tabulate import tabulate

from datetime import datetime, date
import calendar

LOG = logging.getLogger(__name__)
RE_kv = re.compile(r'([a-zA-Z]+)=(.+)')

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return date(year, month, day)

class PaymentDetails:

    DAILY_RATE_MULTIPLIER = {
        'weekly': (1/7.0),
        'monthly': (1/30.0),
        'yearly': (1/365.0),
    }

    def __init__(self, category):
        self._category = category
        self._daily_rate = 0
        self.type = ''
        self.amount = 0
        self.dueday = 1

        # Values are csv keypairs, eg type=monthly,amount=23,dueday=2
        attr = dict(map(lambda x: x.split('='), category.note.split(','))) 

        if 'type' in attr:
            self.type = attr['type']
        if 'amount' in attr:
            self.amount = float(attr['amount'])
        if 'dueday' in attr:
            self.dueday = int(attr['dueday'])

    @property
    def daily_rate_mult(self):
        return self.DAILY_RATE_MULTIPLIER.get(self.type, 0)

    @property
    def daily_rate(self):
        return self.daily_rate_mult * float(self.amount)

    @property
    def next_due(self):
        if self.type == 'weekly':
            return False
            
        today = datetime.now()
        this_month_due = datetime(today.year, today.month, self.dueday)
        LOG.info(f'{self._category.name} {self.dueday}')

        if self.dueday < today.day:
            # Already paid this month, set to next month
            return add_months(this_month_due, 1)
        else:
            return this_month_due

    @property
    def days_until_due(self):
        today = datetime.now()
        return (self.next_due - today).days

def cli_budget_overage(days_until_income=0):

    ynab_bearer_token = CONF.get('ynab_bearer_token')
    ynab_budget_id = CONF.get('ynab_budget_id')
    ynab_account_id = CONF.get('ynab_account_id')

    os.environ['YNAB_TOKEN'] = ynab_bearer_token
    ynab_creds = get_credentials()
    client = YNABClient(ynab_creds)

    import pickle

    # categories = client.categories.get_categories(ynab_budget_id)  
    # with open('/tmp/cats.pickle', 'wb') as fd:
    #     pickle.dump(categories, fd)

    with open('/tmp/cats.pickle', 'rb') as fd:
        categories = pickle.load(fd)

    headers = ['name', 'daily_rate', 'next_due', 'days_until_due']

    table = []
    for category_group in categories.data.category_groups:
        for category in category_group.categories:
            if category.note:

                payment = PaymentDetails(category)
                data = {}
                data['name'] = category.name
                data['daily_rate'] = payment.daily_rate
                data['next_due'] = payment.next_due
                data['days_until_due'] = payment.days_until_due

                table.append([data[x] for x in headers])

    print(tabulate(table, headers))


def cli_budget_bills(days):

    ynab_bearer_token = CONF.get('ynab_bearer_token')
    ynab_budget_id = CONF.get('ynab_budget_id')
    ynab_account_id = CONF.get('ynab_account_id')

    os.environ['YNAB_TOKEN'] = ynab_bearer_token
    ynab_creds = get_credentials()
    client = YNABClient(ynab_creds)

    categories = client.categories.get_categories(ynab_budget_id)    
    transactions = []

    for category_group in categories.data.category_groups:

        for category in category_group.categories:
            
            if category.note:

                daily_rate = get_daily_rate(category.note)
                contribution = round(daily_rate * days)
                LOG.debug(f"{category.name} - {contribution}")

                contribution_millis = contribution * 1000
                new_balance = category.balance + contribution_millis

                transactions.append([category, contribution_millis, new_balance])


    table = [[category.name, f'{contrib/1000:.2f}', f'{new_balance/1000:.2f}'] 
                for category, contrib, new_balance in transactions ]

    print(tabulate(table, headers=['Category', 'Contribution', 'New Balance']))
    print()
    confirm = input('Confirm update [y/N]? ')

    if not confirm.lower() in ['y']:
        print('Cancelled')
    else:

        for category, contribution_millis, new_balance in transactions:
            update_data = SaveMonthCategoryWrapper(SaveMonthCategory(budgeted=new_balance))

            client.categories.update_month_category(
                ynab_budget_id, 'current', category.id, update_data)