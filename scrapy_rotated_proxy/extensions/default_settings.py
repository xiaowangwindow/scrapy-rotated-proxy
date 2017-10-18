# DOWNLOADER_MIDDLEWARES = {}
# DOWNLOADER_MIDDLEWARES.update({
#     'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
#     'scrapy_rotated_proxy.downloadmiddlwares.proxy.RotatedProxyMiddleware': 750,
# })

# default use Spider Settings Proxy
PROXY_STORAGE = 'scrapy_rotated_proxy.extensions.file_storage.FileProxyStorage'
PROXY_FILE_PATH = ''

# PROXY_STORAGE = 'scrapy_rotated_proxy.extensions.mongodb_storage.MongoDBProxyStorage'
PROXY_MONGODB_STORAGE_URI = 'mongodb://127.0.0.1:27017'
PROXY_MONGODB_STORAGE_DB = 'vps_management'
PROXY_MONGODB_STORAGE_COLL = 'service'
PROXY_MONGODB_STORAGE_COLL_INDEX = []


# settings_proxy.txt
# {
#     "HTTP_PROXIES": [
#         "http://host:ip"
#     ],
#     "HTTPS_PROXIES": [
#         "http://auth@host:ip"
#     ]
# }

