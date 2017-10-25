import logging
from itertools import cycle

from twisted.internet import defer
from six.moves.urllib.parse import urlunparse
from twisted.internet.defer import returnValue
from txmongo.connection import ConnectionPool
from txmongo import filter as qf

from scrapy_rotated_proxy import util
from scrapy_rotated_proxy.extensions import default_settings


logger = logging.getLogger(__name__)

class MongoDBProxyStorage():

    def __init__(self, settings, auth_encoding='latin-1'):
        self.settings = settings
        self.auth_encoding = auth_encoding
        db_key = 'PROXY_MONGODB_DB'
        coll_key = 'PROXY_MONGODB_COLL'
        index_key = 'PROXY_MONGODB_COLL_INDEX'
        self.db_uri = 'mongodb://{account}{path}{options}'.format(
            account=self._gen_mongo_account(),
            path=self._gen_mongo_path(),
            options=self._gen_mongo_option()
        )
        self.db_name = settings.get(db_key, getattr(default_settings, db_key))
        self.coll_name = settings.get(coll_key,
                                      getattr(default_settings, coll_key))
        if index_key:
            self.db_index = settings.get(index_key,
                                         getattr(default_settings, index_key))
        self._db_client = None
        self._db = None
        self._coll = None

    @defer.inlineCallbacks
    def open_spider(self, spider):
        self._db_client = yield ConnectionPool(self.db_uri)
        self._db = self._db_client[self.db_name]
        self._coll = self._db[self.coll_name]
        yield self._coll.find_one(timeout=True)
        for index in self.db_index:
            yield self._coll.create_index(qf.sort(index))
        logger.info('{storage} opened'.format(storage=self.__class__.__name__))

    @defer.inlineCallbacks
    def close_spider(self, spider):
        yield self._db_client.disconnect()
        logger.info('{storage} closed'.format(storage=self.__class__.__name__))

    @defer.inlineCallbacks
    def proxies(self):
        '''
        :return: Dict
            {'http': [(UserPassBase64, proxy1_url), (None, proxy2_url)], 'https': []}
        '''

        def _gen_proxy(scheme, host, port, user=None, password=None):
            proxy_url = urlunparse((scheme, '{host}:{port}'.format(host=host,
                                                                   port=port),
                                    '', '', '', ''))
            creds = util._basic_auth_header(user, password,
                                            self.auth_encoding) if user else None
            return creds, proxy_url

        res = {}
        for scheme in ['http', 'https']:
            proxy_list = yield self._coll.find({'scheme': scheme})
            res[scheme] = set(map(lambda proxy: _gen_proxy(proxy['scheme'],
                                                           proxy['ip'],
                                                           proxy['port'],
                                                           proxy['username'],
                                                           proxy['password']),
                                  proxy_list))
        returnValue(res)


    def _gen_mongo_account(self):
        username_key = 'PROXY_MONGODB_USERNAME'
        password_key = 'PROXY_MONGODB_PASSWORD'
        if all(map(lambda x: self.settings.get(x, getattr(default_settings, x)),
                   [username_key, password_key])):
            return '{username}:{password}@'.format(
                username=self.settings.get(username_key, getattr(default_settings, username_key)),
                password=self.settings.get(password_key, getattr(default_settings, password_key))
            )
        else:
            return ''

    def _gen_mongo_path(self):
        host_key = 'PROXY_MONGODB_HOST'
        port_key = 'PROXY_MONGODB_PORT'
        auth_db_key = 'PROXY_MONGODB_AUTH_DB'
        return '{host}:{port}/{auth_db}'.format(
            host=self.settings.get(host_key, getattr(default_settings, host_key)),
            port=self.settings.get(port_key, getattr(default_settings, port_key)),
            auth_db=self.settings.get(auth_db_key, getattr(default_settings, auth_db_key)) or ''
        )

    def _gen_mongo_option(self):
        option_prefix = 'PROXY_MONGODB_OPTIONS_'
        res = '&'.join(
            map(lambda x: '{option}={value}'.format(
                option=x[0].replace(option_prefix, '').lower(),
                value=x[1]
            ), filter(lambda x: x[0].startswith(option_prefix), self.settings.items()))
        )
        return '?' + res if res else ''
