# -*- coding: utf-8 -*-

"""
reqeusts.async
~~~~~~~~~~~~~~

This module contains an asyncronous replica of ``requests.api``, powered
by gevent. All API methods return a ``Request`` instance (as opposed to
``Response``). A list of requests can be sent with ``map()``.
"""

try:
    import gevent
    from gevent import monkey as curious_george
except ImportError:
    raise RuntimeError('Gevent is required for requests.async.')

# Monkey-patch.
curious_george.patch_all(thread=False)

from . import api
from .hooks import dispatch_hook
from .packages.urllib3.poolmanager import PoolManager


def _patched(f):
    """Patches a given api function to not send."""

    def wrapped(*args, **kwargs):
        return f(*args, _return_request=True, **kwargs)

    return wrapped


def _send(r, pools=None):
    """Dispatcher."""

    if pools:
        r._pools = pools

    r.send()

    # Post-request hook.
    r = dispatch_hook('post_request', r.hooks, r)

    # Response manipulation hook.
    r.response = dispatch_hook('response', r.hooks, r.response)

    return r.response

# Patched requests.api functions.
get = _patched(api.get)
head = _patched(api.head)
post = _patched(api.post)
put = _patched(api.put)
patch = _patched(api.patch)
delete = _patched(api.delete)
request = _patched(api.request)

from requests.sessions import session

def map(requests, keep_alive=False):
    """Sends the requests... Asynchronously."""

    if keep_alive:
        pools = PoolManager(num_pools=len(requests), maxsize=1)
    else:
        pools = None

    jobs = [gevent.spawn(_send, r, pools=pools) for r in requests]
    gevent.joinall(jobs)

    return [r.response for r in requests]


