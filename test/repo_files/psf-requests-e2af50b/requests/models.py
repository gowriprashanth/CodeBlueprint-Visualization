# -*- coding: utf-8 -*-

"""
requests.models
~~~~~~~~~~~~~~~

"""

import urllib
import zlib

from urlparse import urlparse, urlunparse, urljoin


from .packages import urllib3
# print dir(urllib3)

from ._config import get_config
from .structures import CaseInsensitiveDict
from .utils import *
from .status_codes import codes
from .exceptions import RequestException, Timeout, URLRequired, TooManyRedirects


REDIRECT_STATI = (codes.moved, codes.found, codes.other, codes.temporary_moved)


class Request(object):
    """The :class:`Request <Request>` object. It carries out all functionality of
    Requests. Recommended interface is with the Requests functions.
    """

    def __init__(self,
        url=None, headers=dict(), files=None, method=None, data=dict(),
        params=dict(), auth=None, cookies=None, timeout=None, redirect=False,
        allow_redirects=False, proxies=None, config=None):

        #: Float describ the timeout of the request.
        #  (Use socket.setdefaulttimeout() as fallback)
        self.timeout = timeout

        #: Request URL.
        self.url = url

        #: Dictonary of HTTP Headers to attach to the :class:`Request <Request>`.
        self.headers = headers

        #: Dictionary of files to multipart upload (``{filename: content}``).
        self.files = files

        #: HTTP Method to use.
        self.method = method

        #: Dictionary or byte of request body data to attach to the
        #: :class:`Request <Request>`.
        self.data = None

        #: Dictionary or byte of querystring data to attach to the
        #: :class:`Request <Request>`.
        self.params = None

        #: True if :class:`Request <Request>` is part of a redirect chain (disables history
        #: and HTTPError storage).
        self.redirect = redirect

        #: Set to True if full redirects are allowed (e.g. re-POST-ing of data at new ``Location``)
        self.allow_redirects = allow_redirects

        # Dictionary mapping protocol to the URL of the proxy (e.g. {'http': 'foo.bar:3128'})
        self.proxies = proxies

        self.config = get_config(config)

        self.data = data
        self._enc_data = encode_params(data)
        self.params = params
        self._enc_params = encode_params(params)

        #: :class:`Response <Response>` instance, containing
        #: content and metadata of HTTP Response, once :attr:`sent <send>`.
        self.response = Response()

        #: :class:`AuthObject` to attach to :class:`Request <Request>`.
        self.auth = auth

        #: CookieJar to attach to :class:`Request <Request>`.
        self.cookies = cookies

        #: True if Request has been sent.
        self.sent = False

        # Header manipulation and defaults.

        if self.config.get('accept_gzip'):
            self.headers.update({'Accept-Encoding': 'gzip'})

        if headers:
            headers = CaseInsensitiveDict(self.headers)
        else:
            headers = CaseInsensitiveDict()

        for (k, v) in self.config.get('base_headers').items():
            if k not in headers:
                headers[k] = v

        self.headers = headers

    def __repr__(self):
        return '<Request [%s]>' % (self.method)

    def _checks(self):
        """Deterministic checks for consistency."""

        if not self.url:
            raise URLRequired

    def _build_response(self, resp, is_error=False):
        """Build internal :class:`Response <Response>` object
        from given response.
        """

        def build(resp):

            response = Response()
            response.status_code = getattr(resp, 'status', None)

            try:
                response.headers = CaseInsensitiveDict(getattr(resp, 'headers', None))
                response.raw = resp

            except AttributeError:
                pass

            if is_error:
                response.error = resp

            return response

        # Request collector.
        history = []

        # Create the lone response object.
        r = build(resp)

        # Store the HTTP response, just in case.
        r._response = resp

        # It's a redirect, and we're not already in a redirect loop.
        if r.status_code in REDIRECT_STATI and not self.redirect:

            while (
                # There's a `Location` header.
                ('location' in r.headers) and

                # See other response.
                ((r.status_code is codes.see_other) or

                # Opt-in to redirects for non- idempotent methods.
                (self.allow_redirects))
            ):

                # print r.headers['location']
                # print dir(r.raw._original_response.fp)
                # print '--'

                # We already redirected. Don't keep it alive.
                # r.raw.close()

                # Woah, this is getting crazy.
                if len(history) >= settings.max_redirects:
                    raise TooManyRedirects()

                # Add the old request to the history collector.
                history.append(r)

                # Redirect to...
                url = r.headers['location']

                # Handle redirection without scheme (see: RFC 1808 Section 4)
                if url.startswith('//'):
                    parsed_rurl = urlparse(r.url)
                    url = '%s:%s' % (parsed_rurl.scheme, url)

                # Facilitate non-RFC2616-compliant 'location' headers
                # (e.g. '/path/to/resource' instead of 'http://domain.tld/path/to/resource')
                parsed_url = urlparse(url)
                if not parsed_url.netloc:
                    parsed_url = list(parsed_url)
                    parsed_url[2] = urllib.quote(parsed_url[2], safe="%/:=&?~#+!$,;'@()*[]")
                    url = urljoin(r.url, str(urlunparse(parsed_url)))

                # If 303, convert to idempotent GET.
                # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.3.4
                if r.status_code is codes.see_other:
                    method = 'GET'
                else:
                    method = self.method

                # Create the new Request.
                request = Request(
                    url=url,
                    headers=self.headers,
                    files=self.files,
                    method=method,
                    data=self.data,
                    # params=self.params,
                    params=None,
                    auth=self.auth,
                    cookies=self.cookies,

                    # Flag as part of a redirect loop.
                    redirect=True
                )

                # Send her away!
                request.send()
                r = request.response

            # Insert collected history.
            r.history = history

        # Attach Response to Request.
        self.response = r

        # Give Response some context.
        self.response.request = self



    def send(self, connection=None, anyway=False):
        """Sends the shit."""

        # Safety check.
        self._checks()

        # Build the final URL.
        url = build_url(self.url, self.params)

        print url
        # Setup Files.
        if self.files:
            pass

        # Setup form data.
        elif self.data:
            pass

        # Setup cookies.
        elif self.cookies:
            pass

        # Only send the Request if new or forced.
        if (anyway) or (not self.sent):

            try:
                # Create a new HTTP connection, since one wasn't passed in.
                if not connection:
                    connection = urllib3.connection_from_url(url, timeout=self.timeout)

                    # One-off request. Delay fetching the content until needed.
                    do_block = False
                else:
                    # Part of a connection pool, so no fancy stuff. Sorry!
                    do_block = True

                # Create the connection.
                r = connection.urlopen(
                    method=self.method,
                    url=url,
                    body=self.data,
                    headers=self.headers,
                    redirect=False,
                    assert_same_host=False,
                    # preload_content=True
                    # preload_content=False
                    preload_content=do_block
                )

                # Extract cookies.
                # if self.cookiejar is not None:
                    # self.cookiejar.extract_cookies(resp, req)

            # except (urllib2.HTTPError, urllib2.URLError), why:
            except Exception, why:
                print why.__dict__
                # if hasattr(why, 'reason'):
                #     if isinstance(why.reason, socket.timeout):
                #         why = Timeout(why)

                # self._build_response(why, is_error=True)
                print 'FUCK'
                print why

            else:
                # self.response = Response.from_urllib3()
                self._build_response(r)
                self.response.ok = True


        self.sent = self.response.ok

        return self.sent


class Response(object):
    """The core :class:`Response <Response>` object.


    All :class:`Request <Request>` objects contain a :class:`response
    <Response>` attribute, which is an instance of this class.
    """

    def __init__(self):

        self._content = None
        self._content_consumed = False

        #: Integer Code of responded HTTP Status.
        self.status_code = None

        #: Case-insensitive Dictionary of Response Headers.
        #: For example, ``headers['content-encoding']`` will return the
        #: value of a ``'Content-Encoding'`` response header.
        self.headers = CaseInsensitiveDict()

        #: File-like object representation of response (for advanced usage).
        self.raw = None

        #: True if no :attr:`error` occured.
        self.ok = False

        #: Resulting :class:`HTTPError` of request, if one occured.
        self.error = None

        #: A list of :class:`Response <Response>` objects from
        #: the history of the Request. Any redirect responses will end
        #: up here.
        self.history = []

        #: The :class:`Request <Request>` that created the Response.
        self.request = None

        #: A dictionary of Cookies the server sent back.
        self.cookies = None

    def __repr__(self):
        return '<Response [%s]>' % (self.status_code)

    def __nonzero__(self):
        """Returns true if :attr:`status_code` is 'OK'."""

        return not self.error

    def iter_content(self, chunk_size=10 * 1024, decode_unicode=None):
        """Iterates over the response data.  This avoids reading the content
        at once into memory for large responses.  The chunk size is the number
        of bytes it should read into memory.  This is not necessarily the
        length of each item returned as decoding can take place.
        """
        if self._content_consumed:
            raise RuntimeError('The content for this response was '
                               'already consumed')

        def generate():
            while 1:
                chunk = self.raw.read(chunk_size)
                if not chunk:
                    break
                yield chunk
            self._content_consumed = True
        gen = generate

        if 'gzip' in self.headers.get('content-encoding', ''):
            gen = stream_decode_gzip(gen)

        if decode_unicode is None:
            decode_unicode = settings.decode_unicode

        if decode_unicode:
            gen = stream_decode_response_unicode(gen, self)

        return gen


    @property
    def content(self):
        """Content of the response, in bytes or unicode
        (if available).
        """

        if self._content is not None:
            return self._content

        if self._content_consumed:
            raise RuntimeError(
                'The content for this response was already consumed')

        # Read the contents.
        self._content = self.raw.read() or self.raw.data

        # Decode GZip'd content.
        if 'gzip' in self.headers.get('content-encoding', ''):
            try:
                self._content = decode_gzip(self._content)
            except zlib.error:
                pass

        # Decode unicode content.
        if settings.decode_unicode:
            self._content = get_unicode_from_response(self)

        self._content_consumed = True
        return self._content


    def raise_for_status(self):
        """Raises stored :class:`HTTPError` or :class:`URLError`,
        if one occured.
        """

        if self.error:
            raise self.error

        if (self.status_code >= 300) and (self.status_code < 400):
            raise Exception('300 yo')


        elif (self.status_code >= 400) and (self.status_code < 500):
            raise Exception('400 yo')

        elif (self.status_code >= 500) and (self.status_code < 600):
            raise Exception('500 yo')
