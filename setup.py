#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pipenv install twine --dev

import io
import os

from setuptools import setup

# Package meta-data.
NAME = "geocortex-reporting-client"
DESCRIPTION = "A Python client for running Geocortex Reporting jobs."
URL = "https://github.com/geocortex/geocortex-reporting-client-py"
EMAIL = "packages@geocortex.com"
AUTHOR = "VertiGIS"
REQUIRES_PYTHON = ">=3.6.0"
VERSION = "0.1.1"

# What packages are required for this module to be executed?
REQUIRED = ["requests>=2.24.0,<3", "websockets>=8.1,<9"]

# What packages are optional?
DEV_EXTRAS = ["aiounittest>=1.4.0,<2", "black>=19.10b", "pylint>=2.5.3,<3", "responses>=0.10.16,<0.11"]

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    project_slug = NAME.lower().replace("-", "_").replace(" ", "_")
    with open(os.path.join(here, project_slug, "__version__.py")) as f:
        exec(f.read(), about)
else:
    about["__version__"] = VERSION


# Where the magic happens:
setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=["geocortex.reporting.client"],
    install_requires=REQUIRED,
    extras_require={"dev": DEV_EXTRAS},
    include_package_data=True,
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
