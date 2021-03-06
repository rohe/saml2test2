import sys
import inspect
import logging

from aatest.events import EV_HTML_SRC
from aatest.events import EV_HTTP_RESPONSE
from aatest.events import EV_PROTOCOL_REQUEST
from aatest.events import EV_REDIRECT_URL
from aatest.events import EV_REQUEST
from aatest.events import EV_RESPONSE_ARGS
from aatest.operation import Operation

from urllib.parse import urlparse
from urllib.parse import urlunparse

from saml2 import BINDING_HTTP_POST
from saml2.profile import ecp
from saml2.request import AuthnRequest
from saml2.saml import NameID, NAMEID_FORMAT_TRANSIENT, \
    NAMEID_FORMAT_EMAILADDRESS, NAMEID_FORMAT_PERSISTENT

from saml2test.message import ProtocolMessage
from saml2test.sp_test.response import RedirectResponse
import six

__author__ = 'roland'

logger = logging.getLogger(__name__)


class Login(Operation):
    start_page = ''

    def run(self, **kwargs):
        self.conv.events.store('start_page', self.start_page)
        self.conv.trace.info("Doing GET on {}".format(self.start_page))
        res = self.conv.entity.send(self.start_page)
        self.conv.events.store(EV_HTTP_RESPONSE, res)
        self.conv.trace.info("Got a {} response".format(res.status_code))
        if res.status_code in [302, 303]:
            loc = res.headers['location']
            self.conv.events.store(EV_REDIRECT_URL, loc, sub='login')
            self.conv.trace.info("Received HTML: {}".format(res.text))
        return res

    def handle_response(self, saml_req, response_args=None, *args):
        if response_args is not None:
            logger.debug("response_args: {}".format(response_args))

        _srv = self.conv.entity
        _req = _srv.parse_authn_request(saml_req)
        self.conv.trace.reply(_req.xmlstr)
        _msg = _req.message
        self.conv.trace.info("{}: {}".format(_msg.__class__.__name__, _msg))
        self.conv.trace.info('issuer: {}'.format(_msg.issuer.text))
        self.conv.events.store(EV_REQUEST, _req.xmlstr, sub='xml')
        self.conv.events.store(EV_PROTOCOL_REQUEST, _req)
        self.conv.events.store('issuer', _msg.issuer.text)


class AuthenticationResponse(ProtocolMessage):
    def __init__(self, conv, req_args, binding, identity, **kwargs):
        ProtocolMessage.__init__(self, conv, req_args, binding)
        try:
            self.op_type = kwargs['op_type']
        except KeyError:
            self.op_type = ''
        else:
            del kwargs['op_type']
        self.identity = identity
        self.msg_args = kwargs

    def construct_message(self, resp_args):
        _kwargs = resp_args.copy()
        _kwargs.update(self.msg_args)
        _kwargs.update(self.op_args)
        if 'status' in self.op_args:  # supposed to be a failure
            try:
                _kwargs['sign'] = self.op_args['sign_response']
            except KeyError:
                pass
            else:
                del _kwargs['sign_response']

            _args = [_kwargs['in_response_to'], _kwargs['destination'],
                     _kwargs['status']]

            for param in ['status', 'destination', 'in_response_to']:
                del _kwargs[param]

            _resp = self.conv.entity.create_error_response(*_args, **_kwargs)
        else:
            if 'name_id_format' in self.op_args:
                if self.op_args['name_id_format'] == NAMEID_FORMAT_TRANSIENT:
                    text = 'transient'
                elif self.op_args['name_id_format'] == NAMEID_FORMAT_EMAILADDRESS:
                    text='foo@domain.org'
                elif self.op_args['name_id_format'] == NAMEID_FORMAT_PERSISTENT:
                    text='foo@domain.org'
                else:
                    text='whatever'

                _kwargs['name_id'] = NameID(
                    name_qualifier=self.conv.entity_id,
                    format=self.op_args['name_id_format'],
                    text=text)
                del _kwargs['name_id_format']

            _kwargs.update(self.op_args)
            _resp = self.conv.entity.create_authn_response(self.identity,
                                                           **_kwargs)

        self.conv.trace.info('Constructed response message: {}'.format(_resp))

        if self.op_type == "ecp":
            kwargs = {"soap_headers": [
                ecp.Response(
                    assertion_consumer_service_url=resp_args['destination'])]}
        else:
            kwargs = {}

        self.conv.trace.info(
            "Response binding used: {}".format(resp_args['binding']))
        self.conv.trace.info(
            "Destination for response: {}".format(resp_args['destination']))

        # because I don't plan to involve a web browser
        if resp_args['binding'] == BINDING_HTTP_POST:
            args = {
                'relay_state': self.conv.events.last_item('RelayState'),
                'typ': 'SAMLRequest',
                'destination': resp_args['destination']}
            http_args = self.entity.use_http_post(
                "%s" % _resp, **args)
            http_args["url"] = resp_args['destination']
            http_args["method"] = "POST"
        else:
            http_args = self.conv.entity.apply_binding(
                resp_args['binding'], "%s" % _resp,
                destination=resp_args['destination'],
                relay_state=self.conv.events.last_item('RelayState'),
                response=True, **kwargs)

        return http_args

    def handle_response(self, result, *args):
        if isinstance(result, six.string_types):
            self.conv.events.store(EV_REDIRECT_URL, result)
        else:
            self.conv.events.store(EV_HTTP_RESPONSE, result)


class AuthenticationResponseRedirect(RedirectResponse):
    request = "authn_request"
    msg_cls = AuthenticationResponse
    tests = {}

    def __init__(self, conv, webio, sh, **kwargs):
        RedirectResponse.__init__(self, conv, webio, sh, **kwargs)
        self.msg_args = {}
        self.signing_key = None

    def _make_response(self):
        self.msg = self.msg_cls(self.conv, self.req_args, binding=self._binding,
                                **self.msg_args)

        self.msg.op_args = self.op_args

        if self.signing_key:
            self.conv.entity.sec.key_file = self.signing_key

        _authn_req = self.conv.events.get_message(EV_PROTOCOL_REQUEST,
                                                  AuthnRequest)
        resp_args = self.conv.entity.response_args(_authn_req.message)
        resp_args.update(self.response_args)
        self.conv.events.store(EV_RESPONSE_ARGS, resp_args)

        http_info = self.msg.construct_message(resp_args)

        return http_info

    def handle_response(self, result, *args):
        self.msg.handle_response(result, self.response_args)


class FollowRedirect(Operation):
    def __init__(self, conv, webio, sh, **kwargs):
        Operation.__init__(self, conv, webio, sh, **kwargs)
        self.send_args = kwargs

    def run(self):
        base_url = self.conv.events.last_item('start_page')
        loc = self.conv.events.last_item(EV_REDIRECT_URL)
        #loc = _redirect.headers['location']
        if loc.startswith('/'):
            p = list(urlparse(base_url))
            p[2] = loc
            url = urlunparse(p)
        else:
            url = base_url + loc
        res = self.conv.entity.send(url)
        self.conv.events.store(EV_HTTP_RESPONSE, res)
        self.conv.trace.info("Got a {} response".format(res.status_code))
        self.conv.trace.info("Received HTML: {}".format(res.text))
        return res

    def handle_response(self, response, *args):
        self.conv.events.store(EV_HTML_SRC, response)


def factory(name):
    for fname, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj):
            if name == fname:
                return obj
