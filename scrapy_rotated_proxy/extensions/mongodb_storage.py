from itertools import cycle

from twisted.internet import defer
from six.moves.urllib.parse import urlunparse
from twisted.internet.defer import returnValue

from scrapy_rotated_proxy import util
from scrapy_rotated_proxy.extensions.base_storage import BaseStorage


class MongoDBProxyStorage(BaseStorage):
    def __init__(self, settings, auth_encoding='latin-1'):
        super(MongoDBProxyStorage, self).__init__(
            settings,
            'PROXY_MONGODB_STORAGE_URI',
            'PROXY_MONGODB_STORAGE_DB',
            'PROXY_MONGODB_STORAGE_COLL',
            'PROXY_MONGODB_STORAGE_COLL_INDEX')
        self.auth_encoding = auth_encoding

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

