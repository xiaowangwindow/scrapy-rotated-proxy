import base64
import logging
import re
import six
import scrapy_rotated_proxy.signals as proxy_signals

from itertools import cycle

import time

from scrapy.utils.misc import load_object
from scrapy_rotated_proxy import util
from twisted.internet import defer
from twisted.internet import task
from twisted.internet import reactor
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


class RotatedProxyMiddleware(object):
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
        crawler.signals.connect(o.proxy_remove_received,
                                signal=proxy_signals.proxy_remove)
        return o

    def __init__(self, crawler, auth_encoding='latin-1'):
        self.crawler = crawler
        self.auth_encoding = auth_encoding
        self.proxies_storage = load_object(
            crawler.settings.get(
                'PROXY_STORAGE',
                getattr(default_settings, 'PROXY_STORAGE')
            )
        )(crawler.settings, self.auth_encoding)
        self.sleep_interval = crawler.settings.get('PROXY_SLEEP_INTERVAL',
                                                   getattr(default_settings, 'PROXY_SLEEP_INTERVAL'))
        self.spider_close_when_no_proxy = crawler.settings.get(
            'PROXY_SPIDER_CLOSE_WHEN_NO_PROXY',
            getattr(default_settings, 'PROXY_SPIDER_CLOSE_WHEN_NO_PROXY')
        )
        self.check_task = None
        self.spider = None
        self.proxies = None
        self.valid_proxies = {}
        self.black_queue = {}
        self.black_proxies = {}
        self.invalid_proxies = {}
        self.proxy_gen = {}

    @defer.inlineCallbacks
    def spider_opened(self, spider, *args, **kwargs):
        self.spider = spider
        self.proxies_storage.open_spider(spider)
        self.proxies = yield self.proxies_storage.proxies()
        self.check_task = task.LoopingCall(self._check_black_proxy)
        self.check_task.start(60)

        logger.info('{middleware} opened {backend}'.format(
            middleware=self.__class__.__name__,
            backend='with backend: {}'.format(self.proxies_storage.__class__.__name__)
        ))
        for scheme, proxies in self.proxies.items():
            logger.info(
                'Loaded {count} {scheme} proxy from {backend}'.format(
                    count=len(proxies),
                    scheme=scheme,
                    backend=self.proxies_storage.__class__.__name__
                ))

    def spider_closed(self, spider):
        self.proxies_storage.close_spider(spider)
        if self.check_task and self.check_task.running:
            self.check_task.stop()

        logger.info('{middleware} closed'.format(middleware=self.__class__.__name__))

    @defer.inlineCallbacks
    def process_request(self, request, spider):
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
            yield self._set_proxy(request, scheme)

    def _get_proxy(self, url, orig_type=''):
        proxy_type, user, password, hostport = _parse_proxy(url)
        proxy_url = urlunparse(
            (proxy_type or orig_type, hostport, '', '', '', ''))

        creds = util._basic_auth_header(user, password, self.auth_encoding) \
            if user else None

        return creds, proxy_url

    @defer.inlineCallbacks
    def _set_proxy(self, request, scheme):
        while True:
            creds, proxy = next(self._cycle_proxy(scheme))
            if not proxy:
                yield self.sleep(self.sleep_interval,
                                 'Proxy pool of {scheme} is empty, waiting '
                                 '{sleep_second} seconds'.format(
                                     scheme=scheme,
                                     sleep_second=self.sleep_interval
                                 ))
            else:
                break

        request.meta['proxy'] = proxy
        if creds:
            request.headers['Proxy-Authorization'] = b'Basic ' + creds

    def _cycle_proxy(self, scheme):
        if not self.proxy_gen.get(scheme):
            self.proxy_gen[scheme] = self._gen_proxy(scheme)
        return self.proxy_gen[scheme]

    def _gen_proxy(self, scheme):
        while True:
            self.valid_proxies[scheme] = self.proxies[scheme]\
                                         - self.black_proxies.get(scheme, set())\
                                         - self.invalid_proxies.get(scheme, set())
            if not self.valid_proxies[scheme]:
                if self.spider_close_when_no_proxy:
                    self.crawler.engine.close_spider(self.spider,
                                                     'Run out of All Proxy')
                    break
                else:
                    logger.info(
                        'Run out of all {scheme} proxies'.format(scheme=scheme))
                    yield None, None

            logger.info('Left {count} {scheme} proxy to run'.format(
                count=len(self.valid_proxies[scheme]),
                scheme=scheme
            ))
            for proxy_item in self.valid_proxies[scheme]:
                if proxy_item in self.black_proxies.get(scheme, set()) or \
                        proxy_item in self.invalid_proxies.get(scheme, set()):
                    continue
                yield proxy_item

    def _extract_proxy_from_request(self, request):
        if request.meta.get('proxy'):
            scheme = urlparse_cached(request)[0]
            if request.headers.get('Proxy-Authorization'):
                creds = request.headers.get('Proxy-Authorization')\
                    .split(b' ')[-1]
            else:
                creds = None
            proxy = request.meta.get('proxy')
            return scheme, creds, proxy
        else:
            return None, None, None

    def proxy_remove_received(self, spider, request, exception):
        scheme, creds, proxy = self._extract_proxy_from_request(request)
        if proxy:
            self._remove_invalid_proxy(scheme, creds, proxy)

            logger.info(
                'Remove proxy: {proxy}, Total remove {count} {scheme} proxy'.format(
                    proxy=request.meta.get('proxy'),
                    count=len(self.invalid_proxies[scheme]),
                    scheme=scheme
                ))

    def _remove_invalid_proxy(self, scheme, creds, proxy):
        if scheme not in self.invalid_proxies:
            self.invalid_proxies.setdefault(scheme, set())

        proxy_item = (creds, proxy)
        if proxy_item not in self.invalid_proxies[scheme]:
            self.invalid_proxies[scheme].add(proxy_item)

    def proxy_block_received(self, spider, response, exception):
        scheme, creds, proxy = self._extract_proxy_from_request(response.request)
        if proxy:
            self._add_black_proxy(scheme, creds, proxy)

            logger.info(
                'Block proxy: {proxy}, Total block {count} {scheme} proxy'.format(
                    proxy=response.meta.get('proxy'),
                    count=len(self.black_proxies[scheme]),
                    scheme=scheme
                ))

    def _add_black_proxy(self, scheme, creds, proxy):
        if scheme not in self.black_proxies:
            self.black_proxies.setdefault(scheme, set())
        if scheme not in self.black_queue:
            self.black_queue.setdefault(scheme, list())

        proxy_item = (creds, proxy)
        if proxy_item not in self.black_proxies[scheme]:
            self.black_proxies[scheme].add(proxy_item)
            self.black_queue[scheme].insert(0, (proxy_item, time.time()))


    def _check_black_proxy(self):
        for scheme in self.black_queue.keys():
            while len(self.black_queue[scheme]):
                if int(time.time()) - int(self.black_queue[scheme][-1][1]) < self.sleep_interval:
                    break
                proxy_item, timestamp = self.black_queue[scheme].pop()
                if proxy_item in self.black_proxies[scheme]:
                    self.black_proxies[scheme].remove(proxy_item)

    def sleep(self, secs, msg):
        logger.info(msg)
        d = defer.Deferred()
        reactor.callLater(secs, d.callback, None)
        return d

