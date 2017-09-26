import base64
import six
from six.moves.urllib.parse import unquote
from scrapy.utils.python import to_bytes


def _basic_auth_header(username, password, auth_encoding=None):
    if six.PY2:
        username = username.encode(auth_encoding)
        password = password.encode(auth_encoding)
    user_pass = to_bytes(
        '{username}:{password}'.format(username=unquote(username),
                                       password=unquote(password)),
        encoding=auth_encoding
    )
    return base64.b64encode(user_pass).strip()
