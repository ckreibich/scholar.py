#!/usr/bin/env python
#coding: utf-8

from pip.req import parse_requirements
from setuptools import setup

reqs = parse_requirements("requirements.txt")
install_reqs = filter(bool,[str(ir.req) for ir in reqs])

setup(
	name = "scholar",
	author = "",
	author_email = "",
	version = "2.10",
	license = "BSD",
	url = "https://github.com/ckreibich/scholar.py",
	download_url = "https://github.com/ckreibich/scholar.py",
	description = "scholar.py is a Python module that implements a querier and parser for Google Scholar's output. Its classes can be used independently, but it can also be invoked as a command-line tool.",
	long_description=open('README.md').read(),
    scripts=['bin/scholar.py' ],
	py_modules = ["scholar"],
	install_requires=install_reqs,
)
