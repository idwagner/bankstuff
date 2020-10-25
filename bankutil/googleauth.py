import logging
import json

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials


LOG = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/userinfo.profile"]


def get_oauth_token(client_secrets):
    """Run a local oauth flow to get an oauth token"""

    flow = Flow.from_client_config(
        client_secrets, scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')

    auth_url, _ = flow.authorization_url(prompt='consent')
    print('Please go to this URL: {}'.format(auth_url))

    code = input('Enter the authorization code: ')
    oauth_creds = flow.fetch_token(code=code)

    client_creds = Credentials(
        token=oauth_creds['access_token'],
        refresh_token=oauth_creds['refresh_token'],
        id_token=oauth_creds['id_token'],
        client_id=client_secrets['installed']['client_id'],
        client_secret=client_secrets['installed']['client_secret'],
        scopes=SCOPES,
    )

    return client_creds


def get_credentials_from_secrets_files(secrets_file, oauth_creds_file):

    with open(secrets_file) as fd:
        client_secrets = json.load(fd)

    with open(oauth_creds_file) as fd:
        oauth_credentials = json.load(fd)

    return get_credentials_from_secrets(client_secrets, oauth_credentials)


def get_credentials_from_secrets(client_secrets, oauth_credentials):
    """Get Google API Credentials with using the api secrets
    and a saved oauth token.
    """

    client_creds = Credentials(
        token=oauth_credentials['token'],
        refresh_token=oauth_credentials['refresh_token'],
        client_id=client_secrets['installed']['client_id'],
        client_secret=client_secrets['installed']['client_secret'],
        token_uri=client_secrets['installed']['token_uri'],
        scopes=SCOPES,
    )

    return client_creds
