import base64
import logging
import re
import six
import scrapy_rotated_proxy.signals as proxy_signals

from itertools import cycle
from scrapy.utils.misc import load_object
from twisted.internet import defer
from six.moves.urllib.parse import urlunparse
from six.moves.urllib.request import proxy_bypass
from six.moves.urllib.parse import unquote
from scrapy import signals
from scrapy.exceptions import NotConfigured, CloseSpider
from scrapy.http import Request
from scrapy.settings import Settings
from scrapy.utils.httpobj import urlparse_cached
from scrapy.utils.python import to_bytes
from scrapy_rotated_proxy.extensions import default_settings

if six.PY2:
    from urllib2 import _parse_proxy
else:
    from urllib.request import _parse_proxy

logger = logging.getLogger(__name__)


class RotatedProxy(object):
    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool('ROTATED_PROXY_ENABLED'):
            raise NotConfigured

        auth_encoding = crawler.settings.get('HTTPPROXY_AUTH_ENCODING')
        o = cls(crawler, auth_encoding)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(o.proxy_block_received,
                                signal=proxy_signals.proxy_block)
        return o

    def __init__(self, crawler, auth_encoding='latin-1'):
        self.auth_encoding = auth_encoding
        self.proxies_storage = load_object(
            crawler.settings.get('PROXY_STORAGE',
                                 getattr(default_settings, 'PROXY_STORAGE')))(
            crawler.settings, self.auth_encoding)
        self.proxies = None  # Style: {'http':{(auth1, proxy1), (auth2, proxy2}}
        self.black_proxies = {}  # Style: like self.proxies
        self.proxy_gen = {}  # Style: {'http': http_cycle_gen, 'https': https_cycle_gen}

    def spider_opened(self, spider):
        self.proxies_storage.open_spider(spider)

    def spider_closed(self, spider):
        self.proxies_storage.close_spider(spider)

    def proxy_block_received(self, spider, response, exception):
        if response.meta.get('proxy'):
            scheme = urlparse_cached(response)[0]
            if scheme not in self.black_proxies:
                self.black_proxies.setdefault(scheme, set())
            if response.request.headers.get('Proxy-Authorization'):
                creds = \
                    response.request.headers.get('Proxy-Authorization').split(
                        b' ')[
                        -1]
            else:
                creds = None
            self.black_proxies[scheme].add((creds, response.meta.get('proxy')))

            logger.debug(
                'Block proxy: {proxy}, Total block {count} {scheme} proxy'.format(
                    proxy=response.meta.get('proxy'),
                    count=len(self.black_proxies[scheme]),
                    scheme=scheme
                ))

    @defer.inlineCallbacks
    def process_request(self, request, spider):
        if not self.proxies:
            self.proxies = yield self.proxies_storage.proxies()
            for scheme, proxies in self.proxies.items():
                logger.debug(
                    'Loaded {count} {scheme} proxy from {origin}'.format(
                        count=len(proxies),
                        scheme=scheme,
                        origin=self.proxies_storage.__class__.__name__
                    ))

        # When Retry, dont_filter=True, reset proxy
        if 'proxy' in request.meta and not request.dont_filter:
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
            '{username}:{password}'.format(username=unquote(username),
                                           password=unquote(password)),
            encoding=self.auth_encoding
        )
        return base64.b64encode(user_pass).strip()

    def _set_proxy(self, request, scheme):
        creds, proxy = next(self._cycle_proxy(scheme))
        print(proxy)
        request.meta['proxy'] = proxy
        if creds:
            request.headers['Proxy-Authorization'] = b'Basic ' + creds

    def _cycle_proxy(self, scheme):
        if not self.proxy_gen.get(scheme):
            self.proxy_gen[scheme] = self._gen_proxy(scheme)
        return self.proxy_gen[scheme]

    def _gen_proxy(self, scheme):
        while True:
            self.proxies[scheme] -= self.black_proxies.get(scheme, set())
            if not self.proxies[scheme]:
                logger.info(
                    'Run out of all {scheme} proxies'.format(scheme=scheme))
                raise CloseSpider('Run out of All Proxy')
                break

            logger.debug('Left {count} {scheme} proxy to run'.format(
                count=len(self.proxies[scheme]),
                scheme=scheme
            ))
            for proxy_item in self.proxies[scheme]:
                if proxy_item in self.black_proxies.get(scheme, set()):
                    continue
                yield proxy_item

    def _get_proxy(self, url, orig_type=''):
        proxy_type, user, password, hostport = _parse_proxy(url)
        proxy_url = urlunparse(
            (proxy_type or orig_type, hostport, '', '', '', ''))

        creds = self._basic_auth_header(user, password) if user else None

        return creds, proxy_url
