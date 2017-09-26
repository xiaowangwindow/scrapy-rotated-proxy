======
Scrapy-Rotated-Proxy
======


Overview
========

Scrapy-Rotated-Proxy is a middleware to dynamically configure Request proxy for Scrapy.
It can used when you have multi proxy ip, and need to attach rotated proxy to each Request.

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

In `settings.py`, for example:
```

ROTATED_PROXY_ENABLED = True

HTTP_PROXY = [
    'http://proxy0:8888',
    'http://user:pass@proxy1:8888',
    'https://user:pass@proxy1:8888',
]

HTTPS_PROXY = [
    'http://proxy0:8888',
    'http://user:pass@proxy1:8888',
    'https://user:pass@proxy1:8888',
]

```
