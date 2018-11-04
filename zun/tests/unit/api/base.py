#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# NOTE: Ported from ceilometer/tests/api.py (subsequently moved to
# ceilometer/tests/api/__init__.py). This should be oslo'ified:
# https://bugs.launchpad.net/ironic/+bug/1255115.

# NOTE(deva): import auth_token so we can override a config option
from keystonemiddleware import auth_token  # noqa
import pecan
import pecan.testing
from six.moves.urllib import parse as urlparse

from zun.api import hooks
import zun.conf
from zun.tests.unit.db import base


PATH_PREFIX = '/v1'
CURRENT_VERSION = "container 1.27"


class FunctionalTest(base.DbTestCase):
    """Base class for API tests.

    Pecan controller test. Used for functional tests of Pecan controllers where
    you need to test your literal application and its integration with the
    framework.
    """

    def setUp(self):
        super(FunctionalTest, self).setUp()
        zun.conf.CONF.set_override("auth_version", "v2.0",
                                   group='keystone_authtoken')
        zun.conf.CONF.set_override("admin_user", "admin",
                                   group='keystone_authtoken')

        # Determine where we are so we can set up paths in the config
        root_dir = self.get_path()
        self.config = {
            'app': {
                'root': 'zun.api.controllers.root.RootController',
                'modules': ['zun.api'],
                'static_root': '%s/public' % root_dir,
                'template_path': '%s/api/templates' % root_dir,
                'hooks': [
                    hooks.ContextHook(),
                    hooks.RPCHook(),
                    hooks.NoExceptionTracebackHook(),
                ],
            },
        }

        self.app = self._make_app()

        def reset_pecan():
            pecan.set_config({}, overwrite=True)

        self.addCleanup(reset_pecan)

    def _verify_attrs(self, attrs, response, positive=True):
        if positive is True:
            verify_method = self.assertIn
        else:
            verify_method = self.assertNotIn
        for attr in attrs:
            verify_method(attr, response)

    def _make_app(self, config=None):
        if not config:
            config = self.config

        return pecan.testing.load_test_app(config)

    def _request_json(self, path, params, expect_errors=False, headers=None,
                      method="post", extra_environ=None, status=None,
                      path_prefix=PATH_PREFIX):
        """Sends simulated HTTP request to Pecan test app.

        :param path: url path of target service
        :param params: content for wsgi.input of request
        :param expect_errors: Boolean value; whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param method: Request method type. Appropriate method function call
                       should be used rather than passing attribute in.
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param status: expected status code of response
        :param path_prefix: prefix of the url path
        """
        if headers is None:
            headers = {}
        headers.setdefault('Accept', 'application/json')
        headers.setdefault('OpenStack-API-Version', CURRENT_VERSION)
        full_path = path_prefix + path
        print('%s: %s %s' % (method.upper(), full_path, params))
        response = getattr(self.app, "%s_json" % method)(
            str(full_path),
            params=params,
            headers=headers,
            status=status,
            extra_environ=extra_environ,
            expect_errors=expect_errors
        )
        print('GOT:%s' % response)
        return response

    def put_json(self, path, params, expect_errors=False, headers=None,
                 extra_environ=None, status=None):
        """Sends simulated HTTP PUT request to Pecan test app.

        :param path: url path of target service
        :param params: content for wsgi.input of request
        :param expect_errors: Boolean value; whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param status: expected status code of response
        """
        return self._request_json(path=path, params=params,
                                  expect_errors=expect_errors,
                                  headers=headers, extra_environ=extra_environ,
                                  status=status, method="put")

    def post_json(self, path, params, expect_errors=False, headers=None,
                  extra_environ=None, status=None):
        """Sends simulated HTTP POST request to Pecan test app.

        :param path: url path of target service
        :param params: content for wsgi.input of request
        :param expect_errors: Boolean value; whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param status: expected status code of response
        """
        return self._request_json(path=path, params=params,
                                  expect_errors=expect_errors,
                                  headers=headers, extra_environ=extra_environ,
                                  status=status, method="post")

    def patch_json(self, path, params, expect_errors=False, headers=None,
                   extra_environ=None, status=None):
        """Sends simulated HTTP PATCH request to Pecan test app.

        :param path: url path of target service
        :param params: content for wsgi.input of request
        :param expect_errors: Boolean value; whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param status: expected status code of response
        """
        return self._request_json(path=path, params=params,
                                  expect_errors=expect_errors,
                                  headers=headers, extra_environ=extra_environ,
                                  status=status, method="patch")

    def get(self, *args, **kwargs):
        headers = kwargs.pop('headers', {})
        headers.setdefault('Accept', 'application/json')
        headers.setdefault('OpenStack-API-Version', CURRENT_VERSION)
        kwargs['headers'] = headers
        return self.app.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        headers = kwargs.pop('headers', {})
        headers.setdefault('Accept', 'application/json')
        headers.setdefault('OpenStack-API-Version', CURRENT_VERSION)
        kwargs['headers'] = headers
        return self.app.post(*args, **kwargs)

    def delete(self, *args, **kwargs):
        headers = kwargs.pop('headers', {})
        headers.setdefault('Accept', 'application/json')
        headers.setdefault('OpenStack-API-Version', CURRENT_VERSION)
        kwargs['headers'] = headers
        return self.app.delete(*args, **kwargs)

    def get_json(self, path, expect_errors=False, headers=None,
                 extra_environ=None, q=None, path_prefix=PATH_PREFIX,
                 **params):
        """Sends simulated HTTP GET request to Pecan test app.

        :param path: url path of target service
        :param expect_errors: Boolean value;whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param q: list of queries consisting of: field, value, op, and type
                  keys
        :param path_prefix: prefix of the url path
        :param params: content for wsgi.input of request
        """
        if headers is None:
            headers = {}
        headers.setdefault('Accept', 'application/json')
        headers.setdefault('OpenStack-API-Version', CURRENT_VERSION)
        if q is None:
            q = []
        full_path = path_prefix + path
        query_params = {'q.field': [],
                        'q.value': [],
                        'q.op': [],
                        }
        for query in q:
            for name in ['field', 'op', 'value']:
                query_params['q.%s' % name].append(query.get(name, ''))
        all_params = {}
        all_params.update(params)
        if q:
            all_params.update(query_params)
        print('GET: %s %r' % (full_path, all_params))
        response = self.app.get(full_path,
                                params=all_params,
                                headers=headers,
                                extra_environ=extra_environ,
                                expect_errors=expect_errors)
        if not expect_errors:
            response = response.json
        print('GOT:%s' % response)
        return response

    def validate_link(self, link, bookmark=False):
        """Checks if the given link can get correct data."""
        # removes the scheme and net location parts of the link
        url_parts = list(urlparse.urlparse(link))
        url_parts[0] = url_parts[1] = ''

        # bookmark link should not have the version in the URL
        if bookmark and url_parts[2].startswith(PATH_PREFIX):
            return False

        full_path = urlparse.urlunparse(url_parts)
        try:
            self.get_json(full_path, path_prefix='')
            return True
        except Exception:
            return False
