import logging
import click
import coloredlogs
from bankutil.config import CONF
LOG = logging.getLogger(__name__)
LOG_LEVELS = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}


##########################
# Entry Point
##########################
@click.group(name="Main")
@click.option('-v', '--verbose', count=True)
@click.option('-d', '--debug', count=True, help="Debug external libs")
@click.option('--config', default=None, help='Config section')
def main(verbose, debug, config):
    # Set the appropriate logging
    coloredlogs.install(level=LOG_LEVELS.get(verbose, logging.DEBUG))
    # logging.basicConfig(level=LOG_LEVELS.get(verbose, logging.DEBUG))
                        # format='[%(levelname)s] %(name)s:%(lineno)d - %(message)s')
    if not debug:
        logging.getLogger('oauth2client').setLevel(logging.CRITICAL)
        logging.getLogger('google').setLevel(logging.CRITICAL)
        logging.getLogger('googleapiclient').setLevel(logging.CRITICAL)

    if config:
        CONF.reload(section=config)



@click.option('--days', required=False, default=1, type=click.INT)
@click.command('import')
def exec_import(days):
    from bankutil.process.import_gmail_notifications import cli_import_transactions

    cli_import_transactions(days)



@click.option('--days', required=False, default=14, type=click.INT)
@click.command('budget-bills')
def exec_budget_bills(days):
    from bankutil.process.ynab import cli_budget_bills

    cli_budget_bills(days)




@click.command('google-auth')
def google_auth():
    """Google Authorization """
    from bankutil.googleauth import get_oauth_token
    import json

    secrets_file = CONF.get('google_api_client_secrets_file')
    oauth_creds_file = CONF.get('google_oauth_creds_cache')

    if not secrets_file:
        raise RuntimeError('Config google_api_client_secrets_file not set')

    try:

        with open(secrets_file) as fd:
            client_secrets = json.load(fd)

    except Exception as e:
        raise RuntimeError(f'Cannot load Google Client Secrets. {e}')

    creds = get_oauth_token(client_secrets)
    with open(oauth_creds_file, 'w') as fd:

        fd.write(creds.to_json())

main.add_command(exec_import)
main.add_command(exec_budget_bills)
main.add_command(google_auth)
