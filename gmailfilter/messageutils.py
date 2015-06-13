
from email.utils import parseaddr


def get_list_id(message):
    list_id = message.get_headers()['List-Id']
    return parseaddr(list_id)[1]
