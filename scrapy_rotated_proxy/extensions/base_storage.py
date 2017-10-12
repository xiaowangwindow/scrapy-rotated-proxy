import logging

from scrapy.settings import Settings
from scrapy import Spider
from twisted.internet import defer
from txmongo.connection import ConnectionPool
from txmongo import filter as qf
from scrapy_rotated_proxy.extensions import default_settings


class BaseStorage(object):
    def __init__(self, settings, uri_key, db_key, coll_key, index_key):
        self.db_uri = settings.get(uri_key, getattr(default_settings, uri_key))
        self.db_name = settings.get(db_key, getattr(default_settings, db_key))
        self.coll_name = settings.get(coll_key, getattr(default_settings, coll_key))
        if index_key:
            self.db_index = settings.get(index_key, getattr(default_settings, index_key))
        self._db_client = None
        self._db = None
        self._coll = None
        self.logger = logging.getLogger(self.__class__.__name__)

    @defer.inlineCallbacks
    def open_spider(self, spider):
        self._db_client = yield ConnectionPool(self.db_uri)
        self._db = self._db_client[self.db_name]
        self._coll = self._db[self.coll_name]
        for index in self.db_index:
            yield self._coll.create_index(qf.sort(index))
        self.logger.info('Spider opened: {spider_name}'.format(spider_name=spider.name, storage_name=self.__class__))

    @defer.inlineCallbacks
    def close_spider(self, spider):
        yield self._db_client.disconnect()
        self.logger.info('Spider closed: {spider_name}'.format(spider_name=spider.name, storage_name=self.__class__))

