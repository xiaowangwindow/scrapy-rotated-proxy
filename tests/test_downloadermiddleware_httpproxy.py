import os
import sys
from functools import partial
from twisted.trial.unittest import TestCase, SkipTest
from twisted.internet import defer

from scrapy_rotated_proxy import RotatedProxy
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from scrapy.exceptions import NotConfigured
from scrapy.http import Response, Request
from scrapy.spiders import Spider
from scrapy.crawler import Crawler
from scrapy.settings import Settings

spider = Spider('foo')


class TestDefaultHeadersMiddleware(TestCase):

    failureException = AssertionError

    def setUp(self):
        self._oldenv = os.environ.copy()

    def tearDown(self):
        os.environ = self._oldenv

    def test_not_enabled(self):
        settings = Settings({'ROTATEDPROXY_ENABLED': False})
        crawler = Crawler(spider, settings)
        self.assertRaises(NotConfigured, partial(RotatedProxy.from_crawler, crawler))

    @defer.inlineCallbacks
    def test_no_setting_proxies(self):
        crawler = Crawler(spider)
        mw = RotatedProxy(crawler)

        for url in ('http://e.com', 'https://e.com', 'file:///tmp/a'):
            req = Request(url)
            res = yield mw.process_request(req, spider)
            assert res is None
            self.assertEqual(req.url, url)
            self.assertEqual(req.meta, {})

    @defer.inlineCallbacks
    def test_setting_proxies(self):

        http_proxy = 'https://proxy.for.http:3128'
        https_proxy = 'http://proxy.for.https:8080'
        settings = Settings({'HTTP_PROXIES': [http_proxy], 'HTTPS_PROXIES': [https_proxy]})

        crawler = Crawler(spider, settings)
        mw = RotatedProxy(crawler)

        for url, proxy in [('http://e.com', http_proxy),
                ('https://e.com', https_proxy), ('file://tmp/a', None)]:
            req = Request(url)
            res = yield mw.process_request(req, spider)
            assert res is None
            self.assertEqual(req.url, url)
            self.assertEqual(req.meta.get('proxy'), proxy)

    @defer.inlineCallbacks
    def test_proxy_precedence_meta(self):
        settings = Settings({'HTTP_PROXIES': ['https://proxy.com']})
        crawler = Crawler(spider, settings)
        mw = RotatedProxy(crawler)
        req = Request('http://scrapytest.org', meta={'proxy': 'https://new.proxy:3128'})
        res = yield mw.process_request(req, spider)
        assert res is None
        self.assertEqual(req.meta, {'proxy': 'https://new.proxy:3128'})

    @defer.inlineCallbacks
    def test_proxy_auth(self):
        settings = Settings({'HTTP_PROXIES': ['https://user:pass@proxy:3128']})
        crawler = Crawler(spider, settings)
        mw = RotatedProxy(crawler)
        req = Request('http://scrapytest.org')
        res = yield mw.process_request(req, spider)
        assert res is None
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'), b'Basic dXNlcjpwYXNz')
        # proxy from request.meta
        req = Request('http://scrapytest.org', meta={'proxy': 'https://username:password@proxy:3128'})
        res = yield mw.process_request(req, spider)
        assert res is None
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'), b'Basic dXNlcm5hbWU6cGFzc3dvcmQ=')

    @defer.inlineCallbacks
    def test_proxy_auth_empty_passwd(self):
        settings = Settings({'HTTP_PROXIES': ['https://user:@proxy:3128']})
        crawler = Crawler(spider, settings)
        mw = RotatedProxy(crawler)
        req = Request('http://scrapytest.org')
        res = yield mw.process_request(req, spider)
        assert res is None
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'), b'Basic dXNlcjo=')
        # proxy from request.meta
        req = Request('http://scrapytest.org', meta={'proxy': 'https://username:@proxy:3128'})
        res = yield mw.process_request(req, spider)
        assert res is None
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'), b'Basic dXNlcm5hbWU6')

    @defer.inlineCallbacks
    def test_proxy_auth_encoding(self):
        # utf-8 encoding
        settings = Settings({'HTTP_PROXIES': [u'https://m\u00E1n:pass@proxy:3128']})
        crawler = Crawler(spider, settings)
        mw = RotatedProxy(crawler, auth_encoding='utf-8')
        req = Request('http://scrapytest.org')
        res = yield mw.process_request(req, spider)
        assert res is None
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'), b'Basic bcOhbjpwYXNz')

        # proxy from request.meta
        req = Request('http://scrapytest.org', meta={'proxy': u'https://\u00FCser:pass@proxy:3128'})
        res = yield mw.process_request(req, spider)
        assert res is None
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'), b'Basic w7xzZXI6cGFzcw==')

        # default latin-1 encoding
        mw = RotatedProxy(crawler, auth_encoding='latin-1')
        req = Request('http://scrapytest.org')
        res = yield mw.process_request(req, spider)
        assert res is None
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'), b'Basic beFuOnBhc3M=')

        # proxy from request.meta, latin-1 encoding
        req = Request('http://scrapytest.org', meta={'proxy': u'https://\u00FCser:pass@proxy:3128'})
        res = yield mw.process_request(req, spider)
        assert res is None
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'), b'Basic /HNlcjpwYXNz')

    @defer.inlineCallbacks
    def test_proxy_already_seted(self):
        settings = Settings({'HTTP_PROXIES': ['https://proxy.for.http:3128']})
        crawler = Crawler(spider, settings)
        mw = RotatedProxy(crawler)
        req = Request('http://noproxy.com', meta={'proxy': None})
        res = yield mw.process_request(req, spider)
        assert res is None
        assert 'proxy' in req.meta and req.meta['proxy'] is None


    @defer.inlineCallbacks
    def test_proxy_rotation(self):
        settings = Settings({'HTTP_PROXIES': ['https://proxy1.for.http:3128', 'https://proxy2.for.http:3128']})
        crawler = Crawler(spider, settings)
        mw = RotatedProxy(crawler)
        req1 = Request('http://scrapytest.org')
        req2 = Request('http://scrapytest.org')
        req3 = Request('http://scrapytest.org')
        res1 = yield mw.process_request(req1, spider)
        res2 = yield mw.process_request(req2, spider)
        res3 = yield mw.process_request(req3, spider)
        assert res1 is None
        assert res2 is None
        assert res3 is None
        res_list = [{'proxy': 'https://proxy1.for.http:3128'}, {'proxy': 'https://proxy2.for.http:3128'}]
        self.assertIn(req1.meta, res_list)
        self.assertIn(req2.meta, res_list)
        self.assertIn(req3.meta, res_list)
        self.assertNotEqual(req1.meta, req2.meta)
        self.assertEqual(req1.meta, req3.meta)

    @defer.inlineCallbacks
    def test_multi_scheme(self):
        settings = Settings({'HTTP_PROXIES': ['https://proxy1.for.http:3128'], 'HTTPS_PROXIES': ['https://proxy2.for.http:3128']})
        crawler = Crawler(spider, settings)
        mw = RotatedProxy(crawler)
        req_http = Request('http://scrapytest.org')
        req_https = Request('https://scrapytest.org')
        res_http = yield mw.process_request(req_http, spider)
        res_https = yield mw.process_request(req_https, spider)
        assert res_http is None
        assert res_https is None
        self.assertEqual(req_http.meta, {'proxy': 'https://proxy1.for.http:3128'})
        self.assertEqual(req_https.meta, {'proxy': 'https://proxy2.for.http:3128'})

