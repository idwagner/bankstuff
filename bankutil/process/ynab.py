from pynab.client import YNABClient, get_credentials
from pynab.openapi.models import SaveMonthCategoryWrapper, SaveMonthCategory
from bankutil.config import CONF
import os
import re
import logging
from tabulate import tabulate

LOG = logging.getLogger(__name__)
RE_kv = re.compile(r'([a-zA-Z]+)=(.+)')

daily_rate_multiplier = {
    'weekly': (1/7.0),
    'monthly': (1/30.0),
    'yearly': (1/365.0),
}

def get_daily_rate(attribute_str: str):
    
    attr = {}
    for pair in attribute_str.split(','):
        matches = RE_kv.match(pair)
        if matches:
            attr[matches[1]] = matches[2]

    if 'type' not in attr:
        LOG.error(f'Period Type not defined')

    if 'amount' not in attr:
        LOG.error(f'Amount not defined')

    if not attr['type'] in daily_rate_multiplier:
        LOG.error(f'Unknown Type {attr["type"]}')
    
    return daily_rate_multiplier[attr['type']] * float(attr['amount'])
    


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