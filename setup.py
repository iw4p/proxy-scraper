from setuptools import setup

setup(
    name='proxyz',
    version='0.2.0',
    py_modules=['proxyScraper', 'proxyChecker'],
    install_requires=[
        'httpx',
        'beautifulsoup4',
        'pysocks',
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
    description='scrape proxies from more than 5 different sources and check which ones are still alive',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/iw4p/proxy-scraper',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
