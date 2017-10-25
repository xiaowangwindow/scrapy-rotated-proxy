# DOWNLOADER_MIDDLEWARES = {}
# DOWNLOADER_MIDDLEWARES.update({
#     'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
#     'scrapy_rotated_proxy.downloadmiddlwares.proxy.RotatedProxyMiddleware': 750,
# })

# default use Spider Settings Proxy
# PROXY_STORAGE = 'scrapy_rotated_proxy.extensions.file_storage.FileProxyStorage'
# PROXY_FILE_PATH = ''

PROXY_STORAGE = 'scrapy_rotated_proxy.extensions.mongodb_storage.MongoDBProxyStorage'
PROXY_MONGODB_HOST = '127.0.0.1'
PROXY_MONGODB_PORT = 27017
PROXY_MONGODB_USERNAME = None
PROXY_MONGODB_PASSWORD = None
PROXY_MONGODB_AUTH_DB = 'admin'
PROXY_MONGODB_DB = 'vps_management'
PROXY_MONGODB_COLL = 'service'
PROXY_MONGODB_COLL_INDEX = []
PROXY_SLEEP_INTERVAL = 60

# settings_proxy.txt
# {
#     "HTTP_PROXIES": [
#         "http://host:ip"
#     ],
#     "HTTPS_PROXIES": [
#         "http://auth@host:ip"
#     ]
# }

