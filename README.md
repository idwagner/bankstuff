# Bank stuff

This is a collection of scripts to import chase alerts from a gmail inbox.

It works by doing this:

# Setup

1. GCP Project. You don't need a paid account, just a gcp project which you can create an oauth credential to use with gmail.
 - Create a project within the google cloud console.
 - Create an oauth credential, and save the client json locally for now.
2. YNAB developer key
 - Go to you account settings > Developer settings. Create a personal access token.
3. Python virtual environment.
```sh
# Clone this repo
# Then run:
python setup.py develop
```
4. Configure this `project's settings file.
  - Use either filename `~/.config/bankstuff.ini`, or environment `BANKSTUFF_CONFIG` pointing to an alternate ini file
```ini
[DEFAULT]
google_api_client_secrets_file = /path/to/goole_client.json # from step 1
google_oauth_creds_cache = /path/to/creds_cache.json # A json file location to keep the credential cache
ynab_bearer_token = abcdefghij # YNAB PAT
ynab_budget_id = aaa-bbb-ccc-ddd # UUID for budget (viewable in ynab desktop website url)
ynab_account_id = aaa-bbb-ccc-ddd # UUID for account to import in. Click on the specific account and get it from the url.
```
5. Setup a filter in gmail to send chase alerts to a certain label (set at `bankstuff.chase.LABEL_NAME`).
6. Once you have the above setup, run `bank google-auth` and follow instructions. This will get you an oauth token with read access to your gmail box.

# Running

`bank import [--days 3]`

This will import the past *x* days of transactions by doing the following
1. Pull messages with the proper label and look for transaction details with regex.
1. Use the gmail messageid as a reference to see if a ynab transaction exists with the messageid in the memo field.
1. Add it if it doesn't exist

> Note you can still add details to the memo field after the messageid.
