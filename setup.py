from os.path import dirname, join
from pkg_resources import parse_version
from setuptools import setup, find_packages, __version__ as setuptools_version


with open(join(dirname(__file__), 'scrapy_rotated_proxy/VERSION'), 'rb') as f:
    version = f.read().decode('ascii').strip()


extras_require = {}

setup(
    name='scrapy-rotated-proxy',
    version=version,
    url='https://github.com/xiaowangwindow/scrapy-rotated-proxy',
    description='A middleware to change proxy rotated for Scrapy',
    long_description=open('README.rst').read(),
    author='Alex Wang',
    maintainer='Alex Wang',
    maintainer_email='xiaowangwindow@163.com',
    license='BSD',
    packages=find_packages(exclude=('tests', 'tests.*')),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Framework :: Scrapy',
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'scrapy>=1.4.0'
    ],
    extras_require=extras_require,
)
