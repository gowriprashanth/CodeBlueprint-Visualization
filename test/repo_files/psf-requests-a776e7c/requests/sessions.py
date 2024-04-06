# -*- coding: utf-8 -*-

"""
requests.session
~~~~~~~~~~~~~~~~

This module provides a Session object to manage and persist settings across
requests (cookies, auth, proxies).

"""

from .compat import cookielib
from .cookies import cookiejar_from_dict, remove_cookie_by_name
from .models import Request
from .hooks import dispatch_hook, default_hooks
from .utils import header_expand, from_key_val_list, default_headers
from .exceptions import TooManyRedirects

from .compat import urlparse, urljoin
from .adapters import HTTPAdapter

from .utils import requote_uri

from .status_codes import codes
REDIRECT_STATI = (codes.moved, codes.found, codes.other, codes.temporary_moved)
DEFAULT_REDIRECT_LIMIT = 30


def merge_kwargs(local_kwarg, default_kwarg):
    """Merges kwarg dictionaries.

    If a local key in the dictionary is set to None, it will be removed.
    """

    if default_kwarg is None:
        return local_kwarg

    if isinstance(local_kwarg, str):
        return local_kwarg

    if local_kwarg is None:
        return default_kwarg

    # Bypass if not a dictionary (e.g. timeout)
    if not hasattr(default_kwarg, 'items'):
        return local_kwarg

    default_kwarg = from_key_val_list(default_kwarg)
    local_kwarg = from_key_val_list(local_kwarg)

    # Update new values.
    kwargs = default_kwarg.copy()
    kwargs.update(local_kwarg)

    # Remove keys that are set to None.
    for (k, v) in local_kwarg.items():
        if v is None:
            del kwargs[k]

    return kwargs


class SessionRedirectMixin(object):

    def resolve_redirects(self, resp, req, prefetch=True, timeout=None, verify=True, cert=None):
        """Receives a Response. Returns a generator of Responses."""

        i = 0

        # ((resp.status_code is codes.see_other))
        while (('location' in resp.headers and resp.status_code in REDIRECT_STATI)):

            resp.content  # Consume socket so it can be released

            if i > self.max_redirects:
                raise TooManyRedirects()

            # Release the connection back into the pool.
            resp.close()

            url = resp.headers['location']
            method = req.method

            # Handle redirection without scheme (see: RFC 1808 Section 4)
            if url.startswith('//'):
                parsed_rurl = urlparse(resp.url)
                url = '%s:%s' % (parsed_rurl.scheme, url)

            # Facilitate non-RFC2616-compliant 'location' headers
            # (e.g. '/path/to/resource' instead of 'http://domain.tld/path/to/resource')
            if not urlparse(url).netloc:
                # Compliant with RFC3986, we percent encode the url.
                url = urljoin(resp.url, requote_uri(url))

            # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.3.4
            if resp.status_code is codes.see_other:
                method = 'GET'

            # Do what the browsers do, despite standards...
            if resp.status_code in (codes.moved, codes.found) and req.method == 'POST':
                method = 'GET'

            if (resp.status_code == 303) and req.method != 'HEAD':
                method = 'GET'

            # Remove the cookie headers that were sent.
            # headers = req.headers
            # try:
            #     del headers['Cookie']
            # except KeyError:
            #     pass

            resp = self.request(
                    url=url,
                    method=method,
                    params=req.params,
                    auth=req.auth,
                    cookies=req.cookies,
                    allow_redirects=False,
                    prefetch=prefetch,
                    timeout=timeout,
                    verify=verify,
                    cert=cert
                )

            i += 1
            yield resp


class Session(SessionRedirectMixin):
    """A Requests session."""

    __attrs__ = [
        'headers', 'cookies', 'auth', 'timeout', 'proxies', 'hooks',
        'params', 'verify', 'cert', 'prefetch']

    def __init__(self):

        #: A case-insensitive dictionary of headers to be sent on each
        #: :class:`Request <Request>` sent from this
        #: :class:`Session <Session>`.
        self.headers = default_headers()

        #: Authentication tuple or object to attach to
        #: :class:`Request <Request>`.
        self.auth = None

        #: Dictionary mapping protocol to the URL of the proxy (e.g.
        #: {'http': 'foo.bar:3128'}) to be used on each
        #: :class:`Request <Request>`.
        self.proxies = {}

        #: Event-handling hooks.
        self.hooks = default_hooks()

        #: Dictionary of querystring data to attach to each
        #: :class:`Request <Request>`. The dictionary values may be lists for
        #: representing multivalued query parameters.
        self.params = {}

        #: Prefetch response content.
        self.prefetch = True

        #: SSL Verification.
        self.verify = True

        #: SSL certificate.
        self.cert = None

        #: Maximum number of redirects to follow.
        self.max_redirects = DEFAULT_REDIRECT_LIMIT

        #: Should we trust the environment
        self.trust_env = True

        # Set up a CookieJar to be used by default
        self.cookies = cookiejar_from_dict({})

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def request(self, method, url,
        params=None,
        data=None,
        headers=None,
        cookies=None or {},
        files=None,
        auth=None,
        timeout=None,
        allow_redirects=True,
        proxies=None,
        hooks=None,
        return_response=True,
        prefetch=None,
        verify=None,
        cert=None):


        # merge session cookies into passed-in ones
        dead_cookies = None
        # passed-in cookies must become a CookieJar:
        if not isinstance(cookies, cookielib.CookieJar):
            cookies = cookiejar_from_dict(cookies)
            # support unsetting cookies that have been passed in with None values
            # this is only meaningful when `cookies` is a dict ---
            # for a real CookieJar, the client should use session.cookies.clear()
            if cookies is not None:
                dead_cookies = [name for name in cookies if cookies[name] is None]
        # merge the session's cookies into the passed-in cookies:
        for cookie in self.cookies:
            cookies.set_cookie(cookie)
        # remove the unset cookies from the jar we'll be using with the current request
        # (but not from the session's own store of cookies):
        if dead_cookies is not None:
            for name in dead_cookies:
                remove_cookie_by_name(cookies, name)

        # Merge local kwargs with session kwargs.
        for attr in self.__attrs__:
            # we already merged cookies:
            if attr == 'cookies':
                continue

            session_val = getattr(self, attr, None)
            local_val = locals().get(attr)
            locals()[attr] = merge_kwargs(local_val, session_val)


        headers = merge_kwargs(headers, self.headers)

        req = Request()
        req.method = method
        req.url = url
        req.headers = headers
        req.files = files
        req.data = data
        req.params = params
        req.auth = auth
        req.cookies = cookies
        # TODO: move to attached
        # req.allow_redirects = allow_redirects
        # req.proxies = proxies
        req.hooks = hooks

        prep = req.prepare()

        # TODO: prepare cookies.

        resp = self.send(prep, prefetch=prefetch, timeout=timeout, verify=verify, cert=cert)

        # Redirect resolving generator.
        gen = self.resolve_redirects(resp, req, prefetch, timeout, verify, cert)

        # Resolve redirects if allowed.
        history = [r for r in gen] if allow_redirects else []

        # Shuffle things around if there's history.
        if history:
            history.insert(0, resp)
            resp = history.pop()
            resp.history = tuple(history)

        # Response manipulation hook.
        self.response = dispatch_hook('response', hooks, resp)

        return resp




    def get(self, url, **kwargs):
        """Sends a GET request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        kwargs.setdefault('allow_redirects', True)
        return self.request('GET', url, **kwargs)

    def options(self, url, **kwargs):
        """Sends a OPTIONS request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        kwargs.setdefault('allow_redirects', True)
        return self.request('OPTIONS', url, **kwargs)

    def head(self, url, **kwargs):
        """Sends a HEAD request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        kwargs.setdefault('allow_redirects', False)
        return self.request('HEAD', url, **kwargs)

    def post(self, url, data=None, **kwargs):
        """Sends a POST request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary or bytes to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        return self.request('POST', url, data=data, **kwargs)

    def put(self, url, data=None, **kwargs):
        """Sends a PUT request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary or bytes to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        return self.request('PUT', url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        """Sends a PATCH request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary or bytes to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        return self.request('PATCH', url,  data=data, **kwargs)

    def delete(self, url, **kwargs):
        """Sends a DELETE request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        return self.request('DELETE', url, **kwargs)

    def send(self, request, prefetch=True, timeout=None, verify=True, cert=None):
        """Send a given PreparedRequest."""
        adapter = HTTPAdapter()
        r = adapter.send(request, prefetch, timeout, verify, cert)
        return r

    def __getstate__(self):
        return dict((attr, getattr(self, attr, None)) for attr in self.__attrs__)

    def __setstate__(self, state):
        for attr, value in state.items():
            setattr(self, attr, value)

        self.init_poolmanager()


def session(**kwargs):
    """Returns a :class:`Session` for context-management."""

    return Session(**kwargs)