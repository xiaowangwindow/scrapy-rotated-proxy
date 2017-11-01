====================
Scrapy-Rotated-Proxy
====================

.. image:: https://img.shields.io/pypi/v/scrapy-rotated-proxy.svg
   :target: https://pypi.python.org/pypi/scrapy-rotated-proxy
   :alt: PyPI Version

.. image:: https://img.shields.io/travis/xiaowangwindow/scrapy-rotated-proxy/master.svg
   :target: http://travis-ci.org/xiaowangwindow/scrapy-rotated-proxy
   :alt: Build Status

Overview
########

Scrapy-Rotated-Proxy is a Scrapy downloadmiddleware to dynamically attach proxy to Request,
which can repeately use rotated proxies supplied by configuration.
It can temporarily block unavailable proxy ip
and retrieve to use in the future when the proxy is available.
Also, it can remove invalid proxy ip through Scrapy signal.
Proxy ip list can be supplied through Spider Settings, File or MongoDB.

Requirements
############

* Python 2.7 or Python 3.3+
* Works on Linux, Windows, Mac OSX, BSD

Install
########

The quick way::

    pip install scrapy-rotated-proxy

OR copy this middleware to your scrapy project.

Configuration
#############

In settings.py, for example:

Basic Configuration
===================

Enable with Spider Settings
---------------------------

enable scrapy-rotated-proxy middleware and supply proxy ip list through Spider Settings

::

    # -----------------------------------------------------------------------------
    # ROTATED PROXY SETTINGS (Spider Settings Backend)
    # -----------------------------------------------------------------------------
    DOWNLOADER_MIDDLEWARES.update({
        'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
        'scrapy_rotated_proxy.downloadmiddlewares.proxy.RotatedProxyMiddleware': 750,
    })
    ROTATED_PROXY_ENABLED = True
    PROXY_STORAGE = 'scrapy_rotated_proxy.extensions.file_storage.FileProxyStorage'
    # When set PROXY_FILE_PATH='', scrapy-rotated-proxy
    # will use proxy in Spider Settings default.
    PROXY_FILE_PATH = ''
    HTTP_PROXIES = [
        'http://proxy0:8888',
        'http://user:pass@proxy1:8888',
        'https://user:pass@proxy1:8888',
    ]
    HTTPS_PROXIES = [
        'http://proxy0:8888',
        'http://user:pass@proxy1:8888',
        'https://user:pass@proxy1:8888',
    ]

Enable with Local File
-----------------------

enable scrapy-rotated-proxy middleware and supply proxy ip list through Local File

::

    # -----------------------------------------------------------------------------
    # ROTATED PROXY SETTINGS (Local File Backend)
    # -----------------------------------------------------------------------------
    DOWNLOADER_MIDDLEWARES.update({
        'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
        'scrapy_rotated_proxy.downloadmiddlewares.proxy.RotatedProxyMiddleware': 750,
    })
    ROTATED_PROXY_ENABLED = True
    PROXY_STORAGE = 'scrapy_rotated_proxy.extensions.file_storage.FileProxyStorage'
    PROXY_FILE_PATH = 'file_path/proxy.txt'

local file store proxy list with json style

::

    # proxy file content, must conform to json format, otherwise will cause json
    # load error
    HTTP_PROXIES = [
        'http://proxy0:8888',
        'http://user:pass@proxy1:8888',
        'https://user:pass@proxy1:8888'
    ]
    HTTPS_PROXIES = [
        'http://proxy0:8888',
        'http://user:pass@proxy1:8888',
        'https://user:pass@proxy1:8888'
    ]

Enable with MongoDB
-------------------

enable `scrapy-rotated-proxy` middleware and supply proxy ip list through MongoDB

::

    # -----------------------------------------------------------------------------
    # ROTATED PROXY SETTINGS (MongoDB Backend)
    # -----------------------------------------------------------------------------
    # mongodb document required field: scheme, ip, port, username, password
    # document example: {'scheme': 'http', 'ip': '10.0.0.1', 'port': 8080,
    # 'username':'user', 'password':'password'}
    DOWNLOADER_MIDDLEWARES.update({
        'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
        'scrapy_rotated_proxy.downloadmiddlewares.proxy.RotatedProxyMiddleware': 750,
    })
    ROTATED_PROXY_ENABLED = True
    PROXY_STORAGE = 'scrapy_rotated_proxy.extensions.mongodb_storage.MongoDBProxyStorage'
    PROXY_MONGODB_HOST = HOST_OR_IP
    PROXY_MONGODB_PORT = 27017
    PROXY_MONGODB_USERNAME = USERNAME_OR_NONE
    PROXY_MONGODB_PASSWORD = PASSWORD_OR_NONE
    PROXY_MONGODB_DB = 'vps_management'
    PROXY_MONGODB_COLL = 'service'

Advanced Configuration
======================
Block Settings
--------------

Default, spider will close when run out of all proxies. you can config spider to
wait until block proxies become valid, which you block by signal

::

    # -----------------------------------------------------------------------------
    # OTHER SETTINGS (Optional)
    # -----------------------------------------------------------------------------
    PROXY_SLEEP_INTERVAL = 60*60*24  # Default 24hours
    PROXY_SPIDER_CLOSE_WHEN_NO_PROXY = False # Default True

Signals
-------

Remove proxy that never be used in the spider, you can send signal to
**scrapy_rotated_proxy.signals.proxy_remove**, which signal must contains arguments
including ``spider``, ``request``, ``exception``

Block proxy that can be used in the future after sleep interval reach, you can send signal to
**scrapy_rotated_proxy.signals.proxy_block**, which signal must contains arguments
including ``spider``, ``response``, ``exception``

Settings Reference
###################
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| Setting                          | Description                                                                              | Default          |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| ROTATED_PROXY_ENABLED            | Whether to enable Scrapy-Rotated-Proxy                                                   | True             |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| PROXY_STORAGE                    | A class which implements the proxy storage backend                                       | FileProxyStorage |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| PROXY_MONGODB_HOST               | MongoDB host for MongoDB backend                                                         | '127.0.0.1'      |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| PROXY_MONGODB_PORT               | MongoDB port for MongoDB backend                                                         | 27017            |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| PROXY_MONGODB_USERNAME           | MongoDB username for MongoDB backend                                                     | None             |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| PROXY_MOGNODB_PASSWORD           | MongoDB password for MongoDB backend                                                     | None             |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| PROXY_MONGODB_DB                 | MongoDB database name for MongoDB backend                                                | proxy_management |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| PROXY_MONGODB_COLL               | MongoDB collection name for MongoDB backend                                              | proxy            |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| PROXY_MONGODB_OPTIONS_*          | MongoDB uri options for MongoDB backend                                                  |                  |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| PROXY_FILE_PATH                  | Path of file that store proxies. default is None, means get proxies from Spider Settings | None             |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| HTTP_PROXIES                     | keywords of HTTP proxies for LocalFile backend or Spider Settings                        |                  |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| HTTPS_PROXIES                    | keywords of HTTPS proxies for LocalFile backend or Spider Settings                       |                  |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| PROXY_SLEEP_INTERVAL             | Time to sleep for blocked proxy become available                                         | 60*60*24         |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+
| PROXY_SPIDER_CLOSE_WHEN_NO_PROXY | Where to close spider when run out of all proxies                                        | True             |
+----------------------------------+------------------------------------------------------------------------------------------+------------------+

