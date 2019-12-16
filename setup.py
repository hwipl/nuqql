#!/usr/bin/env python3

"""
nuqql setup file
"""

from setuptools import setup

VERSION = "0.7"
DESCRIPTION = "Command line instant messenger inspired by centericq/centerim"
with open("README.md", 'r') as f:
    LONG_DESCRIPTION = f.read()
CLASSIFIERS = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
]

setup(
    name="nuqql",
    version=VERSION,
    description=DESCRIPTION,
    license="MIT",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="hwipl",
    author_email="nuqql@hwipl.net",
    url="https://github.com/hwipl/nuqql",
    packages=["nuqql", "nuqql.tools"],
    entry_points={
        "console_scripts": ["nuqql = nuqql.main:run",
                            "nuqql-keys = nuqql.tools.nuqql_keys:main"]
    },
    classifiers=CLASSIFIERS,
    python_requires='>=3.6',
)
