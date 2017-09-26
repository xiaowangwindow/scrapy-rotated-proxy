import base64
import re
import six
from itertools import cycle
from six.moves.urllib.parse import urlunparse
from six.moves.urllib.request import proxy_bypass
from six.moves.urllib.parse import unquote
try:
    from urllib2 import _parse_proxy
except ImportError:
    from urllib.request import _parse_proxy

from scrapy.exceptions import NotConfigured
from scrapy.http import Request
from scrapy.settings import Settings
from scrapy.utils.httpobj import urlparse_cached
from scrapy.utils.python import to_bytes


class RotatedProxy(object):
    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool('{class_name}_ENABLED'.format(class_name=cls.__name__.upper())):
            raise NotConfigured
        auth_encoding = crawler.settings.get('HTTPPROXY_AUTH_ENCODING')
        return cls(crawler, auth_encoding)

    def __init__(self, crawler, auth_encoding='latin-1'):
        self.auth_encoding = auth_encoding
        self.proxies = self.getproxies(crawler.settings)

    def process_request(self, request, spider):
        if 'proxy' in request.meta:
            if request.meta['proxy'] is None:
                return
            creds, proxy_url = self._get_proxy(request.meta['proxy'], '')
            request.meta['proxy'] = proxy_url
            if creds and not request.headers.get('Proxy-Authorization'):
                request.headers['Proxy-Authorization'] = b'Basic ' + creds
            return
        elif not self.proxies:
            return

        parsed = urlparse_cached(request)
        scheme = parsed.scheme

        if scheme in ('http', 'https') and proxy_bypass(parsed.hostname):
            return

        if scheme in self.proxies:
            self._set_proxy(request, scheme)

    def _basic_auth_header(self, username, password):
        if six.PY2:
            username = username.encode(self.auth_encoding)
            password = password.encode(self.auth_encoding)
        user_pass = to_bytes(
            '{username}:{password}'.format(username=unquote(username), password=unquote(password)),
            encoding=self.auth_encoding
        )
        return base64.b64encode(user_pass).strip()

    def _set_proxy(self, request, scheme):
        creds, proxy = next(self.proxies[scheme])
        print(proxy)
        request.meta['proxy'] = proxy
        if creds:
            request.headers['Proxy-Authorization'] = b'Basic ' + creds

    def _get_proxy(self, url, orig_type=''):
        proxy_type, user, password, hostport = _parse_proxy(url)
        proxy_url = urlunparse((proxy_type or orig_type, hostport, '', '', '', ''))

        creds = self._basic_auth_header(user, password) if user else None

        return creds, proxy_url

    def getproxies(self, settings):
        pattern = re.compile(r'(?P<scheme>[A-Z]+)_PROXIES')

        def _filter(tuple_):
            m = pattern.match(tuple_[0])
            if m:
                scheme = m.group('scheme').lower()
                return scheme, cycle([self._get_proxy(item, scheme) for item in tuple_[1]])

        proxies = []
        for item in settings.items():
            pair = _filter(item)
            if pair:
                proxies.append(pair)
        return dict(proxies)


if __name__ == '__main__':
    pass
