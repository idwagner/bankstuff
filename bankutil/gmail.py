import logging
from base64 import b64decode
from datetime import datetime
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.ERROR)

LOG = logging.getLogger(__name__)


class GmailMessage:

    def __init__(self, message_data):
        self._message = message_data

    @property
    def body(self):
        text = b64decode(self._message['payload']['body']['data'])
        text = text.replace(b'\r', b'')
        text = text.replace(b'\n', b'')
        text = text.decode('utf-8')

        return text

    @property
    def date(self):
        epoch = round(int(self._message['internalDate']) / 1000)
        return datetime.fromtimestamp(epoch)

    @property
    def id(self):
        return self._message['id']

class MessageIterator(object):

    def __init__(self, service, messages, userId='me'):
        self._service = service
        self.userId = userId
        self._msgclient = self._service.users().messages()
        self._messages = messages

    def __iter__(self):
        return self

     # Python 3 compatibility
    def __next__(self):
        return self.next()

    def next(self):
        if not self._messages:
            raise StopIteration
        else:
            raw_message = self._msgclient.get(
                userId=self.userId, id=self._messages.pop()).execute()
            return GmailMessage(raw_message)

def get_service(credentials):
    return build('gmail', 'v1', credentials=credentials)


class GmailClient(object):

    def __init__(self, credentials):

        self._service = get_service(credentials)

        self._threads = self._service.users().threads()
        self._messages = self._service.users().messages()
        self._labels = self._service.users().labels()


    def get_label_by_name(self, name):
        all_labels = self._labels.list(userId='me').execute()
        search = [x for x in all_labels['labels'] if x['name'] == name]
        if search:
            return search[0]['id']
        else:
            return None

    def recent_msg_by_labelname(self, label, days=3):
        search_q = f'in:{label} newer_than:{days}d'
        messages = self._messages.list(userId='me', q=search_q).execute()
        messageids = [x['id'] for x in messages.get('messages', [])]
        return MessageIterator(self._service, messageids)

    def get_thread_messages(self, threadid):
        tdata = self._threads.get(userId='me', id=threadid).execute()
        return tdata
