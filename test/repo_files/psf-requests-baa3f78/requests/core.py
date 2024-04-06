# -*- coding: utf-8 -*-

"""
requests.core
~~~~~~~~~~~~~

This module implements the main Requests system.

:copyright: (c) 2011 by Kenneth Reitz.
:license: ISC, see LICENSE for more details.

"""

__title__ = 'requests'
__version__ = '0.6.6'
__build__ = 0x000606
__author__ = 'Kenneth Reitz'
__license__ = 'ISC'
__copyright__ = 'Copyright 2011 Kenneth Reitz'


from . import utils
from .models import HTTPError, Request, Response
from .api import request, get, head, post, patch, put, delete
from .sessions import session
from .status_codes import codes
from .config import settings
from .exceptions import (
    RequestException, AuthenticationError, Timeout, URLRequired,
    InvalidMethod, TooManyRedirects
)
