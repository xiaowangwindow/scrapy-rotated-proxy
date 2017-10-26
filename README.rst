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
========

Scrapy-Rotated-Proxy is a middleware to dynamically configure Request proxy for Scrapy.
It can used when you have multi proxy ip, and need to attach rotated proxy to each Request.
Scrapy-Rotated-Proxy support multi backend storage, you can provide proxy ip
list through Spider Settings, File or MongoDB.

Requirements
============

* Python 2.7 or Python 3.3+
* Works on Linux, Windows, Mac OSX, BSD

Install
=======

The quick way::

    pip install scrapy-rotated-proxy

OR copy this middleware to your scrapy project.

Documentation
=============

In settings.py, for example::

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

    # -----------------------------------------------------------------------------
    # OTHER SETTINGS (Optional)
    # -----------------------------------------------------------------------------
    # if you want to wait proxy become valid after all proxies are blocked,
    # you can set wait flag `PROXY_SPIDER_CLOSE_WHEN_NO_PROXY` to False and interval to wait.
    # otherwise, you can set `PROXY_SPIDER_CLOSE_WHEN_NO_PROXY` to True, it's default setting.
    PROXY_SLEEP_INTERVAL = 60
    PROXY_SPIDER_CLOSE_WHEN_NO_PROXY = False
