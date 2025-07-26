from setuptools import setup

setup(
    name='proxyz',
    version='0.3.0',
    py_modules=['proxyScraper', 'proxyChecker'],
    install_requires=[
        'httpx>=0.23.0,<1.0.0',
        'beautifulsoup4>=4.11.1,<5.0.0',
        'pysocks>=1.7.1,<2.0.0',
    ],
    entry_points={
        'console_scripts': [
            'proxy_scraper=proxyScraper:main',
            'proxy_checker=proxyChecker:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['user_agents.txt'],
    },
    author='Nima Akbarzadeh',
    author_email='iw4p@protonmail.com',
    description='scrape proxies from more than 12 different sources and check which ones are still alive',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/iw4p/proxy-scraper',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
