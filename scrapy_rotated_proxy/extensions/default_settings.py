# DOWNLOADER_MIDDLEWARES = {}

PROXY_STORAGE = 'scrapy_rotated_proxy.extensions.file_storage.FileProxyStorage'
PROXY_FILE_PATH = ''
# PROXY_STORAGE = 'scrapy_rotated_proxy.extensions.mongodb_storage.MongoDBProxyStorage'
PROXY_MONGODB_STORAGE_URI = 'mongodb://10.255.0.0:27017'
PROXY_MONGODB_STORAGE_DB = 'vps_management'
PROXY_MONGODB_STORAGE_COLL = 'service'
PROXY_MONGODB_STORAGE_COLL_INDEX = []
# DOWNLOADER_MIDDLEWARES.update({
#     'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
#     'scrapy_rotated_proxy.proxy.RotatedProxy': 100,
# })


# settings_proxy.txt
# {
#     "HTTP_PROXIES": [
#         "http://10.255.0.2:57777"
#     ],
#     "HTTPS_PROXIES": [
#         "http://10.255.0.2:57777"
#     ]
# }

