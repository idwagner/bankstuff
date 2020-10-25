import os
import re

from setuptools import setup, find_packages

ROOT = os.path.dirname(__file__)

requires = [
    "click>=6.7<7.1",
    "google-api-python-client>=1.7.4<2.0.0",
    "requests>=2.22.0<3.0",
    "requests-oauthlib>=1.3.0<2.0",
    "PyYAML>=5.1.2<6.0",
    "oauthlib>=3.0.0",
    "google-auth-oauthlib>=0.4.1,<0.5",
    "google-auth>=1.19.2<1.2",
    "pynab==0.1.1",
    "coloredlogs==14.0"
]


setup(
    name='bankutil',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    dependency_links=[
        "https://github.com/idwagner/pynab/releases/download/0.1.1/pynab-0.1.1.tar.gz#egg=pynab-0.1.1"
    ],
    entry_points={
        'console_scripts': [
            'bank = bankutil.cli:main'
        ]
    },
    install_requires=get_requirements(),
)
