import logging
from aatest import Break
from aatest.operation import Operation

# from saml2 import samlp
from saml2 import SAMLError
from saml2 import BINDING_HTTP_POST
from saml2 import BINDING_HTTP_REDIRECT

# from saml2.mdstore import REQ2SRV
from saml2.saml import NAMEID_FORMAT_TRANSIENT
from saml2.saml import NAMEID_FORMAT_PERSISTENT
from saml2.time_util import utc_time_sans_frac

__author__ = 'roland'

logger = logging.getLogger(__name__)


class MissingMetadata(Exception):
    pass


class UnknownBinding(Exception):
    pass


class Request(Operation):
    name_id_formats = [NAMEID_FORMAT_TRANSIENT, NAMEID_FORMAT_PERSISTENT]
    bindings = [BINDING_HTTP_POST, BINDING_HTTP_REDIRECT]

    def __init__(self, conv, io, sh, **kwargs):
        Operation.__init__(self, conv, io, sh, **kwargs)
        self.expect_error = {}
        self.req_args = {}
        self.op_args = {}
        self.csi = None
        self.client = self.conv.client
        self.trace = self.conv.trace
        self.relay_state = ''
        self.request_id = ''
        self.response_args = {}

    def expected_error_response(self, response):
        if isinstance(response, SAMLError):
            if self.expect_error["stop"]:
                raise Break("Stop requested after received expected error")
        else:
            self.conv.trace.error("Expected error, didn't get it")
            raise Break("Did not receive expected error")

    def _make_request(self):
        raise NotImplemented


class HttpRedirectRequest(Request):
    _class = None
    _args = {}
    _method = 'GET'

    def run(self):
        info = self._make_request()
        _method = info['method']
        _loc = ''
        for header, value in info['headers']:
            if header == 'Location':
                _loc = value
                break

        self.response_args["outstanding"] = {self.request_id: "/"}
        self.trace.info("redirect.url: {}".format(_loc))
        self.conv.timestamp.append((_loc, utc_time_sans_frac()))
        res = self.client.send(_loc, _method)
        self.trace.info("redirect response: {}".format(res.text))
        return res


class HttpRedirectAuthnRequest(HttpRedirectRequest):
    request = "authn_request"
    tests = {}

    def _make_request(self):
        """
        A slightly modified version of the
        prepare_for_negotiated_authenticate() method of saml2.client.Saml2Client
        :return: Information necessary to do a requests.request operation
        """
        _cli = self.client

        _binding = BINDING_HTTP_REDIRECT
        args = {'binding': _binding}
        try:
            args['entityid'] = self.req_args['entityid']
        except KeyError:
            pass

        destination = _cli._sso_location(**args)

        logger.info("destination to provider: %s", destination)

        self.request_id, request = _cli.create_authn_request(
            destination=destination, **self.req_args)

        self.conv.protocol_request.append(request)

        _req_str = str(request)

        logger.info("AuthNReq: %s", _req_str)

        args = {}
        for param in ['sigalg', 'relay_state']:
            try:
                args[param] = self.req_args[param]
            except KeyError:
                pass

        http_info = _cli.apply_binding(_binding, _req_str, destination, **args)
        return http_info

    def op_setup(self):
        metadata = self.conv.client.metadata
        try:
            entity = metadata[self.conv.entity_id]
        except KeyError:
            raise MissingMetadata("No metadata available for {}".format(
                self.conv.entity_id))

        for arg in ['nameid_format', 'response_binding']:
            if not arg in self.req_args:
                self.req_args[arg] = ''

        for idp in entity["idpsso_descriptor"]:
            for nformat in self.name_id_formats:
                if self.req_args["nameid_format"]:
                    break
                for nif in idp["name_id_format"]:
                    if nif["text"] == nformat:
                        self.req_args["nameid_format"] = nformat
                        break
            for bind in self.bindings:
                if self.req_args["response_binding"]:
                    break
                for sso in idp["single_sign_on_service"]:
                    if sso["binding"] == bind:
                        self.req_args["response_binding"] = bind
                        break

    def handle_response(self, result):
        _cli = self.conv.client
        resp = _cli.parse_authn_request_response(
            result['SAMLResponse'], self.req_args['response_binding'],
            self.response_args["outstanding"])
        self.conv.protocol_response.append(resp)
